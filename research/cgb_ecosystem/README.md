# CAD / US bond ecosystem simulation

The entire simulation study is collected here: hypotheses, mathematical report, executed notebook, generator, exact model source, raw synthetic histories, fitted models, forecasts, execution ledgers, plots and audits. **These are synthetic experiments with assumed mechanisms and costs, not measured market performance.**

## Read the study

1. [Hypotheses and what the experiments actually test](docs/hypotheses.md).
2. [Complete report](REPORT.md): market construction, bond mathematics, learning model, results, objections and interpretation, with 25 plots and rendered equations.
3. [Executed results notebook](simulation-results.ipynb): all 11 experiments, tables and embedded plots. Download and open locally if GitHub's notebook preview is unavailable.
4. [Results interpretation](docs/results-and-limitations.md).
5. [Reproduction instructions](docs/reproducing.md) and [provenance](docs/provenance.md).

## Everything included

| Location | Contents |
|---|---|
| `docs/` | Hypotheses, interpretation, reproduction and provenance |
| `simulation/` | Generator, cash-flow valuation, plot/report assembly and verification |
| `model_snapshot/momentum/` | Exact eight source files used by the fitted models; study commands load this snapshot |
| `results/` | Every completed run, raw compressed inputs, forecasts, ledgers, fitted models and evaluation tables |
| `figures/`, `equations/` | All 25 plots and 24 rendered vector equations; original LaTeX in `equations/source.json` |
| `reference/`, `example-audit/` | Supplied example notebook unchanged, reproduced arrays and its audit |
| `archive/linear-duration-exploration/` | All files from the incomplete, superseded initial experiment |
| Root CSV files | Cross-experiment metrics, execution accounts, mixture weights, path scores and bond/futures comparisons |
| Root JSON files | Protocol, resolved configuration, verification records, source register and SHA-256 manifest |

The primary study contains three base histories, three pressure-removal controls, one CGB-only ablation and four frozen-model stress experiments. Each full history contains 40 synthetic sessions: 24 TRAIN, eight CAL and eight TEST. Horizons are 60, 120 and 240 minutes. The archived exploratory run is not part of those 11 completed experiments.

The strongest recurring result is at 60 minutes. Longer horizons are less reliable, fast-decay stress produces losses, and missing exit prices prevent a complete P&L claim for one feed-gap book. See the report for all outcomes, including failures and no-trade rows.

## Quick verification

From this folder, with the dependencies in `requirements-tested.txt` installed:

```sh
python -m simulation.verify_bundle
python -m simulation.verify_simulation
```

The first checks the complete file inventory and hashes. The second checks measurement identities, model integrity, execution accounting and historical live replay. It uses the included reference notebook rather than a path on the original researcher's computer. Neither command fits a new model. [Reproduction instructions](docs/reproducing.md) explain how to create a separate new run.

No live feed, broker connection, real-market dataset, HTML deliverable or notebook-generation script is included. Package dependencies are installed normally rather than vendored. All research artifacts, including the synthetic input data and frozen model source, are included in this folder.
