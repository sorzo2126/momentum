"""Bounded, retrospective S0 component audit. Writes only beside this file."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, time
import numpy as np
import pandas as pd
from scipy.optimize import minimize

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]
sys.path.insert(0, str(STUDY / 'model_snapshot'))
from momentum.features import prepare_panel, FEATURE_MODULES
from momentum.states import model_measurements
from momentum.model import make_targets, split_sessions, _session_weights
from momentum.scenarios import predict_head, fit_head, path_experts, redistribute
from momentum.deployment import load_deployment

SEEDS = (1729, 2718, 3141)
EXPERTS = ('local', 'structural', 'supervised_local', 'supervised_uniform')
SCORES = ('log_loss','brier','endpoint_crps_ticks','long_mae_crps_ticks',
          'short_mae_crps_ticks','marginal_crps_ticks','long_pinball80_ticks',
          'short_pinball80_ticks','interval80_score_ticks')
CONSUMED = {}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def consume(p): CONSUMED[str(p.relative_to(STUDY))] = sha(p); return p
def csv(p, indexed=False):
    d = pd.read_csv(consume(p))
    for column in ('event_time','available_at','open_time','close_time','target_end'):
        if column in d: d[column]=pd.to_datetime(d[column],utc=True,format='mixed')
    if indexed:
        d['decision_time'] = pd.to_datetime(d.decision_time, utc=True)
        d = d.set_index('decision_time')
    return d
def dump(name, value):
    (HERE/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def crps_terms(v, probabilities, truth):
    """A_k=E_k|X-y|; B_kl=E_kl|X-X'|, exact O(K^2 n log n)."""
    order=np.argsort(v,kind='stable'); v=np.asarray(v)[order]
    p=np.asarray(probabilities)[:,order]
    cq=np.cumsum(p,axis=1); cqx=np.cumsum(p*v,axis=1)
    distance=v*cq-cqx+(p*v).sum(axis=1)[:,None]-cqx-v*(p.sum(axis=1)[:,None]-cq)
    return p@np.abs(v-truth), p@distance.T

def qtile(v,p,level):
    order=np.argsort(v,kind='stable'); accum=np.cumsum(p[order])
    return float(v[order[min(np.searchsorted(accum,level,side='left'),len(order)-1)]])

def score_paths(bank, weights, truth, sigma):
    masses=np.bincount(bank['classes'],weights=weights,minlength=3)
    y=int(truth.class_id); one=np.eye(3)[y]
    values=[bank['endpoint'],bank['mae_long'],bank['mae_short']]
    actual=[truth.return_ticks,truth.mae_long_ticks,truth.mae_short_ticks]
    crps=[]
    for v,t in zip(values,actual):
        a,b=crps_terms(v,weights[None,:],t/sigma)
        crps.append(float((a[0]-.5*b[0,0])*sigma))
    ql=qtile(values[1]*sigma,weights,.8); qs=qtile(values[2]*sigma,weights,.8)
    lo=qtile(values[0]*sigma,weights,.1); hi=qtile(values[0]*sigma,weights,.9)
    el=truth.mae_long_ticks-ql; es=truth.mae_short_ticks-qs
    return dict(log_loss=float(-np.log(max(masses[y],1e-12))),
        brier=float(np.sum((masses-one)**2)), endpoint_crps_ticks=crps[0],
        long_mae_crps_ticks=crps[1],short_mae_crps_ticks=crps[2],
        marginal_crps_ticks=float(np.mean(crps)),
        long_pinball80_ticks=float(max(.8*el,-.2*el)),
        short_pinball80_ticks=float(max(.8*es,-.2*es)),
        interval80_score_ticks=float(hi-lo+10*max(lo-truth.return_ticks,0)+10*max(truth.return_ticks-hi,0)))

def paired(frame, candidates, reference, fields, keys=('seed','horizon_minutes')):
    result=[]
    for key,group in frame.groupby(list(keys)):
        ref=group[group.model==reference].set_index('session_id')
        for candidate in candidates:
            alt=group[group.model==candidate].set_index('session_id')
            ids=ref.index.intersection(alt.index)
            for field in fields:
                diff=(alt.loc[ids,field]-ref.loc[ids,field]).to_numpy()
                rng=np.random.default_rng(9041)
                boots=rng.choice(diff,size=(4000,len(diff)),replace=True).mean(1)
                result.append(dict(zip(keys,key if isinstance(key,tuple) else (key,)))|
                    dict(candidate=candidate,reference=reference,metric=field,sessions=len(diff),
                         difference=float(diff.mean()),ci_low=float(np.quantile(boots,.025)),ci_high=float(np.quantile(boots,.975))))
    return result

def main():
    start=time.time(); (HERE/'fitted-baselines').mkdir(exist_ok=True)
    consume(HERE/'protocol.md')
    # Verification of the exact CRPS formula against a direct finite sum.
    v=np.array([-2.,.5,3.]); p=np.array([[.2,.3,.5],[.5,.2,.3]])
    aa,bb=crps_terms(v,p,.7)
    assert np.allclose(bb,p@np.abs(v[:,None]-v[None,:])@p.T)
    assert np.allclose(aa,p@np.abs(v-.7))
    path_rows=[]; clock_rows=[]; fitted=[]; checks=[]; colspec={}
    for seed in SEEDS:
        folder=STUDY/'results'/f'base-{seed}'
        for item in sorted((folder/'frozen-model').glob('*')):
            if item.is_file(): consume(item)
        research=load_deployment(folder/'frozen-model'); cfg=research['config']; scfg=research['scenario_config']
        data={name:csv(folder/'inputs'/f'{name}.csv.gz') for name in ('quotes','rates','sessions','trades','context')}
        panel=prepare_panel(data['quotes'],data['rates'],data['sessions'],cfg,
            trades=data['trades'],context=data['context'],as_of=data['sessions'].close_time.iloc[-1])
        features=csv(folder/'features.csv.gz',True); obs=csv(folder/'observations.csv.gz',True)
        x,groups=model_measurements(features,obs,cfg,research['use_flow'],research['use_vwap'])
        targets=make_targets(panel,features,cfg); splits=split_sessions(panel,cfg)
        saved=csv(folder/'predictions-and-outcomes.csv.gz',True)
        pricecols=[c for c in FEATURE_MODULES['cgb'] if c in x and c!='spread_ticks' and not c.startswith('phase_')]
        pricecols+=['state_age_minutes','response_z5']+[f'state_{j}' for j in range(5)]
        clockcols=['minutes_remaining','minutes_from_segment_open']
        colspec[str(seed)]={'clock_only':clockcols,'price_only':pricecols,'full':list(x)}
        for h,entry in research['horizons'].items():
            bank=entry['bank']; train=pd.DatetimeIndex(pd.to_datetime(bank['train_times'],utc=True))
            pred=saved[saved.horizon_minutes==h].copy(); test=pred.index
            assert pred.outcome_available.all()
            wt=bank['session_weights']; prior=np.bincount(bank['classes'],weights=wt,minlength=3);prior/=prior.sum()
            probs={'frozen_full':pred[['p_down','p_neutral','p_up']].to_numpy(),
                   'train_frequency':np.tile(prior,(len(test),1))}
            for name,cols in [('clock_only',clockcols),('price_only',pricecols)]:
                head=fit_head(x.loc[train,cols],bank['classes'],wt,scfg,cfg)
                probs[name]=predict_head(head,x.loc[test,cols],3)
                if head['model'] is not None:head['model'].save_model(HERE/'fitted-baselines'/f'{seed}-{h}-{name}.json')
            yy=pred.class_id.to_numpy(int)
            for model,predicted in probs.items():
                assert np.isfinite(predicted).all() and np.allclose(predicted.sum(1),1.)
                for j,t in enumerate(test):
                    clock_rows.append(dict(seed=seed,horizon_minutes=h,decision_time=t,session_id=obs.loc[t,'session_id'],
                        model=model,log_loss=float(-np.log(max(predicted[j,yy[j]],1e-12))),
                        brier=float(np.sum((predicted[j]-np.eye(3)[yy[j]])**2)),
                        p_down=predicted[j,0],p_neutral=predicted[j,1],p_up=predicted[j,2]))
            if h!=60: continue
            candidate=obs.index.intersection(splits['cal']); target=targets[h]
            end=target.loc[candidate,'target_end']; future=obs.state_id.reindex(pd.DatetimeIndex(end)).to_numpy()
            good=obs.loc[candidate,'valid'].to_numpy()&target.loc[candidate,'class_id'].notna().to_numpy()
            good &= end.isin(splits['cal']).to_numpy()&np.isfinite(future)&(future>=0)
            cal=candidate[good]; both=cal.append(test)
            pstate=entry['state_ml_weight']*predict_head(entry['state_head'],x.loc[both],5)+(1-entry['state_ml_weight'])*entry['transition'][obs.loc[both,'state_id'].to_numpy(int)]
            pprice=predict_head(entry['price_head'],x.loc[both],3)
            cache=[]; cal_a=[]; cal_b=[]; maximum_error=0.; class_error=0.
            for j,t in enumerate(both):
                expert,_,_=path_experts(bank,x.loc[t],pstate[j],pprice[j])
                uniform,_=redistribute(np.ones(len(bank['classes'])),bank['classes'],pprice[j])
                expert=np.vstack([expert,uniform]); cache.append(expert)
                for vector in expert:
                    assert np.isfinite(vector).all() and np.isclose(vector.sum(),1.) and np.min(vector)>=0
                sigma=float(features.loc[t,'sigma_ticks']); actual=target.loc[t]
                if j<len(cal):
                    terms=[crps_terms(bank[key],expert,float(actual[truth])/sigma) for key,truth in
                        [('endpoint','return_ticks'),('mae_long','mae_long_ticks'),('mae_short','mae_short_ticks')]]
                    cal_a.append(np.mean([ab[0] for ab in terms],axis=0));cal_b.append(np.mean([ab[1] for ab in terms],axis=0))
                else:
                    mix=entry['mixture_weights']@expert[:3]
                    masses=np.bincount(bank['classes'],weights=mix,minlength=3)
                    maximum_error=max(maximum_error,float(np.max(np.abs(masses-pred.loc[t,['p_down','p_neutral','p_up']].to_numpy(float)))))
                    supervised=np.bincount(bank['classes'],weights=expert[2],minlength=3)
                    class_error=max(class_error,float(np.max(np.abs(supervised-pprice[j]))))
            assert maximum_error<1e-6, maximum_error
            cw=_session_weights(obs.loc[cal,'session_id']); a=np.average(cal_a,axis=0,weights=cw); b=np.average(cal_b,axis=0,weights=cw)
            objective=lambda w: float(a@w-.5*w@b@w)
            opt=minimize(objective,np.ones(4)/4,method='SLSQP',bounds=[(0.,1.)]*4,
                constraints={'type':'eq','fun':lambda w:w.sum()-1},options={'ftol':1e-10,'maxiter':200})
            assert opt.success,opt.message
            weights=np.clip(opt.x,0,1);weights/=weights.sum()
            fitted.append(dict(seed=seed,horizon_minutes=h,cal_origins=len(cal),test_origins=len(test),
                objective='mean volatility-normalized marginal CRPS',cal_objective=objective(weights),
                **{name:float(w) for name,w in zip(EXPERTS,weights)}))
            checks.append(dict(seed=seed,maximum_saved_probability_error=maximum_error,
                maximum_supervised_class_probability_error=class_error,
                original_mixture_weights=entry['mixture_weights'].tolist()))
            for j,t in enumerate(test,start=len(cal)):
                expert=cache[j]; sigma=float(features.loc[t,'sigma_ticks']); truth=target.loc[t]
                candidates={**dict(zip(EXPERTS,expert)), 'frozen_mixture':entry['mixture_weights']@expert[:3],
                    'cal_path_mixture':weights@expert}
                for model,distribution in candidates.items():
                    path_rows.append(dict(seed=seed,horizon_minutes=h,decision_time=t,session_id=obs.loc[t,'session_id'],
                        model=model,**score_paths(bank,distribution,truth,sigma)))
        print(f'completed seed {seed}: {time.time()-start:.1f}s',flush=True)
    paths=pd.DataFrame(path_rows); clocks=pd.DataFrame(clock_rows)
    paths.to_csv(HERE/'path-scores-per-origin.csv.gz',index=False)
    clocks.to_csv(HERE/'baseline-scores-per-origin.csv.gz',index=False)
    bypaths=paths.groupby(['seed','horizon_minutes','model','session_id'])[list(SCORES)].mean().reset_index()
    bypaths.to_csv(HERE/'path-scores-per-session.csv',index=False)
    bypaths.groupby(['seed','horizon_minutes','model'])[list(SCORES)].mean().to_csv(HERE/'path-summary.csv')
    comparisons=paired(bypaths,['supervised_local'],'supervised_uniform',SCORES)
    comparisons+=paired(bypaths,['cal_path_mixture','local','structural'],'frozen_mixture',SCORES)
    pd.DataFrame(comparisons).to_csv(HERE/'path-paired-differences.csv',index=False)
    matched=[]
    for seed,group in clocks.groupby('seed'):
        origins=[set(g.decision_time) for _,g in group.groupby('horizon_minutes')]
        common=set.intersection(*origins)
        matched.append(group[group.decision_time.isin(common)].assign(sample='matched_horizons'))
    clocks=pd.concat([clocks.assign(sample='all_eligible'),*matched],ignore_index=True)
    byclock=clocks.groupby(['seed','horizon_minutes','sample','model','session_id'])[['log_loss','brier']].mean().reset_index()
    byclock.to_csv(HERE/'baseline-scores-per-session.csv',index=False)
    byclock.groupby(['seed','horizon_minutes','sample','model'])[['log_loss','brier']].mean().to_csv(HERE/'baseline-summary.csv')
    baselinepairs=paired(byclock,['clock_only','price_only','frozen_full'],'train_frequency',['log_loss','brier'],keys=('seed','horizon_minutes','sample'))
    baselinepairs+=paired(byclock,['frozen_full'],'price_only',['log_loss','brier'],keys=('seed','horizon_minutes','sample'))
    pd.DataFrame(baselinepairs).to_csv(HERE/'baseline-paired-differences.csv',index=False)
    pd.DataFrame(fitted).to_csv(HERE/'cal-path-mixture-weights.csv',index=False)
    dump('feature-columns.json',colspec)
    unchanged=all(sha(STUDY/name)==digest for name,digest in CONSUMED.items())
    assert unchanged
    dump('verification.json',dict(completed_at=datetime.now(timezone.utc).isoformat(),
        source_files_unchanged=unchanged,crps_direct_sum_check=True,probability_checks=True,
        checks=checks,elapsed_seconds=time.time()-start,source_hashes=CONSUMED,
        script_sha256=sha(Path(__file__)),test_status='Previously consulted S0 TEST; retrospective diagnostic only'))
    make_plots()
    print('COMPLETE',flush=True)

def make_plots():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    d=pd.read_csv(HERE/'path-paired-differences.csv')
    fig,axes=plt.subplots(1,2,figsize=(12,4.3),layout='constrained')
    for ax,candidate,reference,title in [(axes[0],'supervised_local','supervised_uniform','Local path weighting minus uniform within class'),
        (axes[1],'cal_path_mixture','frozen_mixture','CAL path-score mixture minus frozen mixture')]:
        g=d[(d.candidate==candidate)&(d.reference==reference)&(d.metric=='marginal_crps_ticks')]
        y=np.arange(len(g));ax.errorbar(g.difference,y,xerr=np.vstack([g.difference-g.ci_low,g.ci_high-g.difference]),fmt='o',capsize=4)
        ax.axvline(0,color='gray',lw=1);ax.set_yticks(y,[str(s) for s in g.seed]);ax.set_xlabel('Mean marginal CRPS difference (ticks); lower is better')
        ax.set_xlim(-.08,.02)
        if candidate=='cal_path_mixture':ax.text(.04,.95,'Same selected expert; differences below 1e-14 ticks',transform=ax.transAxes,va='top',fontsize=9)
        ax.set_title(title);ax.set_ylabel('Synthetic seed')
    fig.suptitle('One-hour path scores | paired 95% session-bootstrap intervals | 8 sessions per seed',fontsize=12)
    fig.savefig(HERE/'path-attribution.png',dpi=170);plt.close(fig)
    d=pd.read_csv(HERE/'baseline-summary.csv')
    fig,axes=plt.subplots(1,3,figsize=(13,4.3),sharey=True,layout='constrained')
    for ax,seed in zip(axes,SEEDS):
        g=d[(d.seed==seed)&(d['sample']=='all_eligible')]
        for model in ['train_frequency','clock_only','price_only','frozen_full']:
            gg=g[g.model==model];ax.plot(gg.horizon_minutes,gg.log_loss,'o-',label=model.replace('_',' '))
        ax.set_title(f'Seed {seed}');ax.set_xlabel('Horizon (minutes)');ax.set_xticks([60,120,240])
    axes[0].set_ylabel('Session-mean log loss; lower is better');axes[-1].legend(fontsize=8)
    fig.suptitle('Fixed TRAIN-only baselines | already-consulted S0 TEST',fontsize=12)
    fig.savefig(HERE/'baseline-comparison.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
