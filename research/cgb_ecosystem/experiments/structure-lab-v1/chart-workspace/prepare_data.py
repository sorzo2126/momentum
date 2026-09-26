"""Causal chart replay adapter for one existing synthetic S0 session.

This reads frozen artifacts and writes chart-data.json/data-verification.json only.
It does not retrain, generate observations, or send orders.
"""
from pathlib import Path
import hashlib, json, sys
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
STUDY=HERE.parents[2]
sys.path.insert(0,str(STUDY/'model_snapshot'))
from momentum.features import _quote_snapshot

SESSION='2025-02-19'; RUN='base-1729'; TICK=.01
OPEN=pd.Timestamp(SESSION+' 13:00:00',tz='UTC')
CLOSE=pd.Timestamp(SESSION+' 21:00:00',tz='UTC')
FORECAST_FIELDS=('p_down','p_neutral','p_up','indicator','endpoint_mean_ticks',
    'endpoint_q10_ticks','endpoint_q90_ticks','mae_long_q80_ticks','mae_short_q80_ticks',
    'effective_scenarios','predictive_entropy','expert_disagreement','nearest_distance',
    'observed_feature_fraction','unsupported_future_state_mass','neutral_band_ticks')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def ms(t):return int(pd.Timestamp(t).value//1_000_000)
def iso(t):return pd.Timestamp(t).isoformat()
def finite(v):return float(v) if pd.notna(v) and np.isfinite(v) else None
def state_name(v):
    names=('balanced','up-responsive','up-weakening','down-responsive','down-weakening')
    return names[int(v)] if pd.notna(v) and 0<=int(v)<5 else 'warming_up'

def load_inputs():
    source=STUDY/'results'/RUN; result={}; hashes={}
    for name,file in [('quotes','inputs/quotes.csv.gz'),('features','features.csv.gz'),
                      ('observations','observations.csv.gz'),('forecasts','predictions-and-outcomes.csv.gz')]:
        path=source/file;hashes[str(path.relative_to(STUDY))]=sha(path)
        frame=pd.read_csv(path)
        for clock in ('event_time','available_at','decision_time','target_end'):
            if clock in frame:frame[clock]=pd.to_datetime(frame[clock],utc=True,format='mixed')
        if name=='quotes':frame=frame[frame.instrument.eq('CGB')&frame.event_time.between(OPEN,CLOSE)]
        else:frame=frame[frame.decision_time.between(OPEN,CLOSE)]
        result[name]=frame.copy()
    source_code=STUDY/'model_snapshot'/'momentum'/'features.py'
    hashes[str(source_code.relative_to(STUDY))]=sha(source_code)
    return result,hashes

def observe_events(bars,opening_range):
    if opening_range is None:return []
    high=opening_range['high'];low=opening_range['low'];known=opening_range['known_at_time']
    side=0;count=0;episode=0;events=[]
    for bar in bars:
        if bar['time']<=known or bar['close'] is None:continue
        price=bar['close'];new=1 if price>high+1e-10 else -1 if price<low-1e-10 else 0
        event=None
        if new==0:
            if side!=0:
                event=dict(type='returned_inside',level='opening_range',level_price=high if side>0 else low,
                    label='Returned inside opening range',previous_side='above' if side>0 else 'below')
            side=0;count=0
        elif new!=side:
            episode+=1;side=new;count=1
            event=dict(type='break_above' if side>0 else 'break_below',
                level='opening_range_high' if side>0 else 'opening_range_low',level_price=high if side>0 else low,
                label='Break above opening range' if side>0 else 'Break below opening range')
        else:
            count+=1
            if count==2:
                event=dict(type='held_above' if side>0 else 'held_below',
                    level='opening_range_high' if side>0 else 'opening_range_low',level_price=high if side>0 else low,
                    label='Held above: two completed closes' if side>0 else 'Held below: two completed closes')
        if event:
            event.update(time=bar['time'],as_of=bar['as_of'],confirmed_at=bar['as_of'],
                price=price,episode_id=episode,level_known_at=opening_range['known_at'],
                consecutive_closes=count,source='causal_opening_range_observer')
            events.append(event)
    return events

def build(inputs,as_of=CLOSE):
    as_of=min(pd.Timestamp(as_of),CLOSE)
    quotes=inputs['quotes'].loc[inputs['quotes'].available_at.le(as_of)].sort_values(['available_at','event_time'],kind='stable')
    features=inputs['features'].loc[inputs['features'].decision_time.le(as_of)].set_index('decision_time')
    observations=inputs['observations'].loc[inputs['observations'].decision_time.le(as_of)].set_index('decision_time')
    forecast_source=inputs['forecasts'].loc[inputs['forecasts'].decision_time.le(as_of)]
    grid=pd.date_range(OPEN,as_of,freq='1min')
    snapshots=_quote_snapshot(quotes,grid,'cgb',30.)
    bars=[];opening_range=None
    for end in pd.date_range(OPEN+pd.Timedelta(minutes=5),as_of,freq='5min'):
        start=end-pd.Timedelta(minutes=5)
        mask=(snapshots.index>=start if start==OPEN else snapshots.index>start)&(snapshots.index<=end)
        block=snapshots.loc[mask];valid=block.cgb_mid.dropna();current=block.iloc[-1]
        f=features.loc[end] if end in features.index else pd.Series(dtype=float)
        o=observations.loc[end] if end in observations.index else pd.Series(dtype=float)
        mid=finite(current.cgb_mid);distance=finite(f.get('vwap_distance_ticks'))
        vwap=mid-distance*TICK if mid is not None and distance is not None else None
        record=dict(time=ms(end),as_of=iso(end),local_time=end.tz_convert('America/New_York').strftime('%H:%M'),
            start_time=ms(start),open=finite(valid.iloc[0]) if len(valid) else None,
            high=finite(valid.max()) if len(valid) else None,low=finite(valid.min()) if len(valid) else None,
            close=mid,vwap=vwap,flow_pressure=finite(o.get('flow_pressure')),
            flow_available=bool(o.get('flow_available',False)),mom_ticks_30=finite(f.get('mom_ticks_30')),
            mom_z_30=finite(f.get('mom_z_30')),sigma_ticks=finite(f.get('sigma_ticks')),
            spread_ticks=finite(f.get('spread_ticks')),observed_state=state_name(o.get('state_id')),
            state_age_minutes=finite(o.get('state_age_minutes')),source_available_at=iso(current.cgb_available_at),
            source_event_time=iso(current.cgb_event_time),valid_snapshots=int(len(valid)),
            expected_snapshots=int(len(block)),complete=bool(block.cgb_valid.all()),
            opening_range_high=None,opening_range_low=None)
        bars.append(record)
        if end==OPEN+pd.Timedelta(minutes=30) and all(b['complete'] for b in bars):
            opening_range=dict(high=max(b['high'] for b in bars),low=min(b['low'] for b in bars),
                known_at=iso(end),known_at_time=ms(end),window_start=iso(OPEN),window_end=iso(end),
                known_local_time=end.tz_convert('America/New_York').strftime('%H:%M'),
                window_start_local='08:00',window_end_local='08:30',
                definition='Received valid one-minute midpoint snapshots from session open through +30m, endpoints included.')
        if opening_range:
            record['opening_range_high']=opening_range['high'];record['opening_range_low']=opening_range['low']
    forecasts=[]
    for row in forecast_source.sort_values(['decision_time','horizon_minutes']).itertuples(index=False):
        origin=row.decision_time;h=int(row.horizon_minutes);target=origin+pd.Timedelta(minutes=h)
        assert target==row.target_end and target<=CLOSE
        assert origin in snapshots.index
        record=dict(time=ms(origin),as_of=iso(origin),horizon_minutes=h,target_time=ms(target),target_at=iso(target),
            origin_midpoint=finite(snapshots.loc[origin,'cgb_mid']),observed_state=row.observed_state,
            flow_available=bool(row.flow_available),source='saved_frozen_model',data_status='synthetic')
        record.update({k:finite(getattr(row,k)) for k in FORECAST_FIELDS})
        forecasts.append(record)
    return dict(meta=dict(schema_version='cgb-chart-replay-v1',session=SESSION,run=RUN,
        instrument='CGB',contract='SIM_CGB',timezone='America/New_York',tick_size=TICK,tick_value_cad=10.,
        synthetic=True,market_calibrated=False,bar_minutes=5,session_open=iso(OPEN),session_close=iso(CLOSE),
        as_of=iso(as_of),horizons_minutes=[60,120,240],
        price_basis='Atomic bid/ask midpoint, selected at each one-minute receiver time; not trade OHLC.',
        bar_definition='First completed bar includes the session-open snapshot; later bars use (previous close,current close].',
        vwap_definition='Observed session tape VWAP reconstructed as received midpoint minus saved vwap_distance_ticks times tick size.',
        flow_definition='(Buy-initiated classified volume minus sell-initiated classified volume) / total aggressor-classified volume across the preceding five receiver-minute bins. Available only when at least 80% of total volume is classified, classified volume is positive, and contributing bins contain no trade delayed more than 30 seconds. Not an institutional position or absorption estimate.',
        event_definition='Opening range known only at +30m; strict close break, held on the second successive close outside; returned_inside requires a completed close inside the range.',
        forecast_definition='Frozen model endpoint-class probabilities with an origin-specific neutral band; three horizons fitted separately; no future realized outcomes included.',
        replay_rule='Display only bars/events/forecasts with time at or before the replay cursor; level only at or after known_at_time.'),
        bars=bars,forecasts=forecasts,events=observe_events(bars,opening_range),opening_range=opening_range)

def prefix(data,cutoff):
    time=ms(cutoff)
    return dict(bars=[v for v in data['bars'] if v['time']<=time],
        forecasts=[v for v in data['forecasts'] if v['time']<=time],events=[v for v in data['events'] if v['time']<=time],
        opening_range=data['opening_range'] if data['opening_range'] and data['opening_range']['known_at_time']<=time else None)

def verify(inputs,full):
    results={}
    # Every OHLC is the exact reduction of the causally selected minute snapshots.
    grid=pd.date_range(OPEN,CLOSE,freq='1min');q=inputs['quotes'].sort_values(['available_at','event_time'],kind='stable')
    snap=_quote_snapshot(q,grid,'cgb',30.)
    for b in full['bars']:
        end=pd.Timestamp(b['as_of']);start=end-pd.Timedelta(minutes=5)
        mask=(snap.index>=start if start==OPEN else snap.index>start)&(snap.index<=end)
        v=snap.loc[mask,'cgb_mid'].dropna()
        assert b['open']==float(v.iloc[0]) and b['high']==float(v.max()) and b['low']==float(v.min()) and b['close']==float(v.iloc[-1])
        assert b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']
        assert pd.Timestamp(b['source_available_at'])<=end and pd.Timestamp(b['source_event_time'])<=end
    results['exact_causal_ohlc']=True
    cutoffs=[OPEN+pd.Timedelta(minutes=n) for n in (20,30,65,150,240,355)]
    for cutoff in cutoffs:
        truncated={k:v.loc[v['available_at' if k=='quotes' else 'decision_time'].le(cutoff)].copy() for k,v in inputs.items()}
        assert prefix(build(truncated,cutoff),cutoff)==prefix(full,cutoff)
        poisoned={k:v.copy(deep=True) for k,v in inputs.items()}
        for name,frame in poisoned.items():
            later=frame['available_at' if name=='quotes' else 'decision_time'].gt(cutoff)
            for col in frame.select_dtypes(include=[np.number]).columns:
                frame.loc[later,col]=999999.
        assert prefix(build(poisoned,cutoff),cutoff)==prefix(full,cutoff)
        # A late-arriving quote with an earlier event time must remain unavailable.
        late=inputs['quotes'].iloc[[0]].copy();late['event_time']=cutoff-pd.Timedelta(minutes=1)
        late['available_at']=cutoff+pd.Timedelta(seconds=1);late['bid']=900000.;late['ask']=900001.
        poisoned['quotes']=pd.concat([poisoned['quotes'],late],ignore_index=True)
        assert prefix(build(poisoned,cutoff),cutoff)==prefix(full,cutoff)
    results['prefix_invariance_cutoffs']=[iso(c) for c in cutoffs]
    results['future_input_poisoning']=True;results['late_arrival_unavailable']=True
    source=inputs['forecasts'].set_index(['decision_time','horizon_minutes'])
    for f in full['forecasts']:
        row=source.loc[(pd.Timestamp(f['as_of']),f['horizon_minutes'])]
        assert all(f[k]==float(row[k]) for k in FORECAST_FIELDS)
        assert abs(sum(f[k] for k in ('p_down','p_neutral','p_up'))-1)<1e-12
        assert not set(f).intersection({'return_ticks','class_id','mae_long_ticks','mae_short_ticks','outcome_available'})
    results['saved_forecast_identity']=True;results['future_outcomes_excluded']=True
    first=min(f['time'] for f in full['forecasts'])
    assert first==ms(OPEN+pd.Timedelta(minutes=65))
    assert all(b['observed_state']=='warming_up' for b in full['bars'] if b['time']<first)
    assert all(b['flow_pressure'] is None for b in full['bars'] if not b['flow_available'])
    assert all(b['opening_range_high'] is None and b['opening_range_low'] is None for b in full['bars'] if b['time']<ms(OPEN+pd.Timedelta(minutes=30)))
    results['warmup_is_unavailable_not_neutral']=True;results['missing_flow_is_null']=True
    assert all(e['time']>full['opening_range']['known_at_time'] for e in full['events'])
    assert all(e['confirmed_at']==e['as_of'] for e in full['events'])
    levels=dict(high=101.,low=99.,known_at=iso(OPEN+pd.Timedelta(minutes=30)),known_at_time=ms(OPEN+pd.Timedelta(minutes=30)))
    synthetic=[]
    for minute,price in [(20,200.),(30,100.),(35,102.),(40,103.),(45,102.),(50,100.),(55,98.),(60,97.),(65,100.)]:
        t=OPEN+pd.Timedelta(minutes=minute);synthetic.append(dict(time=ms(t),as_of=iso(t),close=price))
    events=observe_events(synthetic,levels)
    assert [e['type'] for e in events]==['break_above','held_above','returned_inside','break_below','held_below','returned_inside']
    assert [pd.Timestamp(e['as_of']).minute for e in events]==[35,40,50,55,0,5]
    results['level_known_before_event']=True;results['event_transition_fixture']=True;results['event_spam_suppressed']=True
    return results

def main():
    inputs,hashes=load_inputs();data=build(inputs);checks=verify(inputs,data)
    data['meta']['source_sha256']=hashes
    payload=json.dumps(data,separators=(',',':'),allow_nan=False)
    assert len(payload.encode())<300000
    (HERE/'chart-data.json').write_text(payload+'\n',encoding='utf-8')
    assert all(sha(STUDY/name)==digest for name,digest in hashes.items())
    verification=dict(status='PASS',checks=checks,source_files_unchanged=True,source_sha256=hashes,
        data_sha256=sha(HERE/'chart-data.json'),code_sha256=sha(Path(__file__)),bytes=len(payload.encode())+1,
        bars=len(data['bars']),forecasts=len(data['forecasts']),events=len(data['events']),
        forecast_counts={str(h):sum(f['horizon_minutes']==h for f in data['forecasts']) for h in (60,120,240)})
    (HERE/'data-verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:verification[k] for k in ('status','bytes','bars','forecasts','events','forecast_counts')}))

if __name__=='__main__':main()
