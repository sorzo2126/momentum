"""Assemble tables, scientific plots and an executed reading notebook from a run."""
from pathlib import Path
import hashlib,json,sys,platform,ast,base64
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
from .structured_simulation import OUT,ROOT,PROTOCOL
from momentum.deployment import load_deployment
from momentum.states import model_measurements,STATE_NAMES
from momentum.scenarios import predict_head,path_experts,weighted_quantile

plt.rcParams.update({'figure.dpi':130,'savefig.dpi':165,'font.size':10,
    'axes.spines.top':False,'axes.spines.right':False,'axes.grid':True,
    'grid.alpha':.2,'figure.facecolor':'white','axes.facecolor':'white'})
COLORS=['#2563eb','#e87929','#179c7d','#ac45a8','#d5454b','#6b7280']
FIG=OUT/'figures';FIG.mkdir(exist_ok=True,parents=True)

def read(name,run='base-1729'):
    return pd.read_csv(OUT/'results'/run/name)

def save(fig,name):
    fig.savefig(FIG/f'{name}.png',bbox_inches='tight');plt.close(fig)

def indexed(name,run='base-1729'):
    d=read(name,run);d['decision_time']=pd.to_datetime(d['decision_time'],utc=True)
    return d.set_index('decision_time')

def plots():
    from .structured_simulation import finalize_execution_status
    finalize_execution_status()
    m=pd.read_csv(OUT/'metrics.csv');a=pd.read_csv(OUT/'execution-summary.csv');w=pd.read_csv(OUT/'fitted-weights.csv')
    base='base-1729';p=read('predictions-and-outcomes.csv.gz');tr=indexed('inputs/truth.csv.gz')
    f=indexed('features.csv.gz');obs=indexed('observations.csv.gz')
    test=tr[tr.day_number>=32];testdays=test.session_id.unique()
    fig,ax=plt.subplots(figsize=(13,5));ax.axis('off')
    boxes=[(.03,.67,'Hidden synthetic mechanisms\npressure • liquidity • shocks'),(.37,.67,'Observable inputs\nquotes • curve • signed tape'),(.71,.67,'Causal measurements\nreceiver clocks • past windows'),(.03,.12,'24 TRAIN sessions\npaths • trees • transitions'),(.37,.12,'8 CAL sessions\nconvex mixture weights'),(.71,.12,'8 TEST sessions\nprobabilities • paths • costs')]
    for x,y,label in boxes:ax.text(x,y,label,transform=ax.transAxes,va='center',bbox=dict(boxstyle='round,pad=.8',facecolor='#eff6ff',edgecolor='#6484aa'),fontsize=11)
    for x1,y1,x2,y2 in [(.27,.67,.36,.67),(.62,.67,.70,.67),(.81,.51,.15,.27),(.28,.12,.36,.12),(.63,.12,.7,.12)]:ax.annotate('',xy=(x2,y2),xytext=(x1,y1),xycoords='axes fraction',arrowprops=dict(arrowstyle='->',lw=1.7,color='#34455a'))
    fig.suptitle('Synthetic experiment: mechanisms are hidden from the estimator',fontsize=15);save(fig,'01-experiment')
    fig,ax=plt.subplots(figsize=(12,2.7))
    for start,width,color,label in [(0,24,COLORS[0],'TRAIN: model parameters'),(24,8,COLORS[1],'CAL: mixture weights'),(32,8,COLORS[2],'TEST: no fitting')]:
        ax.barh(0,width,left=start,color=color,height=.6);ax.text(start+width/2,0,label,ha='center',va='center',color='white',weight='bold')
    ax.set(xlim=(0,40),yticks=[],xlabel='Synthetic session number',title='Chronological holdout; all target paths end inside their own partition');save(fig,'02-split')
    day=test[test.session_id==testdays[0]];ix=day.index;oo=obs.loc[obs.index.intersection(ix)];ff=f.loc[ix]
    fig,axs=plt.subplots(5,1,figsize=(12,12),sharex=True)
    minute=day.minute
    axs[0].plot(minute,(day.cgb_mid-day.cgb_mid.iloc[0])/.01,label='CGB midpoint');axs[0].plot(minute,(ff.vwap_distance_ticks*-1+(day.cgb_mid-day.cgb_mid.iloc[0])/.01),label='Observed VWAP',alpha=.8)
    axs[0].set(ylabel='Ticks from open',title='First TEST session, chosen in advance');axs[0].legend()
    axs[1].plot(minute,day.pressure_us,label='Hidden US pressure');axs[1].plot(minute,day.pressure_cad,label='Hidden CAD pressure');axs[1].legend();axs[1].set_ylabel('Latent units')
    axs[2].plot((oo.index-ix[0]).total_seconds()/60,oo.flow_pressure,label='Observed signed-volume fraction');axs[2].plot((oo.index-ix[0]).total_seconds()/60,oo.absorption,label='Observed absorption proxy');axs[2].legend()
    axs[3].plot(minute,day.vol_multiplier,label='Volatility multiplier');axs[3].plot(minute,day.depth_multiplier,label='Depth multiplier');axs[3].legend()
    axs[4].step((oo.index-ix[0]).total_seconds()/60,oo.state_id,where='post');axs[4].set(yticks=range(5),yticklabels=STATE_NAMES,xlabel='Minutes since synthetic session open',ylabel='Observed state')
    for ax in axs:
        for x in (30,150,300):ax.axvline(x,color='grey',ls=':',alpha=.6)
    fig.tight_layout();save(fig,'03-first-session')
    fig,axs=plt.subplots(2,4,figsize=(14,7),sharex=True)
    for ax,sid in zip(axs.flat,testdays):
        d=test[test.session_id==sid];ax.plot(d.minute,(d.cgb_mid-d.cgb_mid.iloc[0])/.01,color=COLORS[0]);ax.set(title=sid,xlabel='Minute',ylabel='Ticks from open')
    fig.suptitle('Every base-seed TEST session: no selection by profitability');fig.tight_layout();save(fig,'04-all-test-sessions')
    returns=tr.groupby('session_id').cgb_mid.diff()/.01
    ed=[]
    for sid,g in tr.groupby('session_id'):
        r=g.cgb_mid.diff().dropna()/.01
        ed.append(dict(session_id=sid,realized_sigma_ticks=r.std(),range_ticks=(g.cgb_mid.max()-g.cgb_mid.min())/.01,
            move_ticks=(g.cgb_mid.iloc[-1]-g.cgb_mid.iloc[0])/.01,volume=0,
            lag1_return_acf=r.autocorr(1),lag1_absolute_acf=r.abs().autocorr(1)))
    pd.DataFrame(ed).to_csv(OUT/'market-diagnostics.csv',index=False)
    fig,axs=plt.subplots(2,2,figsize=(12,8))
    r=returns.dropna();axs[0,0].hist(r,bins=100,density=True,color=COLORS[0],alpha=.75);axs[0,0].set(xlim=(-8,8),title='One-minute returns',xlabel='CGB ticks',ylabel='Density')
    stats.probplot((r-r.mean())/r.std(),dist='norm',plot=axs[0,1]);axs[0,1].set_title('Normal Q–Q: deliberately heavier-tailed innovations')
    lags=np.arange(1,31);ac=[];av=[]
    for lag in lags:
        ac.append(np.mean([x.cgb_mid.diff().autocorr(lag) for _,x in tr.groupby('session_id')]))
        av.append(np.mean([x.cgb_mid.diff().abs().autocorr(lag) for _,x in tr.groupby('session_id')]))
    axs[1,0].plot(lags,ac,label='Returns');axs[1,0].plot(lags,av,label='Absolute returns');axs[1,0].legend();axs[1,0].set(xlabel='Lag (minutes)',ylabel='Mean within-session correlation',title='No overnight returns in autocorrelation')
    axs[1,1].scatter(tr.depth_multiplier,tr.spread_ticks,s=3,alpha=.1);axs[1,1].set(xlabel='Hidden depth multiplier',ylabel='Displayed spread (ticks)',title='Spread and liquidity share a mechanism')
    fig.tight_layout();save(fig,'05-market-diagnostics')
    cols=['mom_z_30','us_move_30','cad_level5_bp_30','cad_slope25_bp_30','cad_slope510_bp_30','book_imbalance','vwap_distance_ticks']
    corr=f.loc[test.index,cols].corr();corr.to_csv(OUT/'feature-correlations.csv')
    fig,ax=plt.subplots(figsize=(10,8));im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r');ax.set(xticks=range(len(cols)),yticks=range(len(cols)),xticklabels=cols,yticklabels=cols,title='Correlated measurements are not independent confirmations')
    plt.setp(ax.get_xticklabels(),rotation=50,ha='right');fig.colorbar(im,ax=ax);fig.tight_layout();save(fig,'06-feature-correlation')
    model=load_deployment(OUT/'results'/base/'frozen-model')
    fig,axs=plt.subplots(1,3,figsize=(15,4.5))
    for ax,(h,e) in zip(axs,model['horizons'].items()):
        im=ax.imshow(e['transition'],vmin=0,vmax=1,cmap='Blues');ax.set(title=f'{h} minute transition prior',xticks=range(5),yticks=range(5),xlabel='Future observed state',ylabel='Current observed state')
        for i in range(5):
            for j in range(5):ax.text(j,i,f'{e["transition"][i,j]:.2f}',ha='center',color='white' if e['transition'][i,j]>.5 else 'black',fontsize=8)
    fig.suptitle('TRAIN state transitions: empirical, horizon-specific; IDs follow Figure 3');fig.tight_layout();save(fig,'07-transitions')
    fig,axs=plt.subplots(1,3,figsize=(14,5),sharey=True)
    for ax,h in zip(axs,[60,120,240]):
        ww=w[w.horizon_minutes==h];bottom=np.zeros(len(ww))
        for j,col in enumerate(['local_weight','structural_weight','supervised_weight']):
            ax.bar(np.arange(len(ww)),ww[col],bottom=bottom,label=col.replace('_weight',''),color=COLORS[j]);bottom+=ww[col].to_numpy()
        ax.set(title=f'{h} minutes',xticks=np.arange(len(ww)),xticklabels=ww.run,ylim=(0,1));plt.setp(ax.get_xticklabels(),rotation=65,ha='right')
    axs[0].set_ylabel('CAL-selected mixture weight');axs[-1].legend(loc='upper left',bbox_to_anchor=(1,1));fig.tight_layout();save(fig,'08-calibration-weights')
    names=list(m.run.unique())
    fig,axs=plt.subplots(1,3,figsize=(15,8),sharey=True)
    for ax,h in zip(axs,[60,120,240]):
        mm=m[m.horizon_minutes==h].set_index('run').reindex(names);y=np.arange(len(mm));value=mm.loss_difference
        ax.barh(y,value,color=np.where(value<0,COLORS[2],COLORS[4]),alpha=.7)
        ax.errorbar(value,y,xerr=np.array([value-mm.difference_ci_low,mm.difference_ci_high-value]),fmt='none',color='#222',capsize=2)
        for pos,v in enumerate(value):
            if pd.isna(v):ax.text(.005,pos,'unscorable',va='center',fontsize=8,color='#6b7280')
        ax.axvline(0,color='black',lw=1);ax.set(title=f'{h} minutes',yticks=y,yticklabels=names,xlabel='Model loss minus TRAIN-frequency loss')
    fig.suptitle('Negative is better. Whiskers: descriptive 95% session-bootstrap intervals (8 sessions).');fig.tight_layout();save(fig,'09-forecast-loss')
    fig,axs=plt.subplots(1,3,figsize=(14,4.5))
    for ax,h in zip(axs,[60,120,240]):
        rr=read(f'reliability-{h}.csv');ax.plot([0,1],[0,1],'--',color='grey');ax.plot(rr.mean_confidence,rr.accuracy,'o-',color=COLORS[0]);ax.set(xlim=(.3,1),ylim=(0,1),title=f'{h} minutes',xlabel='Mean top-class probability',ylabel='Observed accuracy')
        for _,row in rr.iterrows():ax.annotate(f'n={int(row.rows)}',(row.mean_confidence,row.accuracy),fontsize=8,xytext=(3,5),textcoords='offset points')
    fig.suptitle('Base 1729 calibration: overlapping forecasts are not independent trials');fig.tight_layout();save(fig,'10-reliability')
    fig,axs=plt.subplots(1,3,figsize=(15,7),sharey=True)
    for ax,h in zip(axs,[60,120,240]):
        mm=m[m.horizon_minutes==h].set_index('run').reindex(names);ax.barh(names,mm.interval_80_coverage,color=COLORS[0]);ax.axvline(.8,color=COLORS[4],ls='--');ax.set(xlim=(0,1),title=f'{h} minutes',xlabel='Endpoint 10%–90% interval coverage')
        for pos,v in enumerate(mm.interval_80_coverage):
            if pd.isna(v):ax.text(.02,pos,'unscorable',va='center',fontsize=8)
    fig.tight_layout();save(fig,'11-interval-coverage')
    fig,axs=plt.subplots(1,3,figsize=(14,4.5))
    for ax,h in zip(axs,[60,120,240]):
        d=p[p.horizon_minutes==h];ax.scatter(d.endpoint_mean_ticks,d.return_ticks,s=9,alpha=.25);lim=max(abs(d.return_ticks).max(),abs(d.endpoint_mean_ticks).max());ax.plot([-lim,lim],[-lim,lim],'--',color='grey');ax.axhline(0,color='grey',lw=.5);ax.set(title=f'{h} minutes',xlabel='Forecast mean (ticks)',ylabel='Realized endpoint (ticks)')
    fig.tight_layout();save(fig,'12-endpoint-forecast')
    fig,axs=plt.subplots(1,2,figsize=(14,7),sharey=True)
    mm=m[m.horizon_minutes==120].set_index('run').reindex(names)
    for ax,side in zip(axs,['long','short']):ax.barh(names,mm[f'{side}_mae80_coverage'],color=COLORS[0]);ax.axvline(.8,color=COLORS[4],ls='--');ax.set(xlim=(0,1),title=f'120 minute {side}: adverse-excursion 80% bound',xlabel='Empirical coverage')
    fig.tight_layout();save(fig,'13-path-risk')
    # One fixed decision time, not chosen based on outcome or forecast confidence.
    decision=day.index[190];x,_=model_measurements(f,obs,model['config'],model['use_flow'],model['use_vwap']);sigma=f.loc[decision,'sigma_ticks'];fan=[]
    fig,axs=plt.subplots(1,3,figsize=(15,4.7))
    for ax,h in zip(axs,[60,120,240]):
        e=model['horizons'][h];ps=e['state_ml_weight']*predict_head(e['state_head'],x.loc[[decision]],5)[0]+(1-e['state_ml_weight'])*e['transition'][int(obs.loc[decision,'state_id'])]
        pp=predict_head(e['price_head'],x.loc[[decision]],3)[0];experts,_,_=path_experts(e['bank'],x.loc[decision],ps,pp);weights=e['mixture_weights']@experts;paths=e['bank']['paths']*sigma
        lo=np.array([weighted_quantile(paths[:,j],weights,.1) for j in range(h+1)]);hi=np.array([weighted_quantile(paths[:,j],weights,.9) for j in range(h+1)]);mean=weights@paths
        actual=(tr.loc[decision:decision+pd.Timedelta(minutes=h),'cgb_mid'].to_numpy()-tr.loc[decision,'cgb_mid'])/.01
        ax.fill_between(range(h+1),lo,hi,color=COLORS[0],alpha=.18,label='Pointwise 10%–90%');ax.plot(mean,color=COLORS[0],label='Mean path');ax.plot(actual,color='black',label='Realized');ax.set(title=f'{h} minute bank',xlabel='Minutes after decision',ylabel='CGB ticks')
        for j in range(h+1):fan.append(dict(horizon_minutes=h,minute=j,q10=lo[j],q90=hi[j],mean=mean[j],actual=actual[j]))
    axs[0].legend(fontsize=8);fig.suptitle('First TEST session, minute 190: pointwise bands are not simultaneous path guarantees');fig.tight_layout();save(fig,'14-path-fans');pd.DataFrame(fan).to_csv(OUT/'fixed-decision-path-fans.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(15,5),sharey=True)
    for ax,h in zip(axs,[60,120,240]):
        aa=a[(a.horizon_minutes==h)&(a.strategy=='model')].set_index('run').reindex(names);y=np.arange(len(aa));ax.barh(y-.17,aa.net_cad,height=.32,label='1 tick extra',color=COLORS[0]);ax.barh(y+.17,aa.stress_net_cad,height=.32,label='4 ticks extra',color=COLORS[1]);ax.axvline(0,color='black');ax.set(yticks=y,yticklabels=names,title=f'{h} minutes',xlabel='Net C$ / one-contract book')
        for pos,(_,row) in enumerate(aa.iterrows()):
            if pd.isna(row.net_cad):ax.text(40,pos,'unpriced book',va='center',fontsize=8)
            elif row.trades==0:ax.text(40,pos,'no trades',va='center',fontsize=8)
    axs[-1].legend();fig.suptitle('Execution sensitivity: spread + C$4 fees already included');fig.tight_layout();save(fig,'15-execution-stress')
    marks=read('marked-pnl.csv.gz');fig,axs=plt.subplots(3,1,figsize=(12,10),sharex=True)
    for ax,h in zip(axs,[60,120,240]):
        for strategy,g in marks[marks.horizon_minutes==h].groupby('strategy'):
            ax.plot(np.arange(len(g)),g.pnl_cad,label=strategy)
        ax.set(title=f'{h} minute independent books',ylabel='Marked net P&L (C$)');ax.legend(ncol=4,fontsize=8)
    axs[-1].set_xlabel('TEST minute observations, overnight intervals omitted');fig.tight_layout();save(fig,'16-marked-pnl')
    fig,axs=plt.subplots(1,3,figsize=(15,4.5))
    for ax,h in zip(axs,[60,120,240]):
        mm=m[m.horizon_minutes==h]
        ax.scatter(mm.mean_nearest_distance,mm.log_loss,s=55,color=COLORS[0])
        for _,r in mm.iterrows():ax.annotate(r.run,(r.mean_nearest_distance,r.log_loss),fontsize=7,xytext=(3,3),textcoords='offset points')
        ax.set(title=f'{h} minutes',xlabel='Mean nearest TRAIN distance',ylabel='Log loss')
    fig.suptitle('Support diagnostics are warnings, not calibrated rejection rules');fig.tight_layout();save(fig,'17-support')
    fig,axs=plt.subplots(1,2,figsize=(13,5))
    mm=m[m.horizon_minutes==120]
    axs[0].barh(mm.run,mm.feature_coverage,color=COLORS[0]);axs[0].set(xlim=(0,1),title='Mean observed selected-feature fraction',xlabel='Coverage')
    axs[1].barh(mm.run,mm.missing_outcomes,color=COLORS[1]);axs[1].set(title='Published forecasts whose paths cannot be scored',xlabel='Missing target count')
    fig.tight_layout();save(fig,'18-data-availability')
    fig,axs=plt.subplots(1,2,figsize=(12,4.5))
    arr=np.load(OUT/'example-audit'/'variant-1-arrays.npz');axs[0].plot(arr['equity']);axs[0].set(title='Provided notebook: reproduced accounting equity',xlabel='Synthetic tick',ylabel='Declared equity units')
    axs[1].hist(arr['pnl'][arr['pnl']!=0],bins=45,color=COLORS[1]);axs[1].set(title='Not a complete inventory mark-to-market ledger',xlabel='Nonzero tick accounting P&L',ylabel='Count')
    fig.suptitle('Reference example only: its 26.113% is not comparable with CGB returns');fig.tight_layout();save(fig,'19-example-audit')
    rows=[]
    for run in names:
        pred=read('predictions-and-outcomes.csv.gz',run)
        for h,g in pred[pred.outcome_available].groupby('horizon_minutes'):
            loss=(g.endpoint_q90_ticks-g.endpoint_q10_ticks)+10*np.maximum(g.endpoint_q10_ticks-g.return_ticks,0)+10*np.maximum(g.return_ticks-g.endpoint_q90_ticks,0)
            for side in ['long','short']:
                residual=g[f'mae_{side}_ticks']-g[f'mae_{side}_q80_ticks']
                rows.append(dict(run=run,horizon_minutes=h,side=side,mean_interval_score80=float(loss.groupby(g.session_id).mean().mean()),
                    pinball80=float(pd.Series(np.maximum(.8*residual,-.2*residual),index=g.index).groupby(g.session_id).mean().mean())))
    pd.DataFrame(rows).to_csv(OUT/'proper-path-scores.csv',index=False)
    fig,axs=plt.subplots(1,3,figsize=(14,4.7))
    for ax,h in zip(axs,[60,120,240]):
        d=p[p.horizon_minutes==h].copy();d['bucket']=pd.cut(d.indicator,[-1,-.5,-.2,.2,.5,1],include_lowest=True)
        g=d.groupby('bucket',observed=True).agg(realized=('return_ticks','mean'),forecast=('endpoint_mean_ticks','mean'),count=('indicator','size'))
        ax.plot(np.arange(len(g)),g.realized,'o-',label='Realized');ax.plot(np.arange(len(g)),g.forecast,'o-',label='Forecast');ax.set(xticks=range(len(g)),xticklabels=g.index.astype(str),title=f'{h} minutes',ylabel='Ticks');plt.setp(ax.get_xticklabels(),rotation=45,ha='right')
        for i,n in enumerate(g['count']):ax.annotate(f'n={n}',(i,g.realized.iloc[i]),fontsize=8,xytext=(0,5),textcoords='offset points')
    axs[0].legend();fig.suptitle('Base 1729: stronger indicator is a hypothesis about stronger continuation');fig.tight_layout();save(fig,'20-indicator-buckets')
    bond_plots()
    return m,a,w


def bond_plots():
    from .bond_ecosystem import TENORS,bond_values,carry_future
    curves=read('inputs/curves.csv.gz');curves['decision_time']=pd.to_datetime(curves.decision_time,utc=True)
    tr=indexed('inputs/truth.csv.gz');day=tr[tr.day_number==32]
    fig,axs=plt.subplots(1,3,figsize=(15,4.8))
    for minute,color in zip([0,35,155,305,480],COLORS):
        row=curves[curves.decision_time==day.index[minute]].iloc[0]
        for ax,country in zip(axs,['CAD','US','OIS']):
            ax.plot(TENORS,[row[f'{country}_zero_{t:g}y_bp'] for t in TENORS],label=f'minute {minute}',color=color);ax.set(title=f'{country} zero curve',xlabel='Years',ylabel='Continuously compounded bp')
    axs[-1].legend(fontsize=8);fig.suptitle('First TEST day: all tenors share level, slope and curvature coordinates');fig.tight_layout();save(fig,'21-zero-curves')
    cash=read('inputs/cash_bonds.csv.gz');cash['decision_time']=pd.to_datetime(cash.decision_time,utc=True)
    fut=read('inputs/futures_valuation.csv.gz');fut['decision_time']=pd.to_datetime(fut.decision_time,utc=True)
    fig,axs=plt.subplots(1,3,figsize=(15,4.5))
    cb=cash[cash.instrument.isin(['CAD2','CAD5','CAD10']) & (cash.decision_time==day.index[190])]
    axs[0].bar(cb.instrument,cb.dv01_per_100k,color=COLORS[:3]);axs[0].set(title='Cash DV01 per C$100,000 face',ylabel='C$ per parallel bp')
    k=cb.set_index('instrument')[['krd2_per_100k','krd5_per_100k','krd10_per_100k']];k.plot.bar(stacked=True,ax=axs[1],color=COLORS[:3]);axs[1].set(title='Key-rate decomposition',ylabel='C$ / bp');axs[1].legend(fontsize=8)
    for name,g in fut[fut.decision_time.isin(day.index)].groupby('instrument'):
        if name=='US10':continue
        axs[2].plot(np.arange(len(g)),g.dv01,label=name)
    axs[2].set(title='Futures DV01 per contract',xlabel='Session minute',ylabel='C$ / bp');axs[2].legend();fig.tight_layout();save(fig,'22-risk-units')
    fig,axs=plt.subplots(1,2,figsize=(13,5))
    d=curves[curves.decision_time.isin(day.index)]
    for col in ['CGB_A_delivery_cost','CGB_B_delivery_cost','CGB_C_delivery_cost']:axs[0].plot(np.arange(len(d)),d[col],label=col.replace('_delivery_cost',''))
    axs[0].set(title='Coupon/repo-adjusted delivery candidates',xlabel='Session minute',ylabel='Theoretical futures points');axs[0].legend()
    spec=read('inputs/bond_specs.csv.gz');shifts=np.linspace(-.02,.04,121);r=curves.iloc[0]
    for _,s in spec[spec.group=='CGB'].iterrows():
        pars=(np.full(len(shifts),r.gov_level)+shifts,np.full(len(shifts),r.gov_slope),np.full(len(shifts),r.gov_curvature))
        dirty=bond_values(*pars,np.zeros(len(shifts)),s.initial_maturity_years,s.coupon)[0]
        fwd=carry_future(dirty,np.full(len(shifts),r.repo_rate-(.0003 if s.instrument.endswith('A') else 0)),np.zeros(len(shifts)),s.initial_maturity_years,s.coupon,120/365)[0]
        axs[1].plot(shifts*1e4,fwd,label=s.instrument)
    axs[1].set(title='Independent curve stress, repo held fixed',xlabel='Parallel zero-curve bump (bp)',ylabel='Futures delivery cost');axs[1].legend();fig.tight_layout();save(fig,'23-delivery-basket')
    context=read('inputs/context.csv.gz');context['event_time']=pd.to_datetime(context.event_time,utc=True)
    fig,axs=plt.subplots(2,1,figsize=(12,7),sharex=True)
    for ax,name in zip(axs,['SPX','VIX']):
        z=context[(context.instrument==name)&(context.event_time>=day.index[0])&(context.event_time<=day.index[-1])]
        ax.plot(np.arange(len(z)),z.value);ax.set(title=f'Synthetic {name} context — generated, not selected as a predictor')
    axs[-1].set_xlabel('Session minute');fig.tight_layout();save(fig,'24-context')
    cash_ledger=[]
    from momentum.execution import cash_bond_touch_benchmark
    bonds=cash[cash.instrument=='CAD10'].set_index('decision_time');cgb=fut[fut.instrument=='CGB'].set_index('decision_time')
    trades=read('trade-ledger.csv');trades=trades[trades.strategy=='model']
    for row in trades.to_dict('records'):
        entry=pd.Timestamp(row['entry_time']);exit_time=pd.Timestamp(row['exit_time']);en=bonds.loc[entry];ex=bonds.loc[exit_time]
        face=100000*cgb.loc[entry,'dv01']/en.dv01_per_100k
        held_years=(exit_time-entry).total_seconds()/(365*86400)
        # Net funding friction after collateral/proceeds remuneration; explicitly
        # not charging full repo to both long and short positions.
        financing=.001*held_years*face*en.dirty/100
        ledger=cash_bond_touch_benchmark(en.bid_clean,en.ask_clean,ex.bid_clean,ex.ask_clean,en.accrued,ex.accrued,face,int(row['direction']),
            financing_and_borrow_cad=financing,fees_cad=4,additional_slippage_cad=.002*face/100)
        cash_ledger.append(dict(horizon_minutes=row['horizon_minutes'],decision_time=row['decision_time'],direction=row['direction'],
            face_amount=face,matched_entry_dv01=cgb.loc[entry,'dv01'],futures_net=row['net_benchmark_cad'],
            cash_net=ledger['net_benchmark_cad'],funding_cost=financing,**{k:v for k,v in ledger.items() if k!='net_benchmark_cad'}))
    cl=pd.DataFrame(cash_ledger);cl.to_csv(OUT/'cash-versus-futures-ledger.csv',index=False)
    fig,ax=plt.subplots(figsize=(10,5));comparison=cl.groupby('horizon_minutes')[['futures_net','cash_net']].sum();comparison.plot.bar(ax=ax,color=COLORS[:2]);ax.set(title='Same decisions, entry DV01 matched; different instruments and assumed costs',ylabel='Net C$',xlabel='Horizon (minutes)');fig.tight_layout();save(fig,'25-cash-versus-futures')


if __name__=='__main__':
    if not (OUT/'COMPLETE.json').exists():raise SystemExit('Wait for all declared experiments to finish.')
    plots()
    print('Created 25 figures and additional diagnostic tables.')
