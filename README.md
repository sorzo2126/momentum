# Momentum

An organized research project for a live Canadian duration momentum indicator through CGB, over one to four hours. This folder contains the notebook, reusable code, mathematical explanations, research decisions, source audits, English thesis lessons and paper links. **No market data or fitted market results have been supplied.**

## Start here

Start with [the current first-principles derivation](docs/10-structural-model-derivation.md), [the runnable notebook](notebooks/cgb-conditional-paths.ipynb), and [the operating guide](docs/11-running-and-testing.md). Every source-inspired idea is tied to an observable quantity or explicitly retained as a hypothesis. The source's numerical state grammar, transition matrices and score-squaring rule are not copied into the model.

For the teaching background, read [the intellectual story and all 47 source lessons](docs/08-the-intellectual-story-and-all-lessons.md), [the mathematical walkthrough](docs/07-understanding-the-framework.md) and [the departures and repair checklist](docs/09-departures-and-repair-checklist.md). Those three guides review the earlier baseline; document 10 records the resulting independent redesign.

1. Read [the decision record](docs/04-decision-log.md) for the question, alternatives and unresolved issues.
2. Read [the earlier baseline model](docs/01-model.md) for the preceding experiment and implementation appendices.
3. Run [the current notebook](notebooks/cgb-conditional-paths.ipynb). Its market inputs remain blank; Run All reports awaiting data. The [older self-contained notebook](notebooks/cad-duration-momentum.ipynb) is preserved as a separate baseline.
4. Read [the English thesis lessons](logic/lessons.md), then the six full English [physics essays](logic/README.md).
5. Use [the arXiv catalog](papers/arxiv-catalog.md) for actual paper titles, version-specific links and verification dates.

## Contents

| Folder | Contents |
|---|---|
| `docs/` | Full model, Step 1 specification, earlier research context, decisions, measurement and predictor contracts |
| `notebooks/` | Current conditional-path notebook and earlier embedded-code baseline; empty market inputs |
| `src/momentum/` | Measurements, states, path forecasts, frozen deployment, CLI and separate execution accounting |
| `tests/` | Causality, probability, deployment and accounting software checks; no empirical performance claim |
| `audits/` | Exact source-code audit, source inventory, software checks, math checks and link verification records |
| `papers/` | arXiv catalog and the earlier complete research-note union |
| `logic/` | English teaching guide and six complete English physics essays |
| `reference/` | Earlier Step 1 reference code; original Fractal X notebooks are not redistributed here |
| `data/` | Input instructions; no market dataset |

## Mathematics and code

All explanatory documents are Markdown. The teaching guides and current derivation (07–10) embed pre-rendered vector equations from `assets/math`, so ordinary Markdown previews show mathematics without a LaTeX extension. Keep that directory with the files. Original LaTeX is preserved in each SVG's metadata. Older documents use dollar delimiters and need a math-capable preview. A plain-text editor always shows Markdown source. No HTML or notebook-building script is included.

The current notebook imports the canonical package to avoid implementation drift. Install it with `python -m pip install -e .`; `requirements-tested.txt` records the tested dependency versions. A notebook environment is needed to open `.ipynb` interactively. CPU is the default; CUDA is an explicit configuration choice.

Run `python -m unittest discover -s tests -p test_scenarios.py -v` for the new model and `python tests/verify_pipeline.py` for the earlier measurement/accounting regression checks. See [the verification record](audits/implementation-verification.md) for exact claims and outcomes. Synthetic exercises remain inside tests, not notebook inputs or research results.

The `momentum train`, `momentum forecast` and `momentum show` commands fit an identified experiment, publish a frozen forecast, and read the saved result. The operating guide provides schemas and examples. Fitted artifacts and local market data are ignored by Git.

## Research boundary

The current model learns direct horizon-specific transitions among five descriptive states, fits future-state and future-price XGBoost heads, and combines three distributions over TRAIN historical paths. Direction, expected movement and adverse excursion come from one coherent distribution per horizon. CAL fits mixture weights; TEST supplies subsequent diagnostics. Separate horizons do not form a single joint path process.

The intended default experiment includes CGB, US duration and the Canadian curve. Optional flow, OIS, swaps, forwards, book, VWAP and context need sufficient real coverage. Bid/ask costs use prices in a separate accounting layer. No real-data fit, predictive edge, full event-level L2 reconstruction, automatic retraining or live order execution is claimed. Local scale transfer and state relevance remain falsifiable market hypotheses.
