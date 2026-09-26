# Real-market momentum research: SPY and basket exposures

This folder is an independent real-data experiment. It uses the existing Fractal EODHD credential to retrieve SPY bars, refits the momentum architecture on SPY, and evaluates frozen forecasts. No CGB weights or market data are used or modified.

Start with the [Fractal source deep dive and redesign](FRACTAL-DEEP-DIVE.md), [trading-edge review](EDGE-REVIEW.md), [full report](REPORT.md), [notebook](SPY-real-data-study.ipynb) or [basket design](basket-design.md).

The first SPY result is modest: the one-hour mixture slightly improves on a constant class-frequency forecast, trails price-only, and has uncertainty intervals spanning no improvement. The chart works on real data; this test does not establish an edge.

## Reproduce

Install the versions in [requirements-tested.txt](requirements-tested.txt), plus the repository package. Run from this folder:

```powershell
python fetch_data.py --fractal-dir "C:/path/to/fractal-x"
python run_study.py --raw private/raw/SPY.US-5m.json
```

Alternatively set `EODHD_API_KEY` in your local environment. The adapter reads only the existing key and never writes it into study artifacts. Raw vendor data, fitted models, individual forecasts and chart data live in the ignored `private/` directory. The committed UI contains source rather than embedded market rows.

The [protocol](protocol.json) fixes the period, quality rules, session split, features, horizons, metrics and comparison policy. Do not overwrite the protocol to optimise the saved TEST result. Create a new experiment identity and preserve a fresh holdout.

## Contents

- [REPORT.md](REPORT.md): results, figures, limitations and interpretation.
- [run_study.py](run_study.py): OHLCV adapter, model fitting, baselines, scoring and plots.
- [fetch_data.py](fetch_data.py): credential-safe cached EODHD download.
- [localevents.py](localevents.py): local causal range-event observer.
- [ui/](ui/UI.md): real-data chart source and browser tests.
- [AUDIT.md](AUDIT.md): independent numerical and temporal review.
- [basket-universe.json](basket-universe.json), [basket-design.md](basket-design.md): exact source basket inventory and proposed next experiments; no basket performance claimed.

The full Fractal basket strategy is a different pipeline. This study uses its data connection and explicitly documented ideas, while testing this repository's momentum architecture on new market observations.
