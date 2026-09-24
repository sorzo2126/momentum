"""Causal measurements for the independent CAD duration research notebook.

No data is fabricated, no model is fitted here, and no order is sent. A snapshot
means what the receiver knew at its decision time, not the eventual corrected tape.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResearchConfig:
    grid_minutes: int = 1
    horizons_minutes: tuple = (60, 120, 240)
    tick_size: float = .01
    tick_value_cad: float = 10.
    cgb_stale_seconds: float = 30.
    us_stale_seconds: float = 30.
    context_stale_seconds: float = 30.
    rates_stale_seconds: float = 300.
    vwap_stale_seconds: float = 300.
    volatility_window: int = 60
    beta_window: int = 120
    momentum_windows: tuple = (5, 15, 30, 60)
    phase_threshold: float = .75
    efficiency_threshold: float = .35
    neutral_band_sigma: float = .35
    feature_modules: tuple = ('cgb',)
    min_train_sessions: int = 10
    min_cal_sessions: int = 3
    min_test_sessions: int = 3
    embargo_minutes: int = 240
    xgb_device: str = 'cpu'
    random_state: int = 1729


RATE_INSTRUMENTS = (
    'CAD2Y', 'CAD5Y', 'CAD10Y', 'OIS1Y', 'OIS2Y', 'OIS3Y', 'OIS4Y', 'OIS5Y',
    'SWAP1Y', 'SWAP2Y', 'SWAP3Y', 'SWAP4Y', 'SWAP5Y',
    'FWD1Y1Y', 'FWD2Y1Y',
)
PHASE_NAMES = {
    -1: 'unready', 0: 'balance', 1: 'up-forming', 2: 'up-persistent',
    3: 'up-weakening', 4: 'down-forming', 5: 'down-persistent',
    6: 'down-weakening',
}
FEATURE_MODULES = {
    'cgb': [
        'sigma_ticks', 'mom_z_5', 'mom_z_15', 'mom_z_30', 'mom_z_60',
        'efficiency_30', 'range_position_30', 'vol_ratio_15_60',
        'return_skew_60', 'down_semivol_ratio_60', 'spread_ticks',
    ] + [f'phase_{name}' for name in PHASE_NAMES.values() if name != 'unready'],
    'us': [
        'us_move_5', 'us_move_30', 'beta_us_prior', 'common_ticks_1',
        'local_ticks_1', 'local_z_30', 'cad_us_corr_prior',
    ],
    'curve': [f'cad_{name}_bp_{w}' for name in ('level5', 'slope25', 'slope510')
              for w in (5, 30)],
    'ois': [f'{name.lower()}_change_bp_{w}' for name in ('OIS1Y', 'OIS2Y', 'OIS3Y', 'OIS4Y', 'OIS5Y')
            for w in (5, 30)],
    'swaps': [f'swap{year}y_change_bp_{w}' for year in range(1, 6) for w in (5, 30)],
    'cad_futures': [f'{name}_move_logbp_{w}' for name in ('cgz', 'cgf') for w in (5, 30)],
    'forwards': [f'{name.lower()}_change_bp_{w}' for name in ('FWD1Y1Y', 'FWD2Y1Y')
                 for w in (5, 30)],
    'book': ['book_imbalance', 'microprice_displacement_ticks',
             'book_imbalance_mean_5'],
    'vwap': ['vwap_distance_ticks', 'vwap_distance_sigma', 'vwap_std_ticks'],
    'context': ['spx_move_logbp_5', 'spx_move_logbp_30',
                'vix_move_points_5', 'vix_move_points_30'],
}


def _utc_column(frame, name):
    """Reject naive clocks: guessing a timezone would silently change causality."""
    values = frame[name]
    if values.isna().any():
        raise ValueError(f'{name} contains missing timestamps')
    if any(pd.Timestamp(value).tzinfo is None for value in values):
        raise ValueError(f'{name} must contain timezone-aware timestamps')
    return pd.to_datetime(values, utc=True)


def _validate_cfg(cfg):
    if not isinstance(cfg.grid_minutes, int) or cfg.grid_minutes <= 0:
        raise ValueError('grid_minutes must be a positive integer')
    if cfg.tick_size <= 0 or cfg.tick_value_cad <= 0:
        raise ValueError('Tick size/value must be positive')
    windows = {5, 15, 30, 60, cfg.volatility_window, cfg.beta_window,
               *cfg.momentum_windows, *cfg.horizons_minutes}
    if any(w <= 0 or w % cfg.grid_minutes for w in windows):
        raise ValueError('Every window/horizon must be positive and divisible by grid_minutes')
    if cfg.volatility_window / cfg.grid_minutes < 2 or cfg.beta_window / cfg.grid_minutes < 2:
        raise ValueError('Volatility and beta windows require at least two grid steps')
    if min(cfg.cgb_stale_seconds, cfg.us_stale_seconds, cfg.context_stale_seconds, cfg.rates_stale_seconds,
           cfg.vwap_stale_seconds) < 0:
        raise ValueError('Staleness limits cannot be negative')
    if cfg.phase_threshold < 0 or not 0 <= cfg.efficiency_threshold <= 1:
        raise ValueError('Invalid descriptive phase thresholds')
    if not np.isfinite(cfg.neutral_band_sigma) or cfg.neutral_band_sigma < 0:
        raise ValueError('neutral_band_sigma must be finite and nonnegative')
    unknown = set(cfg.feature_modules).difference(FEATURE_MODULES)
    if unknown:
        raise ValueError(f'Unknown feature modules: {sorted(unknown)}')


def _normalise_events(frame, fields, allowed):
    """Validate identity/clocks while retaining invalid numeric observations."""
    if frame is None or len(frame) == 0:
        return pd.DataFrame(columns=fields)
    frame = frame.copy()
    missing = set(fields).difference(frame.columns)
    if missing:
        raise ValueError(f'Input is missing columns: {sorted(missing)}')
    if frame['instrument'].isna().any():
        raise ValueError('Missing instrument identifier')
    unknown = set(frame['instrument']).difference(allowed)
    if unknown:
        raise ValueError(f'Unsupported instrument identifiers: {sorted(unknown)}')
    for clock in ('event_time', 'available_at'):
        frame[clock] = _utc_column(frame, clock)
    if (frame['event_time'] > frame['available_at']).any():
        raise ValueError('event_time exceeds available_at; repair the clock definition first')
    identity = ['instrument', 'event_time', 'available_at']
    if frame.duplicated(identity).any():
        raise ValueError('Ambiguous duplicate instrument/event/version timestamps')
    return frame.sort_values(['available_at', 'event_time'], kind='stable')


def _known_snapshots(events, grid):
    """Newest event known, then newest version; late old events never rewind it.

    An invalid correction of the newest event remains the latest observation.
    Numeric validity is intentionally assessed only AFTER this temporal selection.
    One receiver timestamp is required per atomic bid/ask or rate snapshot.
    """
    if events.empty:
        return pd.DataFrame(index=grid)
    rows = list(events.to_dict('records'))
    output, position, newest = [], 0, None
    for decision in grid:
        while position < len(rows) and rows[position]['available_at'] <= decision:
            candidate = rows[position]
            if newest is None or candidate['event_time'] >= newest['event_time']:
                newest = candidate
            position += 1
        output.append({} if newest is None else newest.copy())
    return pd.DataFrame(output, index=grid)


def _quote_snapshot(events, grid, prefix, stale_seconds):
    snapshot = _known_snapshots(events, grid)
    output = pd.DataFrame(index=grid)
    for col in ('bid', 'ask', 'bid_size', 'ask_size'):
        output[f'{prefix}_{col}'] = pd.to_numeric(
            snapshot.get(col, pd.Series(np.nan, index=grid)), errors='coerce')
    output[f'{prefix}_contract'] = snapshot.get('contract', pd.Series(None, index=grid, dtype=object))
    for clock in ('event_time', 'available_at'):
        output[f'{prefix}_{clock}'] = pd.to_datetime(
            snapshot.get(clock, pd.Series(pd.NaT, index=grid)), utc=True)
    age = (grid.to_series() - output[f'{prefix}_event_time']).dt.total_seconds()
    output[f'{prefix}_age_seconds'] = age
    bid, ask = output[f'{prefix}_bid'], output[f'{prefix}_ask']
    valid = (np.isfinite(bid) & np.isfinite(ask) & (bid > 0) & (ask >= bid)
             & age.between(0, stale_seconds)
             & output[f'{prefix}_contract'].notna()
             & output[f'{prefix}_contract'].astype(str).str.len().gt(0))
    output[f'{prefix}_valid'] = valid
    output[f'{prefix}_mid'] = ((bid + ask) / 2).where(valid)
    return output


def prepare_panel(quotes, rates, sessions, cfg, trades=None, context=None, as_of=None):
    """Build an explicit receiver-time grid without crossing session/contract gaps.

    quotes: atomic CGB/US10/CGZ/CGF or quoted-context snapshots; rates: rate_bp.
    context: optional SPX/VIX scalar value marks with event/availability clocks. Prices
    must be decimal price points (convert Treasury fractional notation upstream).
    sessions: explicit open/close timestamps and unique session_id. No exchange
    calendar, contract-roll convention, vendor mapping or data revision is inferred.
    as_of is an explicit timezone-aware receiver cutoff, required for both live
    and historical runs. It is never inferred from the final source quote.
    """
    _validate_cfg(cfg)
    if as_of is None:
        raise ValueError('Set an explicit timezone-aware as_of receiver cutoff before constructing the panel')
    cutoff = pd.Timestamp(as_of)
    if pd.isna(cutoff) or cutoff.tzinfo is None:
        raise ValueError('as_of must be a nonmissing timezone-aware timestamp')
    cutoff = cutoff.tz_convert('UTC')
    if quotes is None or sessions is None:
        raise ValueError('Provide quotes and explicit sessions; no data is fabricated')
    quote_fields = ['instrument', 'contract', 'event_time', 'available_at', 'bid', 'ask']
    q = _normalise_events(quotes, quote_fields, {'CGB', 'US10', 'CGZ', 'CGF', 'SPX', 'VIX'})
    r = _normalise_events(rates, ['instrument', 'event_time', 'available_at', 'rate_bp'],
                          set(RATE_INSTRUMENTS))
    context_rows = _normalise_events(context, ['instrument', 'event_time', 'available_at', 'value'],
                                     {'SPX', 'VIX'})
    if set(context_rows['instrument']).intersection(set(q['instrument'])):
        raise ValueError('Choose scalar context OR quote context per instrument, not both')
    if q.empty or not q['instrument'].eq('CGB').any():
        raise ValueError('At least one CGB quote is required')
    required = {'session_id', 'open_time', 'close_time'}
    if not required.issubset(sessions.columns):
        raise ValueError(f'Sessions require {sorted(required)}')
    sessions = sessions.copy()
    if sessions['session_id'].isna().any() or sessions['session_id'].astype(str).duplicated().any():
        raise ValueError('session_id must be present and unique')
    for col in ('open_time', 'close_time'):
        sessions[col] = _utc_column(sessions, col)
    sessions = sessions.sort_values('open_time')
    if (sessions['close_time'] <= sessions['open_time']).any():
        raise ValueError('Session close must be later than open')
    if (sessions['open_time'].iloc[1:].to_numpy() <=
            sessions['close_time'].iloc[:-1].to_numpy()).any():
        raise ValueError('Sessions may not overlap or share an endpoint')
    panels = []
    for s in sessions[sessions['open_time'] <= cutoff].itertuples(index=False):
        grid = pd.date_range(s.open_time, min(s.close_time, cutoff),
                             freq=f'{cfg.grid_minutes}min', name='decision_time')
        if not len(grid):
            continue
        p = pd.DataFrame(index=grid)
        p['session_id'], p['session_close'] = s.session_id, s.close_time
        # At a new session, only new-session event observations are eligible.
        # This avoids yesterday's quote being considered fresh at an early open.
        session_q = q[(q['event_time'] >= s.open_time) & (q['available_at'] <= s.close_time)]
        for instrument, prefix, limit in (
            ('CGB', 'cgb', cfg.cgb_stale_seconds), ('US10', 'us', cfg.us_stale_seconds),
            ('CGZ', 'cgz', cfg.cgb_stale_seconds), ('CGF', 'cgf', cfg.cgb_stale_seconds),
            ('SPX', 'spx', cfg.context_stale_seconds), ('VIX', 'vix', cfg.context_stale_seconds),
        ):
            snap = _quote_snapshot(session_q[session_q['instrument'].eq(instrument)],
                                   grid, prefix, limit)
            p = p.join(snap)
        for instrument, prefix in (('SPX', 'spx'), ('VIX', 'vix')):
            p[f'{prefix}_measurement_kind'] = 'quote_mid'
            if instrument not in set(context_rows['instrument']):
                continue
            scalar_events = context_rows[(context_rows['instrument'].eq(instrument)) &
                                         (context_rows['event_time'] >= s.open_time) &
                                         (context_rows['available_at'] <= s.close_time)]
            snap = _known_snapshots(scalar_events, grid)
            value = pd.to_numeric(snap.get('value', pd.Series(np.nan, index=grid)), errors='coerce')
            for clock in ('event_time', 'available_at'):
                p[f'{prefix}_{clock}'] = pd.to_datetime(
                    snap.get(clock, pd.Series(pd.NaT, index=grid)), utc=True)
            age = (grid.to_series() - p[f'{prefix}_event_time']).dt.total_seconds()
            valid = np.isfinite(value) & (value > 0) & age.between(0, cfg.context_stale_seconds)
            p[f'{prefix}_age_seconds'], p[f'{prefix}_valid'] = age, valid
            p[f'{prefix}_mid'] = value.where(valid)
            p[f'{prefix}_contract'] = instrument + ':scalar_mark'
            p[f'{prefix}_measurement_kind'] = 'scalar_mark'
        p['contract'] = p['cgb_contract']
        contract_key = p['contract'].fillna('<unobserved>').astype(str)
        run = contract_key.ne(contract_key.shift()).cumsum()
        p['segment_id'] = str(s.session_id) + ':' + run.astype(str)
        for prefix in ('cgb', 'us', 'cgz', 'cgf', 'spx', 'vix'):
            same_contract = p[f'{prefix}_contract'].eq(p[f'{prefix}_contract'].shift())
            pair_valid = p[f'{prefix}_valid'] & p[f'{prefix}_valid'].shift(fill_value=False)
            changes = p[f'{prefix}_mid'].diff().where(same_contract & pair_valid)
            if prefix == 'cgb':
                p['cgb_ret_ticks'] = changes / cfg.tick_size
            elif prefix == 'vix':
                p['vix_ret_points'] = changes
            else:
                logret = 10000 * np.log(p[f'{prefix}_mid'] / p[f'{prefix}_mid'].shift())
                p[f'{prefix}_ret_logbp'] = logret.where(same_contract & pair_valid)
        session_r = r[(r['event_time'] >= s.open_time) & (r['available_at'] <= s.close_time)]
        for name in RATE_INSTRUMENTS:
            snapshot = _known_snapshots(session_r[session_r['instrument'].eq(name)], grid)
            rate = pd.to_numeric(snapshot.get('rate_bp', pd.Series(np.nan, index=grid)),
                                 errors='coerce')
            event_time = pd.to_datetime(snapshot.get('event_time', pd.Series(pd.NaT, index=grid)), utc=True)
            age = (grid.to_series() - event_time).dt.total_seconds()
            valid = np.isfinite(rate) & age.between(0, cfg.rates_stale_seconds)
            p[f'{name}_bp'], p[f'{name}_valid'] = rate.where(valid), valid
            p[f'{name}_age_seconds'] = age
        panels.append(p)
    if not panels:
        raise ValueError('No decision grid could be constructed')
    panel = pd.concat(panels).sort_index()
    if panel.index.has_duplicates:
        raise ValueError('Decision timestamps must be globally unique')
    return _attach_observed_vwap(panel, trades, cfg)


def _attach_observed_vwap(panel, trades, cfg):
    """Volume-weighted observed trade prices, with no inferred missing trades.

    Corrections/cancellations must be reconciled upstream into a point-in-time
    event adapter; this simple adapter rejects repeated trade IDs. Coverage of
    the venue trade tape cannot be certified from the supplied rows alone.
    """
    panel = panel.copy()
    for name in ('vwap', 'vwap_std', 'vwap_age_seconds', 'vwap_observed_volume'):
        panel[name] = np.nan
    panel['vwap_status'] = 'no_trades'
    panel['vwap_anchor'] = pd.Series(pd.NaT, index=panel.index, dtype='datetime64[ns, UTC]')
    if trades is None or len(trades) == 0:
        return panel
    required = {'trade_id', 'instrument', 'contract', 'event_time', 'available_at', 'price', 'size'}
    if not required.issubset(trades.columns):
        raise ValueError(f'Trades require {sorted(required)}')
    t = trades.copy()
    if t['trade_id'].isna().any() or t['trade_id'].duplicated().any():
        raise ValueError('Trade IDs must be unique; reconcile corrections before this adapter')
    if not t['instrument'].eq('CGB').all() or t['contract'].isna().any():
        raise ValueError('The trade adapter accepts identified CGB contracts only')
    for name in ('event_time', 'available_at'):
        t[name] = _utc_column(t, name)
    if (t['event_time'] > t['available_at']).any():
        raise ValueError('Trade event_time exceeds available_at')
    for name in ('price', 'size'):
        t[name] = pd.to_numeric(t[name], errors='coerce')
        if not (np.isfinite(t[name]) & t[name].gt(0)).all():
            raise ValueError(f'Trade {name} must be finite and positive')
    t = t.sort_values(['available_at', 'event_time'], kind='stable')
    for _, group in panel.groupby('segment_id', sort=False):
        contract = group['contract'].iloc[0]
        if pd.isna(contract):
            continue
        # Resets on each fixed-contract run. A late first quote means the anchor
        # is later than session open; display the anchor rather than invent data.
        anchor, endpoint = group.index[0], group.index[-1]
        panel.loc[group.index, 'vwap_anchor'] = anchor
        rows = t[(t['contract'].eq(contract)) & t['event_time'].between(anchor, endpoint)]
        rows = list(rows.to_dict('records'))
        j, volume, mean, m2, latest = 0, 0., 0., 0., None
        for decision in group.index:
            while j < len(rows) and rows[j]['available_at'] <= decision:
                trade = rows[j]
                new_volume = volume + trade['size']
                delta = trade['price'] - mean
                new_mean = mean + trade['size'] / new_volume * delta
                m2 += trade['size'] * delta * (trade['price'] - new_mean)
                mean, volume = new_mean, new_volume
                latest = trade['event_time'] if latest is None else max(latest, trade['event_time'])
                j += 1
            if volume <= 0:
                continue
            age = (decision - latest).total_seconds()
            panel.loc[decision, 'vwap_age_seconds'] = age
            panel.loc[decision, 'vwap_observed_volume'] = volume
            panel.loc[decision, 'vwap_status'] = 'observed_tape' if age <= cfg.vwap_stale_seconds else 'stale'
            if age <= cfg.vwap_stale_seconds:
                panel.loc[decision, 'vwap'] = mean
                panel.loc[decision, 'vwap_std'] = np.sqrt(max(m2 / volume, 0.))
    return panel


def _complete_change(series, steps):
    """Endpoint change only when every point in the interval is observed."""
    complete = series.notna().rolling(steps + 1, min_periods=steps + 1).sum().eq(steps + 1)
    return series.diff(steps).where(complete)


def _segment_features(p, cfg):
    """All rolling operations are confined to one session/contract run."""
    f = pd.DataFrame(index=p.index)
    steps = lambda minutes: int(minutes // cfg.grid_minutes)
    returns = p['cgb_ret_ticks']
    vol_n = steps(cfg.volatility_window)
    # This scale precedes the current completed return; 0.25 is a declared floor,
    # not a claim about exchange ticks or a fitted market noise parameter.
    f['sigma_ticks'] = returns.rolling(vol_n, min_periods=vol_n).std(ddof=1).shift(1).clip(lower=.25)
    windows = sorted({5, 15, 30, 60, *cfg.momentum_windows})
    for minutes in windows:
        n = steps(minutes)
        net = returns.rolling(n, min_periods=n).sum()
        path = returns.abs().rolling(n, min_periods=n).sum()
        f[f'mom_ticks_{minutes}'] = net
        f[f'mom_z_{minutes}'] = net / (f['sigma_ticks'] * np.sqrt(n))
        # A truly unchanged path has efficiency zero; an unobserved one stays NaN.
        f[f'efficiency_{minutes}'] = (net.abs() / path.where(path > 0)).where(path.ne(0), 0.)
    n30, n15, n60 = steps(30), steps(15), steps(60)
    mid = p['cgb_mid']
    low = mid.rolling(n30 + 1, min_periods=n30 + 1).min()
    high = mid.rolling(n30 + 1, min_periods=n30 + 1).max()
    width = high - low
    f['range_position_30'] = ((mid - low) / width.where(width > 0)).where(width.ne(0), .5)
    sigma15 = returns.rolling(n15, min_periods=n15).std(ddof=1)
    sigma60 = returns.rolling(n60, min_periods=n60).std(ddof=1)
    f['vol_ratio_15_60'] = sigma15 / sigma60.clip(lower=.25)
    f['return_skew_60'] = returns.rolling(n60, min_periods=n60).skew()
    energy = returns.pow(2).rolling(n60, min_periods=n60).sum()
    downside = returns.clip(upper=0).pow(2).rolling(n60, min_periods=n60).sum()
    f['down_semivol_ratio_60'] = (downside / energy.where(energy > 0)).where(energy.ne(0), .5)
    f['spread_ticks'] = ((p['cgb_ask'] - p['cgb_bid']) / cfg.tick_size).where(p['cgb_valid'])

    us = p['us_ret_logbp']
    n_beta = steps(cfg.beta_window)
    # Keep the regular grid, so a missing pair cannot be skipped in the window.
    cad_pair = returns.where(us.notna())
    us_pair = us.where(returns.notna())
    covariance = cad_pair.rolling(n_beta, min_periods=n_beta).cov(us_pair).shift(1)
    variance = us_pair.rolling(n_beta, min_periods=n_beta).var().shift(1)
    f['beta_us_prior'] = covariance / variance.where(variance > 1e-14)
    f['cad_us_corr_prior'] = cad_pair.rolling(n_beta, min_periods=n_beta).corr(us_pair).shift(1)
    f['common_ticks_1'] = f['beta_us_prior'] * us
    f['local_ticks_1'] = returns - f['common_ticks_1']
    local = f['local_ticks_1']
    local_sigma = local.rolling(vol_n, min_periods=vol_n).std().shift(1).clip(lower=.25)
    f['local_z_30'] = local.rolling(n30, min_periods=n30).sum() / (local_sigma * np.sqrt(n30))
    for minutes in (5, 30):
        n = steps(minutes)
        f[f'us_move_{minutes}'] = us.rolling(n, min_periods=n).sum()
        changes = {name: _complete_change(p[f'{name}_bp'], n) for name in RATE_INSTRUMENTS}
        f[f'cad_level5_bp_{minutes}'] = changes['CAD5Y']
        f[f'cad_slope25_bp_{minutes}'] = changes['CAD5Y'] - changes['CAD2Y']
        f[f'cad_slope510_bp_{minutes}'] = changes['CAD10Y'] - changes['CAD5Y']
        for name in RATE_INSTRUMENTS:
            f[f'{name.lower()}_change_bp_{minutes}'] = changes[name]
        f[f'spx_move_logbp_{minutes}'] = p['spx_ret_logbp'].rolling(n, min_periods=n).sum()
        f[f'vix_move_points_{minutes}'] = p['vix_ret_points'].rolling(n, min_periods=n).sum()
        for prefix in ('cgz', 'cgf'):
            f[f'{prefix}_move_logbp_{minutes}'] = p[f'{prefix}_ret_logbp'].rolling(n, min_periods=n).sum()

    bid_q = pd.to_numeric(p['cgb_bid_size'], errors='coerce')
    ask_q = pd.to_numeric(p['cgb_ask_size'], errors='coerce')
    size_ok = np.isfinite(bid_q) & np.isfinite(ask_q) & (bid_q >= 0) & (ask_q >= 0)
    total = (bid_q + ask_q).where(size_ok & p['cgb_valid'] & ((bid_q + ask_q) > 0))
    f['book_imbalance'] = (bid_q - ask_q) / total
    micro = (p['cgb_ask'] * bid_q + p['cgb_bid'] * ask_q) / total
    f['microprice_displacement_ticks'] = (micro - mid) / cfg.tick_size
    f['book_imbalance_mean_5'] = f['book_imbalance'].rolling(steps(5), min_periods=steps(5)).mean()
    f['vwap_distance_ticks'] = (mid - p['vwap']) / cfg.tick_size
    f['vwap_std_ticks'] = p['vwap_std'] / cfg.tick_size
    # Flat supplied trades have zero dispersion: a sigma-distance is undefined.
    f['vwap_distance_sigma'] = (mid - p['vwap']) / p['vwap_std'].where(p['vwap_std'] > 0)

    z, efficiency = f['mom_z_30'], f['efficiency_30']
    fast = f['mom_ticks_5'] / steps(5)
    slow = f['mom_ticks_30'] / n30
    direction = np.sign(z)
    active = z.abs() >= cfg.phase_threshold
    # "Weakening" is relative observed drift, never an inferred future reversal.
    weakening = direction * fast < .5 * direction * slow
    persistent = efficiency >= cfg.efficiency_threshold
    phase = pd.Series(0, index=p.index, dtype='int64')
    phase.loc[active & (direction > 0)] = 1
    phase.loc[active & (direction < 0)] = 4
    phase.loc[active & persistent & (direction > 0)] = 2
    phase.loc[active & persistent & (direction < 0)] = 5
    phase.loc[active & weakening & (direction > 0)] = 3
    phase.loc[active & weakening & (direction < 0)] = 6
    core_before_phase = FEATURE_MODULES['cgb'][:11]
    ready = np.isfinite(f[core_before_phase]).all(axis=1) & p['cgb_valid']
    phase.loc[~ready] = -1
    f['phase_code'] = phase
    for code, name in PHASE_NAMES.items():
        if code >= 0:
            f[f'phase_{name}'] = phase.eq(code).astype(float).where(ready)
    # Missing current CGB input invalidates the whole observation, not just price.
    f.loc[~p['cgb_valid'], f.columns.difference(['phase_code'])] = np.nan
    return f.replace([np.inf, -np.inf], np.nan)


def build_features(panel, cfg):
    """Return causal, unscaled features; module activation is an explicit choice.

    Core phase labels describe current price paths. Optional measurements remain
    NaN when unavailable. No rolling window, normalizer or phase uses future data.
    Recompute on a prefix and its features equal that prefix of the full run.
    """
    _validate_cfg(cfg)
    if panel.empty or not panel.index.is_monotonic_increasing or panel.index.has_duplicates:
        raise ValueError('Panel must be nonempty, sorted and uniquely indexed')
    result = pd.concat([_segment_features(group, cfg)
                        for _, group in panel.groupby('segment_id', sort=False)])
    return result.reindex(panel.index)
