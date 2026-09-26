"""Synthetic CAD/US curves and discounted-cash-flow pricing.

Conventions are explicit teaching conventions, not an exchange-certified pricer:
ACT/365 time, exact fractional-year semiannual cash flows, continuously compounded
zero curves, continuously compounded repo, synthetic conversion factors at 6%.
No dynamic risk-neutral no-arbitrage claim is made for the physical shock process.
"""
import numpy as np
import pandas as pd

TENORS=np.array([.25,.5,1.,2.,3.,4.,5.,7.,10.,15.,20.,30.])
BONDS=[('CAD2',2.25,.030,'benchmark'),('CAD5',5.25,.0325,'benchmark'),('CAD10',10.25,.035,'benchmark'),
       ('CGZ_A',1.75,.03,'CGZ'),('CGZ_B',2.25,.04,'CGZ'),
       ('CGF_A',4.25,.03,'CGF'),('CGF_B',5.25,.04,'CGF'),
       ('CGB_A',8.25,.03,'CGB'),('CGB_B',9.25,.04,'CGB'),('CGB_C',10.25,.045,'CGB'),
       ('US2',2.25,.04,'US'),('US5',5.25,.0425,'US'),('US10',10.25,.045,'US'),
       ('US10_A',7.25,.04,'US10'),('US10_B',9.25,.045,'US10')]


def loadings(t,decay=2.5):
    t=np.asarray(t,float);x=t/decay;l1=-np.expm1(-x)/x
    return l1,l1-np.exp(-x)


def zero_curve(a,b,c,t):
    l1,l2=loadings(t)
    return np.asarray(a)[...,None]+np.asarray(b)[...,None]*l1+np.asarray(c)[...,None]*l2


def schedule(maturity,coupon):
    times=np.arange(.25,maturity+.001,.5);cash=np.full(len(times),100*coupon/2);cash[-1]+=100
    return times,cash


def bond_values(a,b,c,age,maturity,coupon,bumps=None):
    times,cash=schedule(maturity,coupon);tau=times[None,:]-np.asarray(age)[:,None]
    remaining=tau>1e-12;safe=np.maximum(tau,1e-8)
    z=zero_curve(a,b,c,safe)
    if bumps is not None:z=z+bumps(safe)
    pv=np.where(remaining,cash[None,:]*np.exp(-z*safe),0.)
    dirty=pv.sum(1)
    next_coupon=np.min(np.where(remaining,tau,np.inf),axis=1)
    accrued=100*coupon*(.5-next_coupon)
    return dirty,dirty-accrued,accrued,pv,safe,cash,remaining


def ytm_from_dirty(dirty,tau,cash,remaining):
    y=np.full(len(dirty),.04)
    for _ in range(10):
        pv=np.where(remaining,cash*np.exp(-2*tau*np.log1p(y[:,None]/2)),0.)
        price=pv.sum(1);derivative=-(pv*tau/(1+y[:,None]/2)).sum(1)
        step=(price-dirty)/derivative;y-=step
        if np.max(abs(step))<1e-12:break
    return y


def conversion_factor(maturity,coupon,delivery):
    times,cash=schedule(maturity,coupon);mask=times>delivery
    accrued=100*coupon*(.5-(times[mask][0]-delivery))
    dirty=np.sum(cash[mask]*(1.03)**(-2*(times[mask]-delivery)))
    return float((dirty-accrued)/100),float(accrued)


def carry_future(dirty,repo,age,maturity,coupon,delivery):
    cf,accrued_delivery=conversion_factor(maturity,coupon,delivery)
    times,cash=schedule(maturity,coupon)
    paid=((times[None,:]>age[:,None])&(times[None,:]<=delivery))
    income=(paid*cash[None,:]*np.exp(repo[:,None]*(delivery-times[None,:]))).sum(1)
    return (dirty*np.exp(repo*(delivery-age))-income-accrued_delivery)/cf,cf,accrued_delivery,income


def build_ecosystem(data):
    """Reprice every observable from shared latent duration and policy coordinates.

    Driver CGB/US price coordinates are converted to yield-level coordinates, then
    discarded as observed prices. Actual quotes below come from cash-flow pricing.
    """
    tr=data['truth'].copy();idx=tr.index;n=len(idx)
    age=(idx-idx[0]).total_seconds().to_numpy()/(365*24*3600);delivery=120/365
    # Continuous physical coordinates: level, domestic policy slope, term-premium
    # curvature. These are assumed loadings, not fitted economics.
    a=.038-(tr.latent_mid.to_numpy()-120)/850
    b=-.006+tr.policy_factor.to_numpy()*1e-3
    c=.003+tr.pressure_cad.to_numpy()*8e-5
    au=.045-(tr.latent_us.to_numpy()-112)/1000
    bu=-.008+tr.pressure_us.to_numpy()*7e-5
    cu=.004+tr.pressure_us.to_numpy()*4e-5
    # OIS curve is separate from government-bond convenience/liquidity basis.
    ao=a-.0012;bo=b+.0004;co=c
    repo=zero_curve(ao,bo,co,np.array([1/365]))[:,0]+.0005
    curves=pd.DataFrame({'decision_time':idx,'gov_level':a,'gov_slope':b,'gov_curvature':c,
        'us_level':au,'us_slope':bu,'us_curvature':cu,'ois_level':ao,'ois_slope':bo,'ois_curvature':co,'repo_rate':repo})
    for country,params in [('CAD',(a,b,c)),('US',(au,bu,cu)),('OIS',(ao,bo,co))]:
        zeros=zero_curve(*params,TENORS);discounts=np.exp(-zeros*TENORS)
        for j,t in enumerate(TENORS):
            curves[f'{country}_zero_{t:g}y_bp']=zeros[:,j]*1e4
            curves[f'{country}_discount_{t:g}y']=discounts[:,j]
    cashrows=[];future_candidates={};specs=[];bench_y={};bench_risk={}
    for name,maturity,coupon,group in BONDS:
        params=(au,bu,cu) if name.startswith('US') else (a,b,c)
        dirty,clean,accrued,pv,tau,cash,remaining=bond_values(*params,age,maturity,coupon)
        down=(pv*np.exp(1e-4*tau)).sum(1);up=(pv*np.exp(-1e-4*tau)).sum(1)
        dv01=(down-up)/2*1000 # currency / bp for 100,000 face
        convexity=(down+up-2*dirty)/(dirty*1e-8)
        ytm=ytm_from_dirty(dirty,tau,cash,remaining)
        half=np.maximum(.0005,.000065*dv01*tr.vol_multiplier.to_numpy()/np.sqrt(tr.depth_multiplier.to_numpy()))
        row=pd.DataFrame(dict(decision_time=idx,instrument=name,maturity_years_remaining=maturity-age,coupon=coupon,
            dirty=dirty,clean=clean,accrued=accrued,bid_clean=clean-half,ask_clean=clean+half,
            yield_bp=ytm*1e4,dv01_per_100k=dv01,convexity=convexity))
        if group=='benchmark':
            bench_y[name]=ytm*1e4;bench_risk[name]=dv01
            nodes=np.array([0.,2.,5.,10.,40.])
            for j,tenor in enumerate([2,5,10]):
                vals=[1,1,0,0,0] if j==0 else ([0,0,1,0,0] if j==1 else [0,0,0,1,1])
                loading=np.interp(tau,nodes,vals)
                row[f'krd{tenor}_per_100k']=((pv*np.exp(1e-4*tau*loading)).sum(1)-(pv*np.exp(-1e-4*tau*loading)).sum(1))/2*1000
        cashrows.append(row)
        cf=None
        if group in ('CGB','CGF','CGZ','US10'):
            repo_i=repo-(.0003 if name.endswith('A') else 0.)
            if group=='US10':repo_i=zero_curve(au,bu,cu,np.array([1/365]))[:,0]
            forward,cf,aid,income=carry_future(dirty,repo_i,age,maturity,coupon,delivery)
            fut_down=carry_future(down,repo_i,age,maturity,coupon,delivery)[0]
            fut_up=carry_future(up,repo_i,age,maturity,coupon,delivery)[0]
            future_candidates.setdefault(group,[]).append(dict(name=name,forward=forward,down=fut_down,up=fut_up,
                dirty=dirty,cf=cf,repo=repo_i,income=income,aid=aid))
        specs.append(dict(instrument=name,initial_maturity_years=maturity,coupon=coupon,group=group,conversion_factor=cf,delivery_year_fraction=delivery))
    futures=[];new_quotes=data['quotes'].copy()
    tpos={t:i for i,t in enumerate(idx)}
    # Each event is at grid minus one second except the first session message.
    grid_by_event={((t if tr.loc[t,'minute']==0 else t-pd.Timedelta(seconds=1))):i for i,t in enumerate(idx)}
    for group,candidates in future_candidates.items():
        values=np.array([z['forward'] for z in candidates]);chosen=values.argmin(0)
        fair=values[chosen,np.arange(n)];down=np.array([z['down'] for z in candidates]).min(0);up=np.array([z['up'] for z in candidates]).min(0)
        dv01=(down-up)/2*1000
        names=np.array([z['name'] for z in candidates])[chosen]
        tick=.005 if group=='CGZ' else (1/64 if group=='US10' else .01)
        width=tr.spread_ticks.to_numpy() if group=='CGB' else np.ones(n)
        bid=np.floor((fair-width*tick/2)/tick+1e-9)*tick;ask=bid+width*tick
        futures.append(pd.DataFrame(dict(decision_time=idx,instrument=group,fair=fair,bid=bid,ask=ask,mid=(bid+ask)/2,
            ctd=names,dv01=dv01,delivery_years=delivery-age)))
        for j,z in enumerate(candidates):
            curves[f'{z["name"]}_delivery_cost']=z['forward']
        mask=new_quotes.instrument.eq(group)
        positions=np.array([grid_by_event[t] for t in new_quotes.loc[mask,'event_time']])
        new_quotes.loc[mask,'bid']=bid[positions];new_quotes.loc[mask,'ask']=ask[positions]
        if group=='CGB':
            tr['driver_price_coordinate']=tr.cgb_mid
            tr['cgb_mid']=(bid+ask)/2;tr['cgb_bid']=bid;tr['cgb_ask']=ask;tr['futures_dv01']=dv01;tr['ctd']=names
            tp=np.array([grid_by_event[t] for t in data['trades'].event_time]);data['trades']['price']=np.where(data['trades'].aggressor==1,ask[tp],bid[tp])
    full_rates=[];cashflow_rates=[]
    ann_t=np.arange(1,6);ois_z=zero_curve(ao,bo,co,ann_t);ois_d=np.exp(-ois_z*ann_t)
    par=(1-ois_d)/np.cumsum(ois_d,axis=1)*1e4
    fw1=(ois_d[:,0]/ois_d[:,1]-1)*1e4;fw2=(ois_d[:,1]/ois_d[:,2]-1)*1e4
    for k,t in enumerate(idx):
        if int(tr.iloc[k].minute)%2:continue
        event=t if tr.iloc[k].minute==0 else t-pd.Timedelta(seconds=1)
        arrival=t if tr.iloc[k].minute==0 else t-pd.Timedelta(milliseconds=650)
        common=dict(event_time=event,available_at=arrival)
        for mat in (2,5,10):full_rates.append(dict(instrument=f'CAD{mat}Y',rate_bp=bench_y[f'CAD{mat}'][k],**common))
        for j in range(5):
            for prefix in ('OIS','SWAP'):
                row=dict(instrument=f'{prefix}{j+1}Y',rate_bp=par[k,j],**common)
                cashflow_rates.append(row)
                if tr.iloc[k].day_number>=tr.day_number.max()-3:full_rates.append(row)
        for name,value in [('FWD1Y1Y',fw1[k]),('FWD2Y1Y',fw2[k])]:
            row=dict(instrument=name,rate_bp=value,**common);cashflow_rates.append(row)
            if tr.iloc[k].day_number>=tr.day_number.max()-3:full_rates.append(row)
    # These theoretical rates are hidden audit output; the model sees only the
    # selected observed records, including the deliberately short swap history.
    # Context shares macro drivers but the sign of stock/rate co-movement changes
    # with a declared growth versus inflation interpretation. It is not selected
    # as an alpha feature in this experiment.
    us10=zero_curve(au,bu,cu,np.array([10.]))[:,0]
    dy=np.r_[0.,np.diff(us10)]
    equity_r=np.where(tr.macro_theme.eq('growth'),4.,-4.)*dy+8e-5*tr.equity_noise.to_numpy()
    spx=5000*np.exp(np.cumsum(equity_r))
    vix=18*np.exp(.35*np.log(tr.vol_multiplier.to_numpy())-25*equity_r)
    contexts=[]
    for name,values in [('SPX',spx),('VIX',vix)]:
        times=pd.Series(idx)-pd.to_timedelta(np.where(tr.minute.to_numpy()==0,0,1),unit='s')
        contexts.append(pd.DataFrame(dict(instrument=name,event_time=times,available_at=times+pd.to_timedelta(np.where(tr.minute.to_numpy()==0,0,.35),unit='s'),value=values)))
    data.update(quotes=new_quotes,rates=pd.DataFrame(full_rates),truth=tr,context=pd.concat(contexts,ignore_index=True),
        curve_truth=pd.DataFrame(dict(time=idx,discount1=ois_d[:,0],discount2=ois_d[:,1],discount3=ois_d[:,2],
            fwd1y1y_bp=fw1,fwd2y1y_bp=fw2)),curves=curves,cash_bonds=pd.concat(cashrows,ignore_index=True),
        futures_valuation=pd.concat(futures,ignore_index=True),bond_specs=pd.DataFrame(specs),theoretical_rates=pd.DataFrame(cashflow_rates))
    return data
