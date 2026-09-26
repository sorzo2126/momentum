"""Prepare saved-value and clearly labelled failure fixtures for the compact UI."""
from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
from indicator import card, instant, IDENTITY

root=Path(__file__).resolve().parent
source=json.loads((root.parent/'trader-view/snapshot.json').read_text(encoding='utf8'))
origin=instant(source['decision_time'])
output={}
for variant in ('saved','stale','expired'):
    now=origin+timedelta(seconds=2 if variant!='expired' else 301)
    health={'as_of':now.isoformat(),'sources':{
        name:{'event_time':(now-timedelta(seconds=1)).isoformat(),
              'available_at':(now-timedelta(seconds=.65)).isoformat(),'limit_seconds':limit}
        for name,limit in [('CGB',30),('US10',30),('CAD_benchmarks',300)]}}
    if variant=='stale':health['sources']['US10']['event_time']=(now-timedelta(seconds=31)).isoformat()
    output[variant]={str(h):card(deepcopy(source),horizon=h,now=now.isoformat(),
        session_close=(origin+timedelta(hours=5.5)).isoformat(),
        expected_identity={k:source[k] for k in IDENTITY},health=health,
        required_sources=tuple(health['sources']),expected_contract='SIM_CGB') for h in (60,120,240)}
result={'cases':output,'provenance':'Saved historical synthetic forecast; health and failure states are UI fixtures.',
        'context':{'past_30m_ticks':source['observed_context']['mom_ticks_30'],
                   'vwap_distance_ticks':source['observed_context']['vwap_distance_ticks']}}
(root/'preview-cases.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print('Prepared three horizons and three explicitly labelled UI states.')
