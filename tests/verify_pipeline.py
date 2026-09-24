"""Private deterministic software fixture, never a financial experiment."""
from pathlib import Path
import json, warnings
import numpy as np
import pandas as pd
from pandas.testing import assert_frame_equal

import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from momentum import *
from momentum.features import _known_snapshots
from momentum.model import opinion_pool

cfg = ResearchConfig()
days = pd.bdate_range('2025-01-02', periods=17, tz='UTC')
sessions, quote_parts = [], []
for number, day in enumerate(days):
    start = day + pd.Timedelta(hours=13)
    idx = pd.date_range(start, periods=481, freq='min')
    j = np.arange(len(idx))
    # Analytic exercise path, deliberately not presented as a market dataset.
    sign = (number % 3) - 1
    mid = 110 + sign*.002*j + .04*np.sin(j*2*np.pi/37) + .02*np.cos(j*2*np.pi/17)
    quote_parts.append(pd.DataFrame({'instrument':'CGB','contract':'EXERCISE',
        'event_time':idx-pd.Timedelta(seconds=1),'available_at':idx,
        'bid':mid-.005,'ask':mid+.005,'bid_size':10.,'ask_size':12.}))
    sessions.append({'session_id':str(day.date()), 'open_time':start-pd.Timedelta(seconds=1),
                     'close_time':idx[-1]})
# Anchor grid at a whole minute; first source event must fall inside the session.
sessions = pd.DataFrame(sessions)
sessions['open_time'] += pd.Timedelta(seconds=1)
quotes = pd.concat(quote_parts,ignore_index=True)
quotes['event_time'] = quotes['available_at']
cutoff = sessions.close_time.iloc[15]
panel = prepare_panel(quotes,None,sessions,cfg,as_of=cutoff)
features = build_features(panel,cfg)
assert panel.index[-1] == cutoff and panel.session_id.nunique()==16

prefix_cutoff = sessions.open_time.iloc[1]+pd.Timedelta(minutes=181)
prefix_panel = prepare_panel(quotes,None,sessions,cfg,as_of=prefix_cutoff)
prefix_features = build_features(prefix_panel,cfg)
assert_frame_equal(prefix_features,features.loc[prefix_features.index],check_exact=True)

targets = make_targets(panel,features,cfg)
for h,y in targets.items():
    good = y.class_id.notna()
    assert ((y.loc[good,'target_end']-y.index[good])==pd.Timedelta(minutes=h)).all()
    assert (y.loc[good,'target_end']<=panel.loc[good,'session_close']).all()
    assert (y.loc[good,['mae_long_ticks','mae_short_ticks']]>=0).all().all()

research = fit_research(panel,features,targets,cfg)
assert research['status']=='ready', {h:(x['status'],x.get('reason')) for h,x in research['horizons'].items()}
for h,result in research['horizons'].items():
    for part,index in result['indices'].items():
        assert targets[h].loc[index,'target_end'].isin(research['splits'][part]).all()
    probabilities=result['predictions'][['pooled_p_down','pooled_p_neutral','pooled_p_up']].dropna()
    assert np.allclose(probabilities.sum(axis=1),1)
assert latest_readings(research).status.eq('forecast_unavailable').all()

live_cutoff = sessions.open_time.iloc[16] + pd.Timedelta(minutes=125)
live_panel = prepare_panel(quotes,None,sessions,cfg,as_of=live_cutoff)
live_features = build_features(live_panel,cfg)
live = predict_frozen(research,live_panel,live_features,cfg)
assert live.decision_time.eq(live_cutoff).all()
assert live.status.eq('research_forecast').all(),live[['horizon_minutes','status','data_status']].to_dict()
assert live_panel.session_close.iloc[-1] == sessions.close_time.iloc[16]

# An old revision cannot rewind the event clock; an invalid newest revision is retained.
t0 = sessions.open_time.iloc[0]
events = pd.DataFrame([
 {'event_time':t0,'available_at':t0,'value':1},
 {'event_time':t0+pd.Timedelta(minutes=1),'available_at':t0+pd.Timedelta(minutes=1),'value':2},
 {'event_time':t0,'available_at':t0+pd.Timedelta(minutes=2),'value':999},
 {'event_time':t0+pd.Timedelta(minutes=1),'available_at':t0+pd.Timedelta(minutes=3),'value':np.nan},
])
snapshot = _known_snapshots(events,pd.date_range(t0,periods=4,freq='min'))
assert snapshot.value.iloc[2]==2 and np.isnan(snapshot.value.iloc[3])

# Quote accounting must subtract the spread once, not twice.
ledger = futures_touch_benchmark(110,110.01,110.10,110.11,1,2,cfg)
assert np.isclose(ledger['net_benchmark_cad'],180)
assert np.isclose(ledger['spread_crossing_cad'],20)

# Joint-expert agreement at unit temperature must preserve that distribution.
p=np.array([[.1,.2,.7]])
assert np.allclose(opinion_pool(p,p,.25,1),p)

report={'fixture_type':'deterministic_software_only_not_market_evidence',
        'source_prefix_invariance':True,'revision_semantics':True,
        'horizon_and_split_endpoints':True,'all_three_horizons_execute':True,
        'frozen_mid_session_inference':True,'late_session_unavailable':True,
        'probability_normalization_and_idempotent_pool':True,'spread_counted_once':True}
print(json.dumps(report))
