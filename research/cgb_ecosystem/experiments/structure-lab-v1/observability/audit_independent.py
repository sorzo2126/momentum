"""Reproduce the bounded independent audit without changing the experiment.

Run from any directory: python path/to/observability/audit_independent.py
Only independent-audit.json beside this file is written. The experiment's
protocol, source and results remain unchanged. No simulation is rerun.
"""
from pathlib import Path
import hashlib
import json
import runpy

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    references = [
        'run.py', 'protocol.json', 'results/verification.json',
        'results/martingale-worlds.npz', 'results/martingale-ledger.csv.gz',
        'results/twins.csv.gz',
    ]
    hashes_before = {name: sha256(ROOT / name) for name in references}
    verified = json.loads((ROOT / 'results/verification.json').read_text())
    protocol = json.loads((ROOT / 'protocol.json').read_text())
    assert hashes_before['run.py'] == verified['code_sha256']
    assert hashes_before['protocol.json'] == verified['protocol_sha256']

    # Import functions only. The run.py main guard prevents experiment execution.
    implementation = runpy.run_path(str(ROOT / 'run.py'), run_name='audit_only')
    phi = protocol['pressure_phi_per_minute']
    q = protocol['pressure_innovation_sd_ticks_per_minute']
    r = protocol['return_noise_sd_ticks']
    proxy_sd = 0.1
    kalman_checks = []
    for delay in (0, 5, 30):
        world = implementation['generate'](8, 30, 1729, phi, q, r)
        returns, proxy = implementation['observations'](world, delay, proxy_sd)
        means, variances = implementation['kalman'](
            returns, proxy, delay, proxy_sd, phi, q, r)
        for t in (0, 1, 8, 20):
            # Direct conditioning on every received measurement is an independent
            # matrix calculation, with no sequential-filter recursion.
            signal_times = np.array(list(range(t)) + [j - delay for j in range(t + 1)])
            measured = np.column_stack(
                [returns[:, j] for j in range(1, t + 1)]
                + [proxy[:, j] for j in range(t + 1)])
            prior = q * q / (1 - phi * phi)
            covariance = (
                prior * phi ** np.abs(signal_times[:, None] - signal_times[None, :])
                + np.diag([r * r] * t + [proxy_sd * proxy_sd] * (t + 1)))
            cross = prior * phi ** np.abs(t - signal_times)
            coefficient = np.linalg.solve(covariance, cross)
            reference_mean = measured @ coefficient
            reference_variance = prior - cross @ coefficient
            mean_error = float(np.max(np.abs(reference_mean - means[:, t])))
            variance_error = float(abs(reference_variance - variances[t]))
            assert mean_error < 1e-10 and variance_error < 1e-10
            kalman_checks.append(dict(
                delay_minutes=delay, minute=t, worlds=8,
                maximum_mean_error=mean_error, variance_error=variance_error))

    loading_checks = []
    for horizon in (1, 2, 60, 120, 240):
        loading, variance = implementation['loadings'](horizon, phi, q, r)
        powers = phi ** np.arange(horizon)
        reference_loading = float(powers.sum())
        reference_variance = (
            q * q * sum(float(powers[:horizon - i].sum()) ** 2
                        for i in range(1, horizon)) + horizon * r * r)
        loading_error = abs(loading - reference_loading)
        variance_error = abs(variance - reference_variance)
        assert loading_error < 1e-10 and variance_error < 1e-9
        loading_checks.append(dict(
            horizon_minutes=horizon, mean_loading_error=loading_error,
            innovation_variance_error=variance_error))

    with np.load(ROOT / 'results/martingale-worlds.npz', allow_pickle=False) as archive:
        prices = archive['price_mid_ticks']
    ledger = pd.read_csv(ROOT / 'results/martingale-ledger.csv.gz')
    world = ledger.world.to_numpy(int)
    decision = ledger.decision_minute.to_numpy(int)
    exit_time = ledger.exit_minute.to_numpy(int)
    past = prices[world, decision] - prices[world, decision - 30]
    direction = ledger.direction.to_numpy()
    expected_direction = np.where(
        ledger.policy == 'always_long', 1,
        np.where(ledger.policy == 'always_short', -1,
                 np.sign(past) * np.where(ledger.policy == 'past_30min_momentum', 1, -1)))
    assert np.array_equal(direction, expected_direction)
    gross = direction * (prices[world, exit_time] - prices[world, decision])
    mc = protocol['martingale']
    extra = mc['roundtrip_extra_slippage_ticks'] + mc['roundtrip_fee_ticks']
    net = direction * (ledger.exit_touch_ticks.to_numpy() - ledger.entry_touch_ticks.to_numpy())
    net -= (direction != 0) * extra
    gross_error = float(np.max(np.abs(gross - ledger.gross_ticks.to_numpy())))
    net_error = float(np.max(np.abs(net - ledger.net_ticks.to_numpy())))
    assert gross_error < 1e-9 and net_error < 1e-9

    twin = pd.read_csv(ROOT / 'results/twins.csv.gz')
    a = twin[twin.branch == 'continuation'].sort_values(['world', 'minute'])
    b = twin[twin.branch == 'reversal'].sort_values(['world', 'minute'])
    shape = (protocol['twins']['worlds'], protocol['twins']['duration_minutes'] + 1)
    first_differences = {}
    for column in ('pressure_truth', 'received_return', 'received_proxy', 'forecast60_mean_ticks'):
        unequal = (a[column].to_numpy() != b[column].to_numpy()).reshape(shape)
        first_differences[column] = int(np.flatnonzero(unequal.any(0))[0])

    hashes_after = {name: sha256(ROOT / name) for name in references}
    assert hashes_after == hashes_before
    result = dict(
        status='PASS', scope='Reproduction of previously reported bounded independent checks only.',
        experiment_files_unchanged=True, source_and_input_sha256=hashes_before,
        audit_code_sha256=sha256(Path(__file__)),
        kalman_direct_gaussian_conditioning=kalman_checks,
        future_sum_moment_checks=loading_checks,
        martingale=dict(
            ledger_rows=len(ledger), past_only_directions_match=True,
            gross_reconstruction_maximum_error_ticks=gross_error,
            touch_net_reconstruction_maximum_error_ticks=net_error),
        twins_first_paired_difference_minute=first_differences,
        interpretation_corrections=[
            'The twin observer is deliberately misspecified throughout, not only after the switch.',
            'First unequal paired input/forecast is not a reliable branch-detection time.',
            'Adjacent martingale blocks are separately liquidated and re-entered even if side is unchanged.',
        ],
        checks_requiring_source_inspection=[
            'TRAIN-only ridge scaling/coefficient and independent CAL residual-variance fitting.',
            'Oracle excludes future innovations; filter consumes received time columns only.',
            'Confidence intervals aggregate by independent world rather than overlapping origin.',
        ])
    output = ROOT / 'independent-audit.json'
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(dict(status=result['status'], output=str(output),
                          kalman_cases=len(kalman_checks), ledger_rows=len(ledger),
                          experiment_files_unchanged=True)))


if __name__ == '__main__':
    main()
