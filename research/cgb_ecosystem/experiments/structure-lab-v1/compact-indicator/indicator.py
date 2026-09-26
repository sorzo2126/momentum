"""Pure display mapping for an enriched forecast snapshot; no model or data access.

This prototype consumes the prior trader-view schema, not raw CLI output.
Health, session and expected identity must come from the future service adapter.
"""
from datetime import datetime, timedelta
import math

STATES = {'balanced', 'up-responsive', 'up-weakening', 'down-responsive', 'down-weakening'}
IDENTITY = ('run_id', 'code_contract_version', 'state_series_hash')


def instant(value):
    result = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timezone missing')
    return result


def finite(value):
    return isinstance(value, (float, int)) and not isinstance(value, bool) and math.isfinite(value)


def card(snapshot, *, horizon, now, session_close, expected_identity,
         health, required_sources, expected_contract, refresh_seconds=300):
    """Map one frozen forecast to a small card, or an explicit unavailable state.

    Five-minute expiry is a proposed UI policy matching S0's origin grid.
    Health is separately timestamped; it never changes the frozen forecast origin.
    Required-source selection must match the fitted model's declared dependencies.
    """
    result = {'status': 'unavailable', 'headline': 'Reading unavailable',
              'reason': '', 'forecast': None, 'mode': snapshot.get('display_mode', 'unknown'),
              'horizon_minutes': horizon}

    def reject(reason, status='unavailable'):
        result.update(status=status, headline='Reading expired' if status == 'expired' else 'Reading unavailable', reason=reason)
        return result

    try:
        if not finite(refresh_seconds) or refresh_seconds <= 0:
            return reject('Invalid refresh policy')
        if any(not expected_identity.get(k) or snapshot.get(k) != expected_identity[k] for k in IDENTITY):
            return reject('Model identity mismatch')
        if snapshot.get('contract') != expected_contract or not expected_contract:
            return reject('Instrument contract mismatch')
        decision, current, close = map(instant, (snapshot['decision_time'], now, session_close))
        if not instant(snapshot['model_available_after']) < decision:
            return reject('Forecast predates model availability')
        if current < decision:
            return reject('Forecast is from the future')
        matches = [f for f in snapshot['forecasts'] if f.get('horizon_minutes') == horizon]
        if len(matches) != 1:
            return reject('Missing or duplicate horizon')
        row = matches[0]
        if row.get('status') == 'unavailable':
            return reject(row.get('reason', 'Model unavailable'))
        if row.get('status') not in (None, 'research_forecast'):
            return reject('Unrecognised forecast status')
        if instant(row['decision_time']) != decision:
            return reject('Mixed forecast origins')
        target = decision + timedelta(minutes=horizon)
        if instant(row['target_time']) != target:
            return reject('Incorrect target time')
        if target > close:
            return reject('Horizon extends beyond session')
        result.update(decision_time=decision.isoformat(), target_time=target.isoformat())
        if current >= decision + timedelta(seconds=refresh_seconds):
            return reject('Awaiting the next scheduled forecast', 'expired')
        health_time = instant(health['as_of'])
        if health_time > current or (current-health_time).total_seconds() > 5:
            return reject('Health heartbeat unavailable')
        if not required_sources or not health.get('sources'):
            return reject('Required sources unspecified')
        if not set(required_sources).issubset(health['sources']):
            return reject('Required source missing')
        for name in required_sources:
            source = health['sources'][name]
            limit = source['limit_seconds']
            if not finite(limit) or limit <= 0:
                return reject('Invalid freshness policy: '+name)
            for clock in ('event_time', 'available_at'):
                age = (current-instant(source[clock])).total_seconds()
                if age < 0 or age > limit:
                    label = {'CGB':'CGB quote', 'US10':'US duration quote',
                             'CAD_benchmarks':'Canadian benchmark quote'}.get(name, name)
                    return reject(('Future-dated ' if age < 0 else 'Stale ')+label)
        if row.get('observed_state') not in STATES:
            return reject('Unrecognised observed state')
        numeric = ('p_down', 'p_neutral', 'p_up', 'endpoint_mean_ticks',
                   'endpoint_q10_ticks', 'endpoint_q90_ticks',
                   'mae_long_q80_ticks', 'mae_short_q80_ticks', 'neutral_band_ticks')
        if any(not finite(row.get(k)) for k in numeric):
            return reject('Missing or nonfinite forecast value')
        probs = {s:row['p_'+s] for s in ('down', 'neutral', 'up')}
        if any(p < 0 or p > 1 for p in probs.values()) or abs(sum(probs.values())-1) > 1e-6:
            return reject('Invalid probability distribution')
        if row['endpoint_q10_ticks'] > row['endpoint_q90_ticks']:
            return reject('Reversed endpoint interval')
        if min(row['mae_long_q80_ticks'], row['mae_short_q80_ticks'], row['neutral_band_ticks']) < 0:
            return reject('Negative excursion or neutral band')
        if any(not finite(snapshot.get(k)) for k in ('bid', 'ask', 'midpoint', 'tick_size')):
            return reject('Invalid quote anchor')
        if snapshot['ask'] < snapshot['bid'] or snapshot['tick_size'] <= 0:
            return reject('Crossed quote or invalid tick size')
        if abs((snapshot['ask']+snapshot['bid'])/2-snapshot['midpoint']) > 1e-8:
            return reject('Midpoint anchor mismatch')
        state = row['observed_state']
        direction = 'up' if state.startswith('up-') else 'down' if state.startswith('down-') else None
        winners = [s for s,p in probs.items() if abs(p-max(probs.values())) <= 1e-9]
        label = 'No single most likely endpoint' if len(winners)>1 else {
            'up':'Upside is the most likely endpoint', 'down':'Downside is the most likely endpoint',
            'neutral':'Neutral is the most likely endpoint'}[winners[0]]
        relative = None if direction is None else {
            'direction':direction, 'continuation':probs[direction],
            'opposite':probs['down' if direction=='up' else 'up'], 'neutral':probs['neutral']}
        missing = list(snapshot.get('data_status',{}).get('missing_model_features', []))
        return {**result, 'status':'limited_inputs' if missing else 'available',
                'headline':label, 'reason':', '.join(missing),
                'observed_state':state, 'observed_direction':direction,
                'forecast':{**{k:row[k] for k in numeric}, 'relative':relative,
                            'anchor_midpoint':snapshot['midpoint'],
                            'anchor_spread_ticks':(snapshot['ask']-snapshot['bid'])/snapshot['tick_size']},
                'identity':{k:snapshot[k] for k in IDENTITY},
                'interpretation':'Endpoint at the target time, measured from the frozen origin; no trend-survival claim.'}
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return reject('Incomplete or invalid envelope: '+str(error))
