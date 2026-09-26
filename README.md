# Momentum

A research project for an intraday CGB duration indicator over 60, 120 and 240 minutes. It contains the model, notebook, mathematical reasoning, iteration protocol, lessons and paper catalog. **Market inputs remain blank; no predictive edge has been established.**

## Start here

| Purpose | Open |
|---|---|
| Inspect the executed synthetic CAD/US bond ecosystem | [Full simulation report](research/cgb_ecosystem/REPORT.md), [results notebook](research/cgb_ecosystem/simulation-results.ipynb) and [experiment code](research/cgb_ecosystem/simulation/structured_simulation.py) |
| Add data and improve the model | [Iteration and improvement](docs/12-iteration-and-improvement.md) |
| Understand each design choice | [First-principles derivation](docs/10-structural-model-derivation.md) |
| Run the current implementation | [Notebook](notebooks/cgb-conditional-paths.ipynb) and [operating guide](docs/11-running-and-testing.md) |
| Study the underlying ideas | [All 47 lessons](docs/08-the-intellectual-story-and-all-lessons.md), [math walkthrough](docs/07-understanding-the-framework.md), [repair checklist](docs/09-departures-and-repair-checklist.md) |
| Read source material | [English lessons and essays](logic/README.md), [arXiv catalog](papers/arxiv-catalog.md) |
| Inspect evidence and earlier decisions | [Verification record](audits/implementation-verification.md), [source audit](audits/source-audit.md), [historical archive](archive/README.md) |

## Contents

| Folder | Contents |
|---|---|
| `docs/` | Current derivation, measurement contract, operating/iteration guides and source teaching |
| `notebooks/` | Current conditional-path notebook with blank market inputs |
| `src/momentum/` | Measurements, states, path forecasts, frozen deployment, CLI and separate execution accounting |
| `tests/` | Causality, probability, deployment and accounting software checks; no empirical performance claim |
| `audits/` | Source inspection, lesson coverage, software verification and math checks |
| `papers/` | arXiv catalog and the earlier complete research-note union |
| `logic/` | English teaching guide and six complete English physics essays |
| `archive/` | Earlier design notes, baseline notebook and Step 1 reference code |
| `data/` | Input instructions; no market dataset |
| `research/cgb_ecosystem/` | [Complete simulation study](research/cgb_ecosystem/README.md): hypotheses, notebook, report, generator, exact model snapshot, raw histories, fitted models, forecasts, ledgers, plots and audits |

## Mathematics and code

All explanatory documents are Markdown. Guides 07–10 and 12 embed rendered vector equations from `assets/math`; their LaTeX is preserved in SVG metadata. Keep the assets with the Markdown files. Older documents use dollar delimiters and need a math-capable preview. No HTML deliverable or notebook-generation script is included.

The current notebook imports the canonical package to avoid implementation drift. Install it with `python -m pip install -e .`; `requirements-tested.txt` records the tested dependency versions. A notebook environment is needed to open `.ipynb` interactively. CPU is the default; CUDA is an explicit configuration choice.

Run `python -m unittest discover -s tests -p test_scenarios.py -v` for the new model and `python tests/verify_pipeline.py` for the earlier measurement/accounting regression checks. See [the verification record](audits/implementation-verification.md) for exact claims and outcomes. The separately labeled synthetic ecosystem experiment now lives together in [research/cgb_ecosystem](research/cgb_ecosystem/README.md); it supplies no real-market validation and does not populate the blank live-market notebook inputs.

The `momentum train`, `momentum forecast` and `momentum show` commands fit an identified experiment, publish a frozen forecast, and read the saved result. The operating guide provides schemas and examples. Live-market datasets and ordinary local fit outputs are ignored by Git. The explicitly published synthetic study includes its fitted artifacts and synthetic inputs.

## Research boundary

The current model learns direct horizon-specific transitions among five descriptive states, fits future-state and future-price XGBoost heads, and combines three distributions over TRAIN historical paths. Direction, expected movement and adverse excursion come from one coherent distribution per horizon. CAL fits mixture weights; TEST supplies subsequent diagnostics. Separate horizons do not form a single joint path process.

The intended default experiment includes CGB, US duration and the Canadian curve. Optional flow, OIS, swaps, forwards, book, VWAP and context need sufficient real coverage. Bid/ask costs use prices in a separate accounting layer. No real-data fit, predictive edge, full event-level L2 reconstruction, automatic retraining or live order execution is claimed. Local scale transfer and state relevance remain falsifiable market hypotheses.
