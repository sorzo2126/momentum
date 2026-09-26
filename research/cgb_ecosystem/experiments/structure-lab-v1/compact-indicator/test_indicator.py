"""Meaningful display contract checks with the saved synthetic snapshot."""
from copy import deepcopy
from datetime import timedelta
import hashlib
import json
from pathlib import Path
from indicator import card, instant, IDENTITY

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent/'trader-view/snapshot.json'
base = json.loads(SOURCE.read_text(encoding='utf8'))
origin = instant(base['decision_time'])
identity = {k:base[k] for k in IDENTITY}
now = origin+timedelta(seconds=2)
# Explicit test envelope; these are UI contract fixtures, not new live observations.
health = {'as_of':now.isoformat(), 'sources':{
    name:{'event_time':(origin-timedelta(seconds=1)).isoformat(),
          'available_at':(origin-timedelta(seconds=0.65)).isoformat(), 'limit_seconds':limit}
    for name,limit in [('CGB',30),('US10',30),('CAD_benchmarks',300)]}}
defaults = dict(horizon=60, now=now.isoformat(), session_close=(origin+timedelta(hours=5.5)).isoformat(),
                expected_identity=identity, health=health, required_sources=tuple(health['sources']), expected_contract='SIM_CGB')
checks=[]
def run(name, mutate=None, options=None, expected='unavailable', inspect=None):
    payload=deepcopy(base)
    if mutate:mutate(payload)
    before=deepcopy(payload)
    output=card(payload, **{**deepcopy(defaults), **(options or {})})
    assert output['status']==expected, (name,output)
    assert payload==before, name+' mutated its source'
    if inspect:inspect(output)
    if expected in ('unavailable','expired'):assert output['forecast'] is None
    checks.append({'case':name,'status':'PASS'})
    return output
def eq(actual,wanted):assert actual==wanted,(actual,wanted)

saved=run('Saved upward phase maps up probability to continuation', expected='limited_inputs',
          inspect=lambda o:eq(o['forecast']['relative']['continuation'],base['forecasts'][0]['p_up']))
run('Downward phase maps down probability to continuation',lambda p:p['forecasts'][0].update(observed_state='down-responsive'),expected='limited_inputs',
    inspect=lambda o:eq(o['forecast']['relative']['continuation'],base['forecasts'][0]['p_down']))
run('Balanced phase has no invented continuation probability',lambda p:p['forecasts'][0].update(observed_state='balanced'),expected='limited_inputs',inspect=lambda o:eq(o['forecast']['relative'],None))
run('Equal class probabilities have no arbitrary winner',lambda p:p['forecasts'][0].update(p_up=1/3,p_down=1/3,p_neutral=1/3),expected='limited_inputs',inspect=lambda o:eq(o['headline'],'No single most likely endpoint'))
run('Complete selected inputs are distinguished from missing inputs',lambda p:p['data_status'].update(missing_model_features=[]),expected='available')
for h in (120,240):run('Horizon selection '+str(h),options={'horizon':h},expected='limited_inputs',inspect=lambda o:eq(o['horizon_minutes'],h))
run('Horizon unavailable', options={'horizon':90})
run('Explicit upstream unavailability',lambda p:p['forecasts'][0].update(status='unavailable',reason='Warmup'))
run('Reject mismatched run identity',lambda p:p.update(run_id='other-run'))
run('Reject wrong futures contract',lambda p:p.update(contract='OTHER_CGB'))
run('Reject unknown model status',lambda p:p['forecasts'][0].update(status='failed'))
run('Reject model newer than forecast',lambda p:p.update(model_available_after=origin.isoformat()))
run('Reject future forecast',options={'now':(origin-timedelta(seconds=1)).isoformat()})
run('Expire at the next five-minute update boundary',options={'now':(origin+timedelta(minutes=5)).isoformat()},expected='expired')
run('Reject horizon beyond session',options={'session_close':(origin+timedelta(minutes=59)).isoformat()})
run('Reject wrong target',lambda p:p['forecasts'][0].update(target_time=origin.isoformat()))
run('Reject duplicate horizon',lambda p:p['forecasts'].append(deepcopy(p['forecasts'][0])))
run('Reject mixed origin',lambda p:p['forecasts'][0].update(decision_time=(origin-timedelta(minutes=5)).isoformat()))
stale=deepcopy(health);stale['sources']['US10']['event_time']=(now-timedelta(seconds=31)).isoformat()
run('Required US source stale while heartbeat is fresh',options={'health':stale})
old=deepcopy(health);old['as_of']=(now-timedelta(seconds=6)).isoformat()
run('Reject old health heartbeat',options={'health':old})
run('Reject missing source policy',options={'health':{'as_of':now.isoformat(),'sources':{}}})
missing=deepcopy(health);missing['sources'].pop('US10')
run('Reject one missing required source',options={'health':missing})
future=deepcopy(health);future['sources']['CGB']['available_at']=(now+timedelta(seconds=1)).isoformat()
run('Reject source received in the future',options={'health':future})
run('Reject malformed probabilities',lambda p:p['forecasts'][0].update(p_up=.9))
run('Reject nonfinite forecast',lambda p:p['forecasts'][0].update(endpoint_mean_ticks=float('inf')))
run('Reject reversed quantiles',lambda p:p['forecasts'][0].update(endpoint_q10_ticks=100))
run('Reject negative adverse excursion',lambda p:p['forecasts'][0].update(mae_long_q80_ticks=-1))
run('Reject unknown observer state',lambda p:p['forecasts'][0].update(observed_state='up-invented'))
run('Reject crossed anchor quote',lambda p:p.update(bid=113))
run('Reject altered midpoint anchor',lambda p:p.update(midpoint=114))
def poison(p):
    p.update(future_return=999,truth='BUY')
    p['forecasts'][0].update(return_ticks=999,mae_long_ticks=999)
run('Future outcome fields cannot change displayed card',poison,expected='limited_inputs',inspect=lambda o:eq(o,saved))
before=json.dumps(base,sort_keys=True)
assert before==json.dumps(json.loads(SOURCE.read_text(encoding='utf8')),sort_keys=True)
(HERE/'example-card.json').write_text(json.dumps(saved,indent=2)+'\n',encoding='utf8')
result={'status':'PASS','tests':len(checks),'scope':'Display mapping and explicit test health envelope; no live service or statistical forecast validation.',
        'source_snapshot_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256((HERE/'indicator.py').read_bytes()).hexdigest(),'checks':checks}
(HERE/'logic-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k!='checks'}))
