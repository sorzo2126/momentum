"""Independent SPY bar experiment; imports the existing numerical model primitives.

No fabricated quotes, signed flow, executions, or CGB-trained coefficients.
All vendor rows and origin-level results are kept in the ignored private folder.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse
import hashlib
import json
import pickle
import sys
import time
import numpy as np
import pandas as pd
import exchange_calendars as xc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO/'src'))
from momentum.scenarios import (fit_head, predict_head, transition_distribution, _scale_fit,
    _state_weight, _mixture_weights, path_experts, _forecast_summary)
from momentum.model import _session_weights
from momentum.states import ScenarioConfig, STATE_NAMES
from localevents import observe_events

STEP = pd.Timedelta(minutes=5)
CENT = .01
PRICE_FEATURES = ['sigma_ticks','mom_z_5','mom_z_15','mom_z_30','mom_z_60',
    'efficiency_30','range_position_30','vol_ratio_15_60','return_skew_60','down_semivol_ratio_60']
GROUPS = {**dict.fromkeys(PRICE_FEATURES,'price'),
    **dict.fromkeys(['state_age_minutes']+[f'state_{i}' for i in range(5)],'state'),
    **dict.fromkeys(['minutes_from_open','minutes_remaining'],'clock'),
    'volume_ratio_log':'volume','vwap_proxy_distance_z':'bar_vwap'}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False, default=str)+'\n',encoding='utf-8')


def load_bars(path, protocol):
    raw = pd.DataFrame(json.loads(Path(path).read_text(encoding='utf-8')))
    raw['bar_start'] = pd.to_datetime(raw.timestamp, unit='s', utc=True)
    if raw.bar_start.duplicated().any():
        raise ValueError('Ambiguous duplicate bar timestamps; resolve before modelling.')
    raw = raw.set_index('bar_start').sort_index()
    calendar = xc.get_calendar('XNYS')
    schedule = calendar.schedule.loc[protocol['from_utc'][:10]:
        (pd.Timestamp(protocol['to_utc_exclusive'])-pd.Timedelta(days=1)).strftime('%Y-%m-%d')]
    groups, audits = [], []
    for day, session in schedule.iterrows():
        grid = pd.date_range(session.open, session.close, freq=STEP, inclusive='left')
        bars = raw.reindex(grid).copy()
        numeric = bars[['open','high','low','close','volume']]
        missing_bars = int((~grid.isin(raw.index)).sum())
        missing_ohlc = int((~np.isfinite(bars[['open','high','low','close']]).all(axis=1)).sum())
        invalid_volume = int((~np.isfinite(bars.volume) | bars.volume.le(0)).sum())
        invalid_ohlc = int((np.isfinite(bars[['open','high','low','close']]).all(axis=1) &
            (bars[['open','high','low','close']].le(0).any(axis=1) |
             bars.high.lt(bars[['open','close','low']].max(axis=1)) |
             bars.low.gt(bars[['open','close','high']].min(axis=1)))).sum())
        valid = np.isfinite(numeric).all(axis=1) & numeric.gt(0).all(axis=1)
        valid &= bars.high.ge(bars[['open','close','low']].max(axis=1))
        valid &= bars.low.le(bars[['open','close','high']].min(axis=1))
        record = dict(session=str(day.date()), expected_bars=len(grid), valid_bars=int(valid.sum()),
            retained=bool(valid.all()), open=session.open.isoformat(), close=session.close.isoformat(),
            missing_expected_bars=missing_bars,nonfinite_ohlc_bars=missing_ohlc,
            invalid_volume_bars=invalid_volume,inconsistent_or_nonpositive_ohlc_bars=invalid_ohlc)
        audits.append(record)
        if not valid.all():
            continue
        bars['bar_start'] = grid
        bars.index = grid+STEP
        bars.index.name = 'decision_time'
        bars['session_id'] = str(day.date())
        bars['session_open'] = session.open
        bars['session_close'] = session.close
        groups.append(bars)
    if not groups:
        raise ValueError('No complete regular sessions.')
    return pd.concat(groups), pd.DataFrame(audits), len(raw)


def make_features(bars):
    outputs = []
    for session, g in bars.groupby('session_id', sort=False):
        f = pd.DataFrame(index=g.index)
        returns = g.close.diff()/CENT
        returns.iloc[0] = (g.close.iloc[0]-g.open.iloc[0])/CENT
        f['sigma_ticks'] = returns.rolling(12, min_periods=12).std(ddof=1).shift(1).clip(lower=.25)
        for minutes in (5,15,30,60):
            n = minutes//5
            net = returns.rolling(n, min_periods=n).sum()
            path = returns.abs().rolling(n, min_periods=n).sum()
            f[f'mom_ticks_{minutes}'] = net
            f[f'mom_z_{minutes}'] = net/(f.sigma_ticks*np.sqrt(n))
            f[f'efficiency_{minutes}'] = (net.abs()/path.where(path>0)).where(path.ne(0),0.)
        low = g.close.rolling(7, min_periods=7).min()
        high = g.close.rolling(7, min_periods=7).max()
        f['range_position_30'] = ((g.close-low)/(high-low).where(high>low)).where(high.ne(low),.5)
        f['vol_ratio_15_60'] = returns.rolling(3).std()/returns.rolling(12).std().clip(lower=.25)
        f['return_skew_60'] = returns.rolling(12).skew()
        energy = returns.pow(2).rolling(12).sum()
        down = returns.clip(upper=0).pow(2).rolling(12).sum()
        f['down_semivol_ratio_60'] = (down/energy.where(energy>0)).where(energy.ne(0),.5)
        f['vwap_proxy'] = (((g.high+g.low+g.close)/3)*g.volume).cumsum()/g.volume.cumsum()
        f['vwap_proxy_distance_z'] = (g.close-f.vwap_proxy)/CENT/f.sigma_ticks
        f['volume_ratio_log'] = np.log(g.volume/g.volume.rolling(12).mean().shift(1))
        f['minutes_from_open'] = (g.index-g.session_open.iloc[0]).total_seconds()/60
        f['minutes_remaining'] = (g.session_close.iloc[0]-g.index).total_seconds()/60
        valid = np.isfinite(f[PRICE_FEATURES+['vwap_proxy_distance_z','volume_ratio_log']]).all(axis=1)
        state, age, ids, ages = -1, 0, [], []
        for t, row in f.iterrows():
            if not valid.loc[t]:
                state, age = -1, 0
            else:
                direction = int(np.sign(row.mom_z_30)) if abs(row.mom_z_30)>=.75 else 0
                weakening = direction*(row.mom_ticks_5/5)<.5*direction*(row.mom_ticks_30/30)
                new = 0 if not direction else (1 if direction>0 else 3)+int(weakening)
                age = age+5 if state==new else 5
                state = new
            ids.append(state); ages.append(age)
        f['state_id'], f['state_age_minutes'], f['valid'] = ids, ages, valid
        for j in range(5):
            f[f'state_{j}'] = f.state_id.eq(j).astype(float).where(valid)
        f['session_id'] = session
        outputs.append(f)
    return pd.concat(outputs).replace([np.inf,-np.inf], np.nan)


def make_targets(bars, features, horizon):
    n = horizon//5
    out = pd.DataFrame(index=bars.index)
    records = []
    for session, g in bars.groupby('session_id', sort=False):
        for i in range(len(g)-n):
            t = g.index[i]
            if not features.loc[t,'valid'] or not features.loc[g.index[i+n],'valid']:
                continue
            sigma = features.loc[t,'sigma_ticks']
            future = g.iloc[i+1:i+n+1]
            ret = (g.close.iloc[i+n]-g.close.iloc[i])/CENT
            band = .35*sigma*np.sqrt(n)
            records.append(dict(decision_time=t, target_end=g.index[i+n],
                session_id=session, return_ticks=ret, neutral_band_ticks=band,
                class_id=0 if ret < -band else 2 if ret > band else 1,
                future_state=int(features.loc[g.index[i+n],'state_id']),
                mae_long_ticks=max(0,(g.close.iloc[i]-future.low.min())/CENT),
                mae_short_ticks=max(0,(future.high.max()-g.close.iloc[i])/CENT)))
    return pd.DataFrame(records).set_index('decision_time').sort_index()


def build_bank(bars, f, y, train, scfg):
    x = f[list(GROUPS)]
    center, scale = _scale_fit(x.loc[train])
    weights = _session_weights(y.loc[train,'session_id'])
    sigma = f.loc[train,'sigma_ticks'].to_numpy()
    n = int((y.loc[train[0],'target_end']-train[0])/STEP)
    positions = bars.index.get_indexer(train)
    close = bars.close.to_numpy()
    paths = np.array([(close[i:i+n+1]-close[i])/CENT/s for i,s in zip(positions,sigma)])
    return dict(classes=y.loc[train,'class_id'].to_numpy(int),
        paths=paths,
        future_states=y.loc[train,'future_state'].to_numpy(int),
        current_states=f.loc[train,'state_id'].to_numpy(int),
        center=center, scale=scale, standardized_x=(x.loc[train].to_numpy()-center)/scale,
        session_weights=weights, groups=list(GROUPS.values()), feature_columns=list(GROUPS),
        neighbor_count=scfg.neighbor_count, kernel_floor=scfg.kernel_floor,
        endpoint=y.loc[train,'return_ticks'].to_numpy()/sigma,
        mae_long=y.loc[train,'mae_long_ticks'].to_numpy()/sigma,
        mae_short=y.loc[train,'mae_short_ticks'].to_numpy()/sigma,
        train_times=[t.isoformat() for t in train])


def session_scores(prob, y):
    p = np.asarray(prob)
    if not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(1),1):
        raise ValueError('Invalid forecast probabilities.')
    truth = y.class_id.to_numpy(int)
    losses = pd.DataFrame(dict(session=y.session_id.to_numpy(),
        log_loss=-np.log(np.maximum(p[np.arange(len(p)),truth],1e-12)),
        brier=((p-np.eye(3)[truth])**2).sum(1), accuracy=(p.argmax(1)==truth).astype(float)),index=y.index)
    daily = losses.groupby('session').mean()
    return {k:float(v) for k,v in daily.mean().items()}, daily, losses


def block_ci(difference, seed=1729):
    values=np.asarray(difference); n=len(values); rng=np.random.default_rng(seed)
    samples=[]; length=min(5,n)
    for _ in range(2000):
        starts=rng.integers(0,n,size=int(np.ceil(n/length)))
        ids=np.concatenate([(s+np.arange(length))%n for s in starts])[:n]
        samples.append(values[ids].mean())
    low,high=np.quantile(samples,[.025,.975])
    return dict(mean=float(values.mean()),low=float(low),high=float(high),sessions=n)


def causal_audit(bars, f):
    checks={}
    day=bars.session_id.unique()[5]
    g=bars[bars.session_id.eq(day)]
    t=g.index[36]
    prefix=make_features(bars.loc[:t])
    cols=[c for c in f.columns if c!='session_id']
    pd.testing.assert_frame_equal(prefix[cols],f.loc[prefix.index,cols],check_freq=False)
    poisoned=bars.copy()
    poisoned.loc[poisoned.index>t,['open','high','low','close']]*=3
    poisoned.loc[poisoned.index>t,'volume']*=10
    changed=make_features(poisoned)
    pd.testing.assert_frame_equal(changed.loc[:t,cols],f.loc[:t,cols],check_freq=False)
    checks['prefix_invariance']=True;checks['future_feature_poisoning']=True
    y=make_targets(bars,f,60)
    origin=y.index[0]; loc=bars.index.get_loc(origin)
    future=bars.iloc[loc+1:loc+13]
    assert np.isclose(y.loc[origin,'mae_long_ticks'],max(0,(bars.loc[origin,'close']-future.low.min())/CENT))
    altered=bars.copy();altered.loc[origin,'low']=.1
    y2=make_targets(altered,f,60)
    assert np.isclose(y2.loc[origin,'mae_long_ticks'],y.loc[origin,'mae_long_ticks'])
    checks['future_bar_extrema_only']=True
    checks['bar_end_is_start_plus_5m']=bool(((bars.index-bars.bar_start)==STEP).all())
    checks['no_missing_prices_or_volume']=bool(np.isfinite(bars[['open','high','low','close','volume']]).all().all())
    checks['no_synthetic_quotes_or_flow']=True
    return checks


def chart_payload(bars,f,predictions,session,protocol):
    g=bars[bars.session_id.eq(session)];opening=g.iloc[:6]
    ms=lambda t:int(pd.Timestamp(t).value//1_000_000)
    fin=lambda v:float(v) if pd.notna(v) and np.isfinite(v) else None
    range_=dict(high=float(opening.high.max()),low=float(opening.low.min()),
        known_at=g.index[5].isoformat(),known_at_time=ms(g.index[5]),
        known_local_time='10:00',window_start_local='09:30',window_end_local='10:00')
    records=[]
    for t,r in g.iterrows():
        x=f.loc[t]; state=int(x.state_id)
        records.append(dict(time=ms(t),as_of=t.isoformat(),start_time=ms(r.bar_start),
            local_time=t.tz_convert('America/New_York').strftime('%H:%M'),
            **{k:float(r[k]) for k in ['open','high','low','close','volume']},
            vwap=fin(x.vwap_proxy),flow_pressure=None,flow_available=False,spread_ticks=None,
            mom_ticks_30=fin(x.mom_ticks_30),mom_z_30=fin(x.mom_z_30),sigma_ticks=fin(x.sigma_ticks),
            observed_state=STATE_NAMES[state] if state>=0 else 'warming_up',
            state_age_minutes=float(x.state_age_minutes),complete=True,
            opening_range_high=range_['high'] if t>=g.index[5] else None,
            opening_range_low=range_['low'] if t>=g.index[5] else None))
    forecasts=[]
    subset=predictions[predictions.session_id.eq(session)]
    keys=['p_down','p_neutral','p_up','indicator','endpoint_mean_ticks','endpoint_q10_ticks',
        'endpoint_q90_ticks','mae_long_q80_ticks','mae_short_q80_ticks','neutral_band_ticks']
    for r in subset.to_dict('records'):
        t=pd.Timestamp(r['decision_time']);end=pd.Timestamp(r['target_end'])
        forecasts.append(dict(time=ms(t),as_of=t.isoformat(),target_time=ms(end),target_at=end.isoformat(),
            horizon_minutes=int(r['horizon_minutes']),origin_midpoint=float(g.loc[t,'close']),
            observed_state=r['observed_state'],source='SPY_TRAIN_CAL_frozen',
            **{k:fin(r[k]) for k in keys}))
    return dict(meta=dict(schema_version='spy-real-bars-v1',session=session,instrument='SPY',
        contract='SPY.US',timezone='America/New_York',tick_size=CENT,currency='USD',
        synthetic=False,bar_minutes=5,default_cutoff_index=29,
        session_open=g.session_open.iloc[0].isoformat(),session_close=g.session_close.iloc[0].isoformat(),
        horizons_minutes=protocol['horizons_minutes'],price_basis='Vendor OHLC bars; decision clock is completed bar end.',
        vwap_definition='Cumulative volume-weighted bar typical price (H+L+C)/3; not tape VWAP.',
        flow_definition='Unavailable: EODHD OHLCV does not provide aggressor-classified trades.'),
        bars=records,forecasts=forecasts,events=observe_events(records,range_),opening_range=range_)


def run(raw_path):
    started=time.perf_counter();private=HERE/'private';private.mkdir(exist_ok=True)
    protocol=json.loads((HERE/'protocol.json').read_text())
    protocol_hash=digest(HERE/'protocol.json')
    runner_hash=digest(__file__)
    bars,quality,raw_count=load_bars(raw_path,protocol)
    days=list(bars.session_id.unique()); n=len(days)
    nt,nc=int(n*.6),int(n*.2)
    if min(nt,nc,n-nt-nc)<20:raise ValueError('Too few complete sessions for this protocol.')
    split={'train':days[:nt],'cal':days[nt:nt+nc],'test':days[nt+nc:]}
    # Persist the split and protocol identity before any outcome-based fitting or scoring.
    write_json(HERE/'split.json',dict(protocol_sha256=protocol_hash,sessions=split))
    quality.to_csv(HERE/'session-quality.csv',index=False)
    print(json.dumps(dict(stage='quality_and_split',raw_rows=raw_count,retained_sessions=n,
        excluded_sessions=int((~quality.retained).sum()),split={k:len(v) for k,v in split.items()})),flush=True)
    f=make_features(bars);checks=causal_audit(bars,f)
    x=f[list(GROUPS)];scfg=ScenarioConfig(**protocol['hyperparameters']);cfg=SimpleNamespace(xgb_device='cpu')
    metrics=[];predictions=[];daily_scores=[];comparisons=[];fits={};risk=[];case_rows=[]
    for h in protocol['horizons_minutes']:
        y=make_targets(bars,f,h)
        parts={part:y.index[y.session_id.isin(sessions)] for part,sessions in split.items()}
        tr,ca,te=[parts[p] for p in ('train','cal','test')]
        assert len(tr)>30 and len(ca)>30 and len(te)>30
        assert y.loc[tr,'target_end'].max()<ca.min() and y.loc[ca,'target_end'].max()<te.min()
        assert (y.target_end<=bars.loc[y.index,'session_close']).all()
        assert set(y.loc[tr,'class_id'])=={0,1,2}
        bank=build_bank(bars,f,y,tr,scfg);wt=bank['session_weights'];wc=_session_weights(y.loc[ca,'session_id'])
        transition=transition_distribution(bank['current_states'],bank['future_states'],wt,scfg.transition_prior_count)
        state_head=fit_head(x.loc[tr],bank['future_states'],wt,scfg,cfg)
        price_head=fit_head(x.loc[tr],bank['classes'],wt,scfg,cfg)
        both=ca.append(te)
        state_ml=predict_head(state_head,x.loc[both],5);price_ml=predict_head(price_head,x.loc[both],3)
        state_prior=transition[f.loc[both,'state_id'].to_numpy(int)]
        alpha=_state_weight(state_ml[:len(ca)],state_prior[:len(ca)],y.loc[ca,'future_state'].to_numpy(int),wc)
        sp=alpha*state_ml+(1-alpha)*state_prior
        pcal=[]
        for i,t in enumerate(ca):pcal.append(path_experts(bank,x.loc[t],sp[i],price_ml[i])[1])
        mixture=_mixture_weights(np.asarray(pcal),y.loc[ca,'class_id'].to_numpy(int),wc)
        entry=dict(bank=bank,mixture_weights=mixture)
        rows=[];individual={k:[] for k in ('local','structural','supervised')}
        for i,t in enumerate(te,start=len(ca)):
            experts,endpoints,diag=path_experts(bank,x.loc[t],sp[i],price_ml[i])
            row=_forecast_summary(entry,experts,sp[i],float(f.loc[t,'sigma_ticks']),diag)
            row.update(decision_time=t,horizon_minutes=h,session_id=bars.loc[t,'session_id'],
                target_end=y.loc[t,'target_end'],neutral_band_ticks=y.loc[t,'neutral_band_ticks'],
                observed_state=STATE_NAMES[int(f.loc[t,'state_id'])],actual_class=int(y.loc[t,'class_id']),
                actual_return_ticks=float(y.loc[t,'return_ticks']))
            rows.append(row)
            for j,name in enumerate(individual):individual[name].append(endpoints[j])
        pred=pd.DataFrame(rows).set_index('decision_time');predictions.extend(rows)
        prior=np.bincount(bank['classes'],weights=wt,minlength=3);prior/=prior.sum()
        candidates={'mixture':pred[['p_down','p_neutral','p_up']].to_numpy(),
            'train_frequency':np.tile(prior,(len(te),1)),'direct_full':price_ml[len(ca):],
            **{k:np.asarray(v) for k,v in individual.items()}}
        baseline_models={}
        for name,columns in [('momentum_only',['mom_z_30']),('clock_only',['minutes_from_open','minutes_remaining']),('price_only',PRICE_FEATURES)]:
            head=fit_head(x.loc[tr,columns],bank['classes'],wt,scfg,cfg)
            candidates[name]=predict_head(head,x.loc[te,columns],3)
            baseline_models[name]=dict(head=head,columns=columns)
        dailies={}
        for name,prob in candidates.items():
            score,daily,losses=session_scores(prob,y.loc[te]);dailies[name]=daily
            metrics.append(dict(horizon_minutes=h,model=name,rows=len(te),sessions=len(daily),**score))
            frame=daily.reset_index();frame['horizon_minutes']=h;frame['model']=name;daily_scores.extend(frame.to_dict('records'))
        for name in ('train_frequency','momentum_only','clock_only','price_only','direct_full'):
            comparisons.append(dict(horizon_minutes=h,baseline=name,
                difference='mixture minus baseline log loss; negative favours mixture',
                **block_ci(dailies['mixture'].log_loss-dailies[name].log_loss)))
        actual=y.loc[te];w=_session_weights(actual.session_id)
        row=dict(horizon_minutes=h,rows=len(te),endpoint_mae_cents=float(np.average(abs(pred.endpoint_mean_ticks-actual.return_ticks),weights=w)),
            endpoint_80_interval_coverage=float(np.average(actual.return_ticks.between(pred.endpoint_q10_ticks,pred.endpoint_q90_ticks),weights=w)))
        for side in ('long','short'):
            row[side+'_adverse_q80_coverage']=float(np.average(actual[f'mae_{side}_ticks']<=pred[f'mae_{side}_q80_ticks'],weights=w))
        risk.append(row)
        observed=f.loc[te,'state_id'].to_numpy(int);directions=np.where(observed==0,0,np.where(observed<3,1,-1))
        p=candidates['mixture'];cls=actual.class_id.to_numpy(int)
        for label,direction in [('up_observed',1),('down_observed',-1),('balanced',0)]:
            mask=directions==direction
            if not mask.any():continue
            # Description only; thresholds and the sample are not selected on these results.
            cc=2 if direction==1 else 0;op=0 if direction==1 else 2
            case_rows.append(dict(horizon_minutes=h,observed=label,rows=int(mask.sum()),
                mean_up_probability=float(p[mask,2].mean()),mean_down_probability=float(p[mask,0].mean()),
                realised_up_rate=float((cls[mask]==2).mean()),realised_down_rate=float((cls[mask]==0).mean()),
                continuation_probability=None if direction==0 else float(p[mask,cc].mean()),
                realised_continuation=None if direction==0 else float((cls[mask]==cc).mean())))
        fits[h]=dict(entry=entry,state_head=state_head,price_head=price_head,transition=transition,
            state_ml_weight=alpha,baseline_models=baseline_models,fit_last_origin=tr.max().isoformat(),
            available_after=bars[bars.session_id.isin(split['cal'])].index.max().isoformat(),
            feature_columns=list(GROUPS),eligible_sessions={k:int(y.loc[v,'session_id'].nunique()) for k,v in parts.items()})
        print(json.dumps(dict(stage='horizon_complete',horizon=h,train_rows=len(tr),cal_rows=len(ca),test_rows=len(te),
            weights=mixture.tolist(),state_ml_weight=alpha)),flush=True)
    pred=pd.DataFrame(predictions)
    pred.to_csv(private/'predictions.csv.gz',index=False)
    bars.to_csv(private/'clean-bars.csv.gz')
    f.to_csv(private/'features.csv.gz')
    with (private/'frozen-model.pkl').open('wb') as stream:pickle.dump(fits,stream)
    pd.DataFrame(metrics).to_csv(HERE/'metrics.csv',index=False)
    pd.DataFrame(daily_scores).to_csv(private/'session-scores.csv',index=False)
    pd.DataFrame(comparisons).to_csv(HERE/'comparisons.csv',index=False)
    pd.DataFrame(risk).to_csv(HERE/'risk-metrics.csv',index=False)
    pd.DataFrame(case_rows).to_csv(HERE/'observed-direction-breakdown.csv',index=False)
    fit_metadata={str(h):dict(mixture_weights=m['entry']['mixture_weights'].tolist(),state_ml_weight=m['state_ml_weight'],
        fit_last_origin=m['fit_last_origin'],available_after=m['available_after'],eligible_sessions=m['eligible_sessions']) for h,m in fits.items()}
    write_json(HERE/'fit-metadata.json',fit_metadata)
    chart=chart_payload(bars,f,pred,split['test'][0],protocol)
    write_json(private/'chart-data.json',chart)
    checks.update(chronological_train_cal_test=True,targets_end_inside_session_and_split=True,
        original_CGB_weights_not_loaded=True,all_three_classes_supported=True,probabilities_sum_to_one=True,
        raw_bar_count=raw_count,retained_sessions=len(days),retained_bars=len(bars),
        quality_excluded_sessions=int((~quality.retained).sum()),source_sha256=digest(raw_path),
        protocol_sha256=protocol_hash,runner_sha256=runner_hash,
        local_event_observer_sha256=digest(HERE/'localevents.py'),
        reused_source_sha256={name:digest(REPO/'src/momentum'/name) for name in ['scenarios.py','states.py','model.py']},
        ui_session=split['test'][0],elapsed_seconds=round(time.perf_counter()-started,2))
    write_json(HERE/'verification.json',dict(status='PASS',checks=checks))
    plots(pd.DataFrame(metrics),pd.DataFrame(daily_scores),pred,comparisons)
    print(json.dumps(dict(stage='done',seconds=checks['elapsed_seconds'],test_rows=len(pred),ui_session=split['test'][0])),flush=True)


def plots(metrics,daily,pred,comparisons):
    output=HERE/'figures';output.mkdir(exist_ok=True)
    plt.rcParams.update({'figure.dpi':150,'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    names=['train_frequency','momentum_only','clock_only','price_only','direct_full','mixture']
    fig,axs=plt.subplots(1,3,figsize=(14,4),sharey=True)
    for ax,h in zip(axs,[60,120,240]):
        m=metrics[metrics.horizon_minutes.eq(h)].set_index('model').loc[names]
        ax.barh(names[::-1],m.log_loss.iloc[::-1],color=['#2476b4' if n=='mixture' else '#9ca8b3' for n in names[::-1]])
        ax.set_title(str(h)+' min · lower is better');ax.set_xlabel('Session-balanced log loss')
    fig.suptitle('SPY held-out prediction quality');fig.tight_layout();fig.savefig(output/'heldout-scores.png');plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4))
    for name in ['mixture','train_frequency','price_only']:
        d=daily[daily.horizon_minutes.eq(60)&daily.model.eq(name)].sort_values('session')
        ax.plot(pd.to_datetime(d.session),d.log_loss.rolling(5,min_periods=1).mean(),label=name)
    ax.set_ylabel('5-session mean log loss');ax.set_title('One-hour forecasts across the untouched TEST period');ax.legend();fig.autofmt_xdate();fig.tight_layout();fig.savefig(output/'test-loss-through-time.png');plt.close(fig)
    fig,axs=plt.subplots(1,3,figsize=(12,3.8))
    p=pred[pred.horizon_minutes.eq(60)]
    for ax,name,cls in zip(axs,['down','neutral','up'],range(3)):
        prob=p['p_'+name];tab=pd.DataFrame({'prob':prob,'actual':p.actual_class.eq(cls).astype(float),'bin':pd.cut(prob,np.linspace(0,1,11),include_lowest=True)})
        groups=tab.groupby('bin',observed=True).agg(prob=('prob','mean'),actual=('actual','mean'),n=('actual','size'))
        groups=groups[groups.n>=20]
        ax.plot([0,1],[0,1],color='#9ca8b3',linestyle='--');ax.scatter(groups.prob,groups.actual,s=groups.n/10,color='#2476b4')
        ax.set(xlim=(0,1),ylim=(0,1),title=name.capitalize(),xlabel='Forecast probability',ylabel='Observed frequency')
    fig.suptitle('One-hour reliability · descriptive origin bins, at least20 origins');fig.tight_layout();fig.savefig(output/'reliability.png');plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw',type=Path,default=HERE/'private/raw/SPY.US-5m.json')
    args=parser.parse_args();run(args.raw)
