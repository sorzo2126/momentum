"""Local causal opening-range observer for the independent SPY presentation.

This consumes completed bars and an explicitly dated known range. It does not
load any CGB source, data, model, credentials or network resource.
"""


def observe_events(bars, opening_range):
    if opening_range is None:
        return []
    high = opening_range['high']
    low = opening_range['low']
    known = opening_range['known_at_time']
    side, count, episode = 0, 0, 0
    events = []
    for bar in bars:
        if bar['time'] <= known or bar['close'] is None:
            continue
        price = bar['close']
        new = 1 if price > high + 1e-10 else -1 if price < low - 1e-10 else 0
        event = None
        if new == 0:
            if side != 0:
                event = dict(type='returned_inside', level='opening_range',
                    level_price=high if side > 0 else low,
                    label='Returned inside opening range',
                    previous_side='above' if side > 0 else 'below')
            side, count = 0, 0
        elif new != side:
            episode += 1
            side, count = new, 1
            event = dict(type='break_above' if side > 0 else 'break_below',
                level='opening_range_high' if side > 0 else 'opening_range_low',
                level_price=high if side > 0 else low,
                label='Break above opening range' if side > 0 else 'Break below opening range')
        else:
            count += 1
            if count == 2:
                event = dict(type='held_above' if side > 0 else 'held_below',
                    level='opening_range_high' if side > 0 else 'opening_range_low',
                    level_price=high if side > 0 else low,
                    label='Held above: two completed closes' if side > 0 else 'Held below: two completed closes')
        if event:
            event.update(time=bar['time'], as_of=bar['as_of'], confirmed_at=bar['as_of'],
                price=price, episode_id=episode, level_known_at=opening_range['known_at'],
                consecutive_closes=count, source='causal_opening_range_observer')
            events.append(event)
    return events
