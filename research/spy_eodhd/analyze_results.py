"""Post-hoc diagnosis of frozen SPY forecasts; no refit or trading-rule search."""
from pathlib import Path
import hashlib
import json
import pickle
import numpy as np
import pandas as pd
from run_study import block_ci, make_targets
from momentum.scenarios import weighted_quantile

HERE = Path(__file__).resolve().parent


def interval_score(y, lower, upper, alpha=.2):
    return upper-lower + 2/alpha*np.maximum(lower-y, 0) + 2/alpha*np.maximum(y-upper, 0)


def pinball(y, forecast, q=.8):
    error = y-forecast
    return np.maximum(q*error, (q-1)*error)


def main():
    private = HERE/'private'
    inputs = [private/name for name in ['predictions.csv.gz', 'session-scores.csv',
              'features.csv.gz', 'clean-bars.csv.gz', 'frozen-model.pkl']]
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    forecasts = pd.read_csv(inputs[0], parse_dates=['decision_time', 'target_end'])
    daily = pd.read_csv(inputs[1])
    features = pd.read_csv(inputs[2], index_col=0, parse_dates=True)
    bars = pd.read_csv(inputs[3], index_col=0, parse_dates=True)
    with inputs[4].open('rb') as stream:
        fits = pickle.load(stream)  # Trusted artifact produced locally by run_study.py.
    results, risk_rows, comparisons, stability = {}, [], [], []
    for h, g in forecasts.groupby('horizon_minutes'):
        g = g.set_index('decision_time').sort_index()
        probabilities = g[['p_down', 'p_neutral', 'p_up']]
        maximum = probabilities.max(axis=1)
        balance = g.p_up-g.p_down
        sigma = features.loc[g.index, 'sigma_ticks']
        target = make_targets(bars, features, int(h)).loc[g.index]
        np.testing.assert_allclose(target.return_ticks, g.actual_return_ticks)
        bank = fits[int(h)]['entry']['bank']
        weights = bank['session_weights']/bank['session_weights'].sum()
        base_mean = float(weights@bank['endpoint'])*sigma
        lo = weighted_quantile(bank['endpoint'], weights, .1)*sigma
        hi = weighted_quantile(bank['endpoint'], weights, .9)*sigma
        baseline_long = weighted_quantile(bank['mae_long'], weights, .8)*sigma
        baseline_short = weighted_quantile(bank['mae_short'], weights, .8)*sigma
        y = g.actual_return_ticks
        frame = pd.DataFrame({'session': g.session_id,
            'mixture_endpoint_absolute_error': abs(g.endpoint_mean_ticks-y),
            'zero_endpoint_absolute_error': abs(y),
            'baseline_endpoint_absolute_error': abs(base_mean-y),
            'mixture_endpoint_squared_error': (g.endpoint_mean_ticks-y)**2,
            'zero_endpoint_squared_error': y**2,
            'baseline_endpoint_squared_error': (base_mean-y)**2,
            'mixture_interval_score': interval_score(y, g.endpoint_q10_ticks, g.endpoint_q90_ticks),
            'baseline_interval_score': interval_score(y, lo, hi),
            'mixture_interval_coverage': y.between(g.endpoint_q10_ticks, g.endpoint_q90_ticks).astype(float),
            'baseline_interval_coverage': y.between(lo, hi).astype(float),
            'mixture_interval_width': g.endpoint_q90_ticks-g.endpoint_q10_ticks,
            'baseline_interval_width': hi-lo,
            'mixture_long_pinball': pinball(target.mae_long_ticks, g.mae_long_q80_ticks),
            'baseline_long_pinball': pinball(target.mae_long_ticks, baseline_long),
            'mixture_short_pinball': pinball(target.mae_short_ticks, g.mae_short_q80_ticks),
            'baseline_short_pinball': pinball(target.mae_short_ticks, baseline_short),
            'baseline_long_coverage': target.mae_long_ticks.le(baseline_long).astype(float),
            'baseline_short_coverage': target.mae_short_ticks.le(baseline_short).astype(float)})
        means = frame.groupby('session').mean()
        risk_rows.append({'horizon_minutes': int(h), **means.mean().to_dict()})
        for metric in ['endpoint_absolute_error', 'endpoint_squared_error', 'interval_score', 'long_pinball', 'short_pinball']:
            comparisons.append({'horizon_minutes': int(h), 'metric': metric,
                'difference': 'mixture minus volatility-scaled TRAIN distribution; negative favours mixture',
                **block_ci(means['mixture_'+metric]-means['baseline_'+metric])})
        for metric in ['endpoint_absolute_error', 'endpoint_squared_error']:
            comparisons.append({'horizon_minutes': int(h), 'metric': metric,
                'difference': 'mixture minus zero price-change forecast; negative favours mixture',
                **block_ci(means['mixture_'+metric]-means['zero_'+metric])})
        times = g.index.tz_convert('America/New_York').strftime('%H:%M')
        results[str(h)] = {
            'origins': len(g), 'sessions': int(g.session_id.nunique()),
            'observed_class_counts': {str(k): int(v) for k,v in g.actual_class.value_counts().sort_index().items()},
            'maximum_class_probability_quantiles': maximum.quantile([0,.5,.9,.99,1]).to_dict(),
            'origins_with_max_probability_over_half': int(maximum.gt(.5).sum()),
            'direction_balance_pp_quantiles': (100*balance).quantile([0,.5,.9,1]).to_dict(),
            'fraction_direction_balance_positive': float(balance.gt(0).mean()),
            'fraction_probability_balance_and_mean_opposite_sign': float((balance*g.endpoint_mean_ticks).lt(0).mean()),
            'endpoint_mean_cents_quantiles': g.endpoint_mean_ticks.quantile([0,.5,.9,1]).to_dict(),
            'raw_endpoint_forecast_actual_correlation': float(g.endpoint_mean_ticks.corr(y)),
            'normalized_endpoint_forecast_actual_correlation': float((g.endpoint_mean_ticks/sigma).corr(y/sigma)),
            'median_neutral_band_cents': float(g.neutral_band_ticks.median()),
            'median_endpoint_interval_width_cents': float((g.endpoint_q90_ticks-g.endpoint_q10_ticks).median()),
            'train_path_count': len(bank['endpoint']),
            'median_effective_scenarios': float(g.effective_scenarios.median()),
            'median_normalized_class_entropy': float(g.predictive_entropy.median()),
            'origin_clock_first': min(times), 'origin_clock_last': max(times)}
        table = daily[daily.horizon_minutes.eq(h)].pivot(index='session', columns='model', values='log_loss').sort_index()
        for baseline in ['train_frequency', 'price_only', 'direct_full']:
            d = table['mixture']-table[baseline]
            stability.append({'horizon_minutes': int(h), 'baseline': baseline, 'sessions': len(d),
                'days_mixture_better': int(d.lt(0).sum()), 'mean_difference': float(d.mean()),
                'median_difference': float(d.median()), 'first_24_days_mean': float(d.iloc[:24].mean()),
                'last_25_days_mean': float(d.iloc[24:].mean())})
    pd.DataFrame(risk_rows).to_csv(HERE/'risk-baseline-diagnostics.csv', index=False)
    pd.DataFrame(comparisons).to_csv(HERE/'risk-baseline-comparisons.csv', index=False)
    pd.DataFrame(stability).to_csv(HERE/'day-level-diagnostics.csv', index=False)
    payload = {'status': 'post-hoc descriptive analysis of already inspected TEST; not fresh confirmation',
        'method': 'Frozen predictions and TRAIN artifacts only. No refit, new parameters, policy search, or PnL. Risk baseline uses session-weighted TRAIN outcomes scaled by the same known origin volatility.',
        'interval_score_alpha': .2, 'pinball_quantile': .8,
        'uncertainty': 'Same 2000 circular five-session block replications and seed 1729 as original. Multiple exploratory comparisons; no multiplicity adjustment.',
        'correlations': 'Pooled overlapping origins, descriptive and not independent-sample significance tests.',
        'input_sha256': hashes, 'horizons': results}
    (HERE/'edge-diagnostics.json').write_text(json.dumps(payload, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==hashes[p.name] for p in inputs)
    print(json.dumps({'status': 'PASS', 'frozen_inputs_unchanged': True, 'horizons': list(results), 'risk_comparisons': len(comparisons)}))


if __name__ == '__main__':
    main()
