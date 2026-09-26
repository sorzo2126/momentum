"""Mechanism-based synthetic CGB experiment. No market calibration or orders.

Run from the study folder: python -m simulation.structured_simulation
All protocol choices below are fixed before inspecting the experiment's results.
Hidden simulator variables never enter the model input tables.
"""
from __future__ import annotations
from dataclasses import asdict, replace
from pathlib import Path
import argparse, hashlib, json, math, os, time
import numpy as np
import pandas as pd

from momentum import ResearchConfig, ScenarioConfig, prepare_panel, build_features
from momentum.model import make_targets, _metrics, _session_weights
from momentum.states import build_state_observations, model_measurements, STATE_NAMES
from momentum.scenarios import (fit_scenario_research, predict_head, path_experts,
    _forecast_summary, weighted_quantile)
from momentum.execution import futures_touch_benchmark
from momentum.deployment import save_deployment

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('CGB_SIMULATION_OUTPUT', str(ROOT))).expanduser().resolve()
SEEDS = (1729, 2718, 3141)
PROTOCOL = dict(version='2.0-bond-ecosystem', seeds=SEEDS, sessions=40, train_sessions=24,
    calibration_sessions=8, test_sessions=8, session_minutes=480,
    session_timezone='America/New_York', session_open='08:00', session_close='16:00',
    horizons_minutes=[60,120,240], decision_minutes=5, model_trees=100,
    modules=['cgb','us','curve','book','vwap'],
    stress_worlds=['fast_decay','liquidity_shock','decoupling','feed_gaps'],
    entry_delay_minutes=1, contracts=1, signal_threshold=.2,
    roundtrip_fee_cad=4., base_extra_slippage_ticks=1., stressed_extra_slippage_ticks=4.,
    costs_are_assumptions=True, market_calibrated=False,
    no_threshold_or_parameter_selection_on_test=True)


def dump_json(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=lambda x:
        x.item() if isinstance(x,np.generic) else str(x)), encoding='utf8')


def generate_driver(seed=1729, world='base', days=40):
    """One-minute observable snapshots; independent random streams per session.

    Prices quoted on instrument lattices; futures dollar accounting uses CGB only.
    Each minute's buy/sell tape rows aggregate same-side contracts at the touch.
    They are not individual L2 events. Exact timestamps express receiver ordering.
    """
    sessions=[]; quotes=[]; rates=[]; trades=[]; truth=[]; curve_truth=[]
    mid=120.; us=112.; cgf=116.; cgz=103.; cum_y10=0.; policy=0.
    cgb_origin=mid; basis=0.
    for dayno, day in enumerate(pd.bdate_range('2025-01-06',periods=days)):
        rng=np.random.default_rng(np.random.SeedSequence([seed,dayno]))
        # Pre-draw all noise: stress choices cannot change later random numbers.
        z=rng.normal(size=(481,16)); tail=rng.standard_t(5,size=(481,2))/math.sqrt(5/3)
        uniform=rng.random((481,6)); shock=rng.normal(0,1.7,3)
        start=(pd.Timestamp(day.date()).tz_localize('America/New_York')+pd.Timedelta(hours=8)).tz_convert('UTC')
        idx=pd.date_range(start,periods=481,freq='min')
        sid=str(day.date()); sessions.append(dict(session_id=sid,open_time=idx[0],close_time=idx[-1]))
        stress=dayno>=32 and world not in ('base','null')
        u=c=0.; logvol=0.; logdepth=0.; transient=0.; absorption=0
        # Arbitrary independent overnight repricing; positions never cross it.
        mid+=.12*z[0,12]; us+=.12*z[0,13]
        for k,t in enumerate(idx):
            previous_mid=mid
            phi=.65 if stress and world=='fast_decay' else .985
            u=phi*u+.075*z[k,0]; c=phi*c+.085*z[k,1]
            event=k in (30,150,300)
            if event:
                j=(30,150,300).index(k)
                # US macro, Canadian policy, then common supply/risk-premium shock.
                u+=shock[j]*[1.,.1,.7][j]
                c+=shock[j]*[.3,1.2,.4][j]+.45*z[k,2]
            if uniform[k,0]<(.035 if absorption else .018): absorption=1-absorption
            logvol=.975*logvol+.085*z[k,3]+(.35 if event else 0.)
            logdepth=.96*logdepth+.10*z[k,4]-(.35 if event else 0.)
            vol=float(np.clip(np.exp(logvol),.45,3.))
            depth=float(np.clip(np.exp(logdepth),.25,3.))
            shock_window=stress and world=='liquidity_shock' and 130<=k<=250
            if shock_window: vol*=2.5; depth*=.25
            q=float(np.tanh(.75*c+.55*u+.4*z[k,5]))
            if world=='null': q=float(np.tanh(.4*z[k,5]))
            us_r=.22*u+.9*vol*tail[k,0]
            rho=.8 if stress and world=='fast_decay' else .975
            impact=.35*q*(1-.85*absorption)/math.sqrt(depth)
            next_transient=rho*transient+impact
            beta=-.35 if stress and world=='decoupling' else .65
            local_coefficient=.4 if stress and world=='decoupling' else .2
            drift=beta*.22*u+local_coefficient*c+next_transient-transient
            cad_r=beta*us_r+local_coefficient*c+next_transient-transient+.75*vol*tail[k,1]
            if world=='null':
                us_r=.9*vol*tail[k,0]
                cad_r=.65*us_r+.75*vol*tail[k,1]
                drift=0.; next_transient=0.
            if shock_window and k==150: cad_r+=15*np.sign(shock[1])
            transient=next_transient
            if k: mid+=.01*cad_r; us+=(1/64)*us_r
            policy=.975*policy+.02*z[k,6]+(shock[(30,150,300).index(k)]*[.03,.30,.05][(30,150,300).index(k)] if event else 0.)
            basis=.97*basis+.015*z[k,7]
            # Stylized fixed sensitivities, not an actual CTD/convexity model.
            y10=330-(mid-cgb_origin)/.085+basis
            y5=320+.9*(y10-330)+policy
            y2=310+.65*(y10-330)+2.0*policy
            cgf=116-.05*(y5-320); cgz=103-.02*(y2-310)
            spread=int(np.clip(1+int(vol>1.5)+int(depth<.6)+(3 if shock_window else 0),1,10))
            bid=math.floor((mid-.005*spread)/.01+1e-9)*.01; ask=bid+spread*.01
            visible_mid=(bid+ask)/2
            imb=float(np.tanh(.65*q+.35*z[k,8]))
            total_depth=max(4,int(120*depth/(1+.2*vol)))
            bid_n=max(1,int(total_depth*(1+imb)/2)); ask_n=max(1,total_depth-bid_n)
            event_time=t if k==0 else t-pd.Timedelta(seconds=1)
            arrival=t if k==0 else t-pd.Timedelta(milliseconds=650)
            gap=stress and world=='feed_gaps' and 190<=k<=199
            for name,price,tick,st in [('CGB',visible_mid,.01,spread),('US10',us,1/64,1),('CGF',cgf,.01,1),('CGZ',cgz,.005,1)]:
                if name=='CGB': qb,qa=bid,ask
                else:
                    qb=math.floor((price-st*tick/2)/tick)*tick; qa=qb+st*tick
                recv=arrival
                if stress and world=='feed_gaps' and name=='US10' and 170<=k<=230: recv+=pd.Timedelta(seconds=90)
                if name=='CGB' and gap: continue
                quotes.append(dict(instrument=name,contract='SIM_'+name,event_time=event_time,
                    available_at=recv,bid=qb,ask=qa,bid_size=bid_n,ask_size=ask_n))
            if k%2==0:
                for name,value in [('CAD2Y',y2),('CAD5Y',y5),('CAD10Y',y10)]:
                    rates.append(dict(instrument=name,event_time=event_time,available_at=arrival,rate_bp=value))
                # Only four late sessions: deliberately cannot train swap/OIS modules.
                if dayno>=days-4:
                    tenors=np.arange(1,6); zeros=y2+np.array([-8,-2,2,5,8])+policy*np.array([.4,.2,.1,0,-.1])
                    discounts=np.exp(-zeros*1e-4*tenors)
                    par=(1-discounts)/np.cumsum(discounts)*1e4
                    for j in range(5):
                        for prefix,value in [('OIS',par[j]),('SWAP',par[j]+8+.4*basis)]:
                            rates.append(dict(instrument=f'{prefix}{j+1}Y',event_time=event_time,available_at=arrival,rate_bp=value))
                    for name,value in [('FWD1Y1Y',2*zeros[1]-zeros[0]),('FWD2Y1Y',3*zeros[2]-2*zeros[1])]:
                        rates.append(dict(instrument=name,event_time=event_time,available_at=arrival,rate_bp=value))
                    curve_truth.append(dict(time=t,zero1_bp=zeros[0],zero2_bp=zeros[1],zero3_bp=zeros[2],
                        fwd1y1y_bp=2*zeros[1]-zeros[0],fwd2y1y_bp=3*zeros[2]-2*zeros[1]))
            count=max(2,int(55*np.exp(.2*z[k,9])*(1+.5*abs(q))*(2 if event else 1)))
            buys=int(np.clip(round(count*(1+q)/2),1,count-1))
            for side,size,price in [(1,buys,ask),(-1,count-buys,bid)]:
                recv=arrival
                if stress and world=='feed_gaps' and 170<=k<=230: recv+=pd.Timedelta(seconds=60)
                trades.append(dict(trade_id=f'{seed}-{dayno}-{k}-{side}',instrument='CGB',contract='SIM_CGB',
                    event_time=event_time,available_at=recv,price=price,size=size,aggressor=side))
            truth.append(dict(decision_time=t,session_id=sid,day_number=dayno,minute=k,
                world=world,latent_mid=mid,latent_us=us,policy_factor=policy,equity_noise=z[k,14],
                macro_theme='growth' if dayno%2 else 'inflation',cgb_mid=visible_mid,cgb_bid=bid,cgb_ask=ask,
                pressure_us=u,pressure_cad=c,signed_pressure=q,absorption_switch=absorption,
                instantaneous_drift_ticks=drift,vol_multiplier=vol,depth_multiplier=depth,
                transient_ticks=transient,beta=beta,spread_ticks=spread,
                scheduled_event=event,shock_window=shock_window,cgb_quote_missing=gap,
                bid_size=bid_n,ask_size=ask_n))
    return dict(sessions=pd.DataFrame(sessions),quotes=pd.DataFrame(quotes),rates=pd.DataFrame(rates),
                trades=pd.DataFrame(trades),truth=pd.DataFrame(truth).set_index('decision_time'),
                curve_truth=pd.DataFrame(curve_truth))


def generate(seed=1729, world='base', days=40):
    from .bond_ecosystem import build_ecosystem
    return build_ecosystem(generate_driver(seed,world,days))


def prepare(data,cfg):
    p=prepare_panel(data['quotes'],data['rates'],data['sessions'],cfg,trades=data['trades'],context=data.get('context'),as_of=data['sessions'].close_time.iloc[-1])
    return p,build_features(p,cfg)


def frozen_forecasts(research,panel,features,trades,test_start):
    """Batch equivalent of live inference, including decisions with missing outcomes.

    Training, transforms and CAL weights are never updated. Eligibility at decision
    time uses only current observations and the known session close.
    """
    cfg=research['config']; scfg=research['scenario_config']
    obs=build_state_observations(panel,features,cfg,scfg,trades)
    x,_=model_measurements(features,obs,cfg,research['use_flow'],research['use_vwap'])
    frames=[]
    for h,e in research['horizons'].items():
        if e['status']!='ready': continue
        ix=obs.index[(obs.index>=test_start)&obs.valid]
        ix=ix[ix+pd.Timedelta(minutes=h)<=panel.loc[ix,'session_close']]
        ps=e['state_ml_weight']*predict_head(e['state_head'],x.loc[ix],5)+(1-e['state_ml_weight'])*e['transition'][obs.loc[ix,'state_id'].astype(int)]
        pp=predict_head(e['price_head'],x.loc[ix],3)
        rows=[]
        for j,t in enumerate(ix):
            experts,_,diag=path_experts(e['bank'],x.loc[t],ps[j],pp[j])
            row=_forecast_summary(e,experts,ps[j],features.loc[t,'sigma_ticks'],diag)
            row.update(decision_time=t,horizon_minutes=h,session_id=panel.loc[t,'session_id'],
                observed_state=STATE_NAMES[int(obs.loc[t,'state_id'])],flow_available=bool(obs.loc[t,'flow_available']))
            rows.append(row)
        frames.append(pd.DataFrame(rows))
    return pd.concat(frames,ignore_index=True),obs,x


def bootstrap_sessions(values,seed=99):
    v=np.asarray(values,float); rng=np.random.default_rng(seed)
    if not len(v):return np.nan,np.nan
    b=rng.choice(v,size=(2000,len(v)),replace=True).mean(1)
    return float(np.quantile(b,.025)),float(np.quantile(b,.975))


def evaluate(predictions,panel,features,research,tag,folder):
    targets=make_targets(panel,features,research['config']); allrows=[]; metricrows=[]; dayrows=[]
    for h,p in predictions.groupby('horizon_minutes'):
        p=p.set_index('decision_time').join(targets[h],rsuffix='_actual')
        p['outcome_available']=p.class_id.notna()
        allrows.append(p.reset_index())
        f=p.loc[p.outcome_available].copy(); y=f.class_id.astype(int).to_numpy()
        if f.empty:
            metricrows.append(dict(run=tag,horizon_minutes=h,forecasts=len(p),scored=0,missing_outcomes=len(p),
                sessions=0,log_loss=np.nan,brier=np.nan,baseline_log_loss=np.nan,loss_difference=np.nan,
                difference_ci_low=np.nan,difference_ci_high=np.nan,endpoint_mae_ticks=np.nan,
                zero_forecast_mae_ticks=np.nan,endpoint_rmse_ticks=np.nan,zero_forecast_rmse_ticks=np.nan,
                interval_80_coverage=np.nan,interval_80_width=np.nan,long_mae80_coverage=np.nan,short_mae80_coverage=np.nan,
                mean_scenario_ess=float(p.effective_scenarios.mean()),mean_nearest_distance=float(p.nearest_distance.mean()),
                feature_coverage=float(p.observed_feature_fraction.mean()),flow_coverage=float(p.flow_available.mean())))
            pd.DataFrame(columns=['bin','rows','mean_confidence','accuracy']).to_csv(folder/f'reliability-{h}.csv',index=False)
            continue
        bank=research['horizons'][int(h)]['bank']; prior=np.bincount(bank['classes'],weights=bank['session_weights'],minlength=3);prior/=prior.sum()
        probs=f[['p_down','p_neutral','p_up']].to_numpy()
        f['loss']=-np.log(np.maximum(probs[np.arange(len(y)),y],1e-9))
        f['baseline_loss']=-np.log(np.maximum(prior[y],1e-9)); f['loss_difference']=f.loss-f.baseline_loss
        by=f.groupby('session_id')[['loss','baseline_loss','loss_difference']].mean()
        lo,hi=bootstrap_sessions(by.loss_difference)
        for sid,row in by.iterrows():dayrows.append(dict(run=tag,horizon_minutes=h,session_id=sid,**row.to_dict()))
        metric=_metrics(probs,y,f.return_ticks,f.endpoint_mean_ticks,f.session_id)
        w=_session_weights(f.session_id)
        metricrows.append(dict(run=tag,horizon_minutes=h,forecasts=len(p),scored=len(f),missing_outcomes=len(p)-len(f),
            sessions=f.session_id.nunique(),log_loss=metric['log_loss'],brier=metric['brier'],
            baseline_log_loss=float(by.baseline_loss.mean()),loss_difference=float(by.loss_difference.mean()),
            difference_ci_low=lo,difference_ci_high=hi,
            endpoint_mae_ticks=metric['endpoint_mae_ticks'],zero_forecast_mae_ticks=float(np.average(abs(f.return_ticks),weights=w)),
            endpoint_rmse_ticks=float(np.sqrt(np.average((f.return_ticks-f.endpoint_mean_ticks)**2,weights=w))),
            zero_forecast_rmse_ticks=float(np.sqrt(np.average(f.return_ticks**2,weights=w))),
            interval_80_coverage=float(np.average((f.return_ticks>=f.endpoint_q10_ticks)&(f.return_ticks<=f.endpoint_q90_ticks),weights=w)),
            interval_80_width=float(np.average(f.endpoint_q90_ticks-f.endpoint_q10_ticks,weights=w)),
            long_mae80_coverage=float(np.average(f.mae_long_ticks<=f.mae_long_q80_ticks,weights=w)),
            short_mae80_coverage=float(np.average(f.mae_short_ticks<=f.mae_short_q80_ticks,weights=w)),
            mean_scenario_ess=float(f.effective_scenarios.mean()),mean_nearest_distance=float(f.nearest_distance.mean()),
            feature_coverage=float(f.observed_feature_fraction.mean()),flow_coverage=float(f.flow_available.mean())))
        metric['reliability'].to_csv(folder/f'reliability-{h}.csv',index=False)
    joined=pd.concat(allrows,ignore_index=True)
    joined.to_csv(folder/'predictions-and-outcomes.csv.gz',index=False,compression='gzip')
    pd.DataFrame(dayrows).to_csv(folder/'session-losses.csv',index=False)
    return pd.DataFrame(metricrows),joined


def trade_ledger(predictions,panel,features,cfg,tag,folder):
    """One contract, one position per independent horizon/strategy book.

    Entry next minute; exit at original forecast expiry, so execution stays inside
    the forecast's target. Base slippage 1 tick roundtrip; stress 4. Fees C$4.
    No terminal-label filter: missing exit quotes use first fresh quote up to 5m
    later or record an unpriced trade, never quietly delete a losing outcome.
    """
    rows=[]; minute_rows=[]; reject=[]
    for h,frame in predictions.groupby('horizon_minutes'):
        frame=frame.sort_values('decision_time')
        for strategy in ('model','simple_momentum','always_long','always_short'):
            available_after=panel.index.min()
            equity=pd.Series(0.,index=panel.index); fees=pd.Series(0.,index=panel.index)
            for r in frame.to_dict('records'):
                t=pd.Timestamp(r['decision_time'])
                if t<=available_after: continue
                if strategy=='model':
                    if abs(r['indicator'])<.2: continue
                    direction=int(np.sign(r['indicator']))
                    if direction*r['endpoint_mean_ticks']<=features.loc[t,'spread_ticks']+1.4: continue
                elif strategy=='simple_momentum':
                    m=features.loc[t,'mom_z_30']
                    if not np.isfinite(m) or abs(m)<.75: continue
                    direction=int(np.sign(m))
                else: direction=1 if strategy=='always_long' else -1
                entry=t+pd.Timedelta(minutes=1); desired_exit=t+pd.Timedelta(minutes=int(h))
                if entry not in panel.index or not panel.loc[entry,'cgb_valid']:
                    reject.append(dict(run=tag,horizon_minutes=h,strategy=strategy,decision_time=t,reason='entry_quote_unavailable'));continue
                exit_time=desired_exit
                for delay in range(6):
                    candidate=desired_exit+pd.Timedelta(minutes=delay)
                    if candidate in panel.index and candidate<=panel.loc[t,'session_close'] and panel.loc[candidate,'cgb_valid']:
                        exit_time=candidate;break
                else:
                    reject.append(dict(run=tag,horizon_minutes=h,strategy=strategy,decision_time=t,reason='open_trade_exit_unpriced'))
                    available_after=panel.loc[t,'session_close'];continue
                en=panel.loc[entry]; ex=panel.loc[exit_time]
                if min(en.cgb_bid_size,en.cgb_ask_size,ex.cgb_bid_size,ex.cgb_ask_size)<1: raise AssertionError('Insufficient one-contract touch depth')
                base=futures_touch_benchmark(en.cgb_bid,en.cgb_ask,ex.cgb_bid,ex.cgb_ask,direction,1,cfg,fees_cad=4.,additional_slippage_ticks_per_contract=1.)
                row=dict(run=tag,horizon_minutes=int(h),strategy=strategy,session_id=r['session_id'],decision_time=t,
                    entry_time=entry,exit_time=exit_time,direction=direction,**base,
                    stress_net_cad=base['net_benchmark_cad']-30.,delayed_exit_minutes=(exit_time-desired_exit).total_seconds()/60)
                rows.append(row);available_after=exit_time
                # Mark to liquidation touch minute by minute; gap marks carry the
                # last observed quote and therefore understate within-gap risk.
                track=panel.loc[entry:exit_time]
                mark=(track.cgb_bid if direction==1 else track.cgb_ask).where(track.cgb_valid).ffill()
                fill=en.cgb_ask if direction==1 else en.cgb_bid
                value=direction*(mark-fill)/cfg.tick_size*cfg.tick_value_cad-7.
                value.iloc[-1]-=7. # split C$4 fees + 1 tick extra slippage across legs
                changes=value.diff();changes.iloc[0]=value.iloc[0]
                equity.loc[changes.index]+=changes
            curve=equity.cumsum(); peak=np.maximum.accumulate(np.r_[0.,curve.to_numpy()])[1:]
            sel=curve.loc[curve.index>=frame.decision_time.min()]
            for t,v in sel.items():minute_rows.append(dict(run=tag,horizon_minutes=h,strategy=strategy,decision_time=t,pnl_cad=v,drawdown_cad=peak[curve.index.get_loc(t)]-v))
    ledger=pd.DataFrame(rows);marks=pd.DataFrame(minute_rows)
    ledger.to_csv(folder/'trade-ledger.csv',index=False);marks.to_csv(folder/'marked-pnl.csv.gz',index=False,compression='gzip')
    pd.DataFrame(reject,columns=['run','horizon_minutes','strategy','decision_time','reason']).to_csv(folder/'execution-rejections.csv',index=False)
    summary=[]
    for (h,s),g in ledger.groupby(['horizon_minutes','strategy']):
        mark=marks[(marks.horizon_minutes==h)&(marks.strategy==s)]
        assert abs(mark.pnl_cad.iloc[-1]-g.net_benchmark_cad.sum())<1e-7
        summary.append(dict(run=tag,horizon_minutes=h,strategy=s,trades=len(g),long_trades=int((g.direction==1).sum()),
            short_trades=int((g.direction==-1).sum()),gross_cad=g.midpoint_change_cad.sum(),spread_cad=g.spread_crossing_cad.sum(),
            extra_slippage_cad=g.additional_slippage_cad.sum(),fees_cad=g.fees_cad.sum(),net_cad=g.net_benchmark_cad.sum(),
            stress_net_cad=g.stress_net_cad.sum(),win_fraction=(g.net_benchmark_cad>0).mean(),
            max_drawdown_cad=mark.drawdown_cad.max(),held_minutes=((pd.to_datetime(g.exit_time)-pd.to_datetime(g.entry_time)).dt.total_seconds()/60).sum()))
    return pd.DataFrame(summary)


def save_inputs(data,folder):
    folder.mkdir(parents=True,exist_ok=True)
    for name,frame in data.items():frame.to_csv(folder/f'{name}.csv.gz',index=name=='truth',compression='gzip')


def finalize_execution_status():
    """A priced subset is never presented as the P&L of an unpriced full book."""
    path=OUT/'execution-summary.csv';summary=pd.read_csv(path)
    # Zero trades is an observed policy outcome, not a missing experiment row.
    extra=[]
    for run in summary.run.unique():
        forecasts=pd.read_csv(OUT/'results'/run/'predictions-and-outcomes.csv.gz',usecols=['horizon_minutes'])
        for h in forecasts.horizon_minutes.unique():
            for strategy in ('model','simple_momentum','always_long','always_short'):
                if (summary.run.eq(run)&summary.horizon_minutes.eq(h)&summary.strategy.eq(strategy)).any():continue
                extra.append(dict(run=run,horizon_minutes=h,strategy=strategy,trades=0,long_trades=0,short_trades=0,
                    gross_cad=0.,spread_cad=0.,extra_slippage_cad=0.,fees_cad=0.,net_cad=0.,stress_net_cad=0.,
                    win_fraction=np.nan,max_drawdown_cad=0.,held_minutes=0.))
    if extra:summary=pd.concat([summary,pd.DataFrame(extra)],ignore_index=True)
    if 'priced_subset_net_cad' not in summary:summary['priced_subset_net_cad']=summary.net_cad
    summary['unpriced_trades']=0;summary['accounting_status']='complete_priced_book'
    summary.loc[summary.trades.eq(0),'accounting_status']='flat_no_trades'
    for run in summary.run.unique():
        rejected=pd.read_csv(OUT/'results'/run/'execution-rejections.csv')
        missing=rejected[rejected.reason.eq('open_trade_exit_unpriced')]
        for (h,strategy),rows in missing.groupby(['horizon_minutes','strategy']):
            mask=summary.run.eq(run)&summary.horizon_minutes.eq(h)&summary.strategy.eq(strategy)
            summary.loc[mask,'unpriced_trades']=len(rows)
            summary.loc[mask,'accounting_status']='INCOMPLETE_UNPRICED_OPEN_TRADE'
            summary.loc[mask,['net_cad','stress_net_cad','gross_cad','max_drawdown_cad']]=np.nan
    summary.to_csv(path,index=False)
    return summary


def run_experiment():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'COMPLETE.json').exists():raise SystemExit('Completed run exists; set CGB_SIMULATION_OUTPUT to a new folder to retain provenance.')
    dump_json(OUT/'protocol.json',PROTOCOL)
    cfg=ResearchConfig(feature_modules=tuple(PROTOCOL['modules']),min_train_sessions=24,min_cal_sessions=8,min_test_sessions=8)
    scfg=ScenarioConfig()
    dump_json(OUT/'resolved-config.json',dict(research=asdict(cfg),scenarios=asdict(scfg)))
    metrics=[]; accounts=[]; fits=[]; start=time.perf_counter()
    for seed in SEEDS:
        for world in ('base','null'):
            tag=f'{world}-{seed}'; folder=OUT/'results'/tag;folder.mkdir(parents=True,exist_ok=True)
            print(f'{tag}: generate and measure',flush=True)
            data=generate(seed,world);save_inputs(data,folder/'inputs')
            panel,features=prepare(data,cfg)
            print(f'{tag}: fit 24 TRAIN / 8 CAL / 8 TEST sessions',flush=True)
            research=fit_scenario_research(panel,features,cfg,scfg,data['trades'])
            if research['status']!='ready':raise RuntimeError({h:e.get('reason') for h,e in research['horizons'].items()})
            save_deployment(research,folder/'frozen-model')
            test_start=data['sessions'].open_time.iloc[32]
            pred,obs,x=frozen_forecasts(research,panel,features,data['trades'],test_start)
            met,joined=evaluate(pred,panel,features,research,tag,folder);metrics.append(met)
            accounts.append(trade_ledger(pred,panel,features,cfg,tag,folder))
            obs.to_csv(folder/'observations.csv.gz',compression='gzip'); features.to_csv(folder/'features.csv.gz',compression='gzip')
            for h,e in research['horizons'].items():fits.append(dict(run=tag,horizon_minutes=h,state_ml_weight=e['state_ml_weight'],
                local_weight=e['mixture_weights'][0],structural_weight=e['mixture_weights'][1],supervised_weight=e['mixture_weights'][2],
                train_paths=len(e['bank']['classes']),cal_paths=len(e['indices']['cal']),test_paths=len(e['indices']['test'])))
            print(f'{tag}: completed; elapsed {time.perf_counter()-start:.1f}s',flush=True)
            if seed==SEEDS[0] and world=='base':
                # A controlled CGB-only ablation, including removal of tape inputs.
                acfg=replace(cfg,feature_modules=('cgb',))
                afit=fit_scenario_research(panel,features,acfg,scfg,None)
                atag=f'cgb_only-{seed}'; afolder=OUT/'results'/atag;afolder.mkdir(parents=True,exist_ok=True)
                save_deployment(afit,afolder/'frozen-model')
                apred,_,_=frozen_forecasts(afit,panel,features,None,test_start)
                am,_=evaluate(apred,panel,features,afit,atag,afolder);metrics.append(am)
                accounts.append(trade_ledger(apred,panel,features,acfg,atag,afolder))
                for stress in PROTOCOL['stress_worlds']:
                    stag=f'{stress}-{seed}'; sfolder=OUT/'results'/stag;sfolder.mkdir(parents=True,exist_ok=True)
                    print(f'{stag}: frozen base model; no refitting',flush=True)
                    sd=generate(seed,stress);save_inputs(sd,sfolder/'inputs')
                    sp,sf=prepare(sd,cfg)
                    from pandas.testing import assert_frame_equal
                    assert_frame_equal(panel.loc[panel.index<test_start],sp.loc[sp.index<test_start])
                    assert_frame_equal(features.loc[features.index<test_start],sf.loc[sf.index<test_start])
                    pr,so,_=frozen_forecasts(research,sp,sf,sd['trades'],test_start)
                    sm,_=evaluate(pr,sp,sf,research,stag,sfolder);metrics.append(sm)
                    accounts.append(trade_ledger(pr,sp,sf,cfg,stag,sfolder))
                    so.to_csv(sfolder/'observations.csv.gz',compression='gzip')
                    dump_json(sfolder/'frozen-model-reference.json',dict(source='../base-1729/frozen-model',same_train_cal_prefix=True))
            pd.concat(metrics,ignore_index=True).to_csv(OUT/'metrics.csv',index=False)
            pd.concat(accounts,ignore_index=True).to_csv(OUT/'execution-summary.csv',index=False)
            pd.DataFrame(fits).to_csv(OUT/'fitted-weights.csv',index=False)
    finalize_execution_status()
    dump_json(OUT/'COMPLETE.json',dict(elapsed_seconds=time.perf_counter()-start,runs=11,synthetic=True))
    print('COMPLETE',time.perf_counter()-start,flush=True)


if __name__=='__main__':run_experiment()
