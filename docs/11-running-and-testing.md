# Run the conditional CGB path experiment

Start with [the derivation](10-structural-model-derivation.md), then open [the current notebook](../notebooks/cgb-conditional-paths.ipynb). Its market-input cells are blank. Run All reports `awaiting_data` until real inputs are supplied. It imports the canonical package so notebook and command-line forecasts use the same implementation.

The older [CAD notebook](../archive/notebooks/cad-duration-momentum.ipynb) remains as an explicitly separate baseline with its embedded code. It does not run the new path model. The two experiments must not be mistaken for interchangeable versions of the same estimator.

## Install and check

From this project directory, use a Python environment with the dependencies in `pyproject.toml`. `requirements-tested.txt` records the versions used for the software exercise.

```powershell
python -m pip install -e .
python -m unittest discover -s tests -p test_scenarios.py -v
python tests/verify_pipeline.py
```

The first suite checks the new path model; the second checks the existing causal panel, baseline and execution accounting. Synthetic inputs live only in the tests. Neither command establishes market performance. A notebook environment is required for interactive `.ipynb` use; the command-line interface does not require one.

## Exact input files

Place the actual adapter outputs in a local directory such as `data/live`. That directory is ignored by Git. Every timestamp needs a timezone. Decimal prices, yield basis points, log-price basis points and monetary units are distinct.

| File | Required columns | Meaning |
|---|---|---|
| `quotes.csv` | `instrument, contract, event_time, available_at, bid, ask` | Atomic two-sided quotes; optional `bid_size, ask_size` |
| `sessions.csv` | `session_id, open_time, close_time` | Explicit nonoverlapping research sessions and allowed horizon close |
| `rates.csv` | `instrument, event_time, available_at, rate_bp` | Optional observed rates already converted to basis points |
| `trades.csv` | `trade_id, instrument, contract, event_time, available_at, price, size` | Optional CGB trade tape for VWAP; add `aggressor` for signed pressure |
| `context.csv` | `instrument, event_time, available_at, value` | Optional positive scalar SPX/VIX observations |

Quote aliases are `CGB`, `US10`, `CGZ`, `CGF`, and optionally actual two-sided `SPX`/`VIX` instruments. Prefer the scalar context table for index values; do not manufacture bid and ask. Use one representation per context instrument. `US10` is the chosen observed US duration proxy, not an inferred cross-market contract mapping.

Rates aliases are `CAD2Y`, `CAD5Y`, `CAD10Y`, `OIS1Y` through `OIS5Y`, `SWAP1Y` through `SWAP5Y`, `FWD1Y1Y` and `FWD2Y1Y`. Negative rates are valid. Contract identifiers must describe actual fixed-contract quote series. Continuous adjusted futures prices are not executable contract quotes.

Trade `aggressor` is +1 for buyer-initiated, -1 for seller-initiated, and 0 for unknown. It must come from a declared feed or upstream classification procedure. The code does not infer it from future prices. Duplicate trade IDs, ambiguous corrections and invalid trade sizes are rejected. Upstream tape completeness, cancellations and sequence gaps still need a real feed adapter. Supplying a nonempty tape implies complete coverage of its declared replay interval; the current schema has no independent heartbeat proving that assumption.

See [the detailed measurement contract](05-feature-contract.md) for each base transformation and freshness rule. The new model excludes the baseline's seven `phase_` columns and builds its own five observed states. Its signed-flow and recovery contracts are in [the derivation](10-structural-model-derivation.md).

## Select an experiment before fitting

The new notebook and CLI default to `cgb`, `us`, `curve`. This is the intended environmental experiment. Missing enabled-module training coverage produces an explicit ineligible status rather than silently falling back to CGB alone. Use an explicit configuration to run a reduced baseline or add modules.

Available base modules are `cgb`, `us`, `curve`, `cad_futures`, `ois`, `swaps`, `forwards`, `book`, `vwap`, and `context`. Signed-flow model features activate only if the training period contains the minimum configured number of sessions with valid classified flow. Later arrival of a new flow feed does not change a frozen model's feature contract; a new experiment is needed to train on it.

A local configuration file can contain `research` and `scenario` objects whose keys match the corresponding dataclasses. For example, to declare the smaller CGB-only study:

```json
{
  "research": {
    "feature_modules": ["cgb"],
    "horizons_minutes": [60, 120, 240],
    "min_train_sessions": 10,
    "min_cal_sessions": 3,
    "min_test_sessions": 3
  },
  "scenario": {
    "decision_step_minutes": 5,
    "neighbor_count": 64,
    "trees": 100,
    "tree_depth": 2
  }
}
```

Changing the feature set, clocks, state thresholds, forecast horizon or model parameters defines a new experiment. Defaults are initial engineering choices. Do not choose whichever setting happens to win the existing TEST slice and report that slice as untouched evidence.

## Train, then publish a frozen forecast

The timestamps below are examples of command syntax, not supplied market data or a recommended operating session. Replace them with explicit receiver cutoffs appropriate to the actual files.

```powershell
momentum train --data data/live --as-of "2026-09-23T20:00:00Z" --output runs/research-001
momentum forecast --artifact runs/research-001 --data data/live --as-of "2026-09-24T15:00:00Z" --output runs/readings/20260924-1500.json
momentum show runs/readings/20260924-1500.json
```

Append `--config path/to/config.json` to `train` for an explicit alternative. `python -m momentum.cli` accepts the same subcommands after installation.

Training with missing quote/session files returns `awaiting_data` and writes no fitted artifact. Insufficient eligible history returns a reason and exit code 2. Ready or partially ready fits are saved; each unavailable horizon retains its reason. A successful fit is a software/data-eligibility result, not authorization to trade.

Forecasting requires the complete receiver-time replay from the saved history origin. The calibration prefix must match its saved hashes. Correcting that historical prefix or changing source code requires a new versioned run. Current observations after that prefix may change normally. Each prediction names its actual five-minute decision time, and a horizon extending beyond the supplied session close is unavailable.

The CLI deliberately does not schedule itself. Run the forecast command from an external data process after the selected cutoff if a live feed is later integrated. Runtime is a full-history batch replay; this version is an auditable research deployment, not a measured low-latency streaming service.

## Artifact contents and lineage

| Artifact | Purpose |
|---|---|
| `manifest.json` | Run UUID, contract version, state-series hash, dependency versions, code hashes and file hashes |
| `deployment.json` | Frozen settings, feature list, history origin, CAL cutoff, model metadata and state-mixture weights |
| `bank-H.npz` | TRAIN-only normalized paths, similarity coordinates, state/endpoint groups, transition and expert weights |
| `state_head-H.json`, `price_head-H.json` | Fitted XGBoost models when more than one training class exists |
| `state_journal.csv` | Observed states through the calibration boundary; the hash is calculated on the in-memory canonical frame |
| `test_metrics.csv`, `evaluation.json` | Endpoint probability/error metrics and adverse-excursion quantile diagnostics |
| `test-predictions-H.csv` | Held-out path forecasts for the horizon |
| `per_session-*`, `pointwise_losses-*`, `reliability-*` | Reconstructable TEST diagnostics by expert and horizon |
| Separately saved live JSON | Frozen run lineage and published readings; existing prediction files cannot be overwritten |

The live-reading consumer only reads saved JSON. It does not recalculate a state, refit a tree or access the feed. The loader validates hashes against the supplied manifest and checks local package source by default. These checks detect accidental alteration relative to the manifest; they are not a digital signature authenticating an untrusted publisher. Dependency versions are recorded, not independently verified for compatibility.

The feedback function is available as `matured_feedback(predictions, panel, features, config, as_of)`. Supply preserved predictions and a receiver-time panel. It returns only horizons whose complete outcomes are known. It performs no parameter update. Persist the returned ledger separately if using it operationally.

## What to inspect after real data arrives

First inspect coverage, clocks, missingness, contract boundaries, state occupancy and counts by session. Then compare the mixture with each individual expert and the TRAIN frequency prior on the same TEST rows. Read per-session losses and reliability tables before averaging away the days. Examine adverse-excursion quantile coverage and loss; an endpoint score alone cannot validate the path shape.

The implementation uses one chronological split. It does not yet establish repeated walk-forward stability, permutation significance, a persistence-only benchmark, event-matched controls, a capacity model or a net trading return. Use [the iteration protocol](12-iteration-and-improvement.md) to choose the next experiment from observed failures, with a declared question, comparator and rejection condition.

## File-to-reason map

| File | Decision it implements |
|---|---|
| `features.py` | What was measurable, in which units, at each receiver time |
| `states.py` | A compact description of observed motion, optional pressure/response and completed recovery events |
| `scenarios.py` | TRAIN conditional paths and heads, CAL pooling, untouched TEST reporting, future-path summaries and matured feedback |
| `deployment.py` | Freeze an identified experiment and preserve its lineage |
| `cli.py` | Explicit local training, inference and read-only consumption |
| `execution.py` | Separate price-side accounting for a proposed trade |
| `tests/test_scenarios.py` | Counterexamples to timing, support, probability and deployment claims |
| `tests/verify_pipeline.py` | Earlier measurement, baseline and accounting regression checks |

No notebook-generation script, HTML report, fabricated market input or automatic broker execution is part of this project.
