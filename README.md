# Momentum

An organized research project for a live Canadian duration momentum indicator through CGB, over one to four hours. This folder contains the notebook, reusable code, mathematical explanations, research decisions, source audits, English thesis lessons and paper links. **No market data or fitted market results have been supplied.**

## Start here

1. Read [the decision record](docs/04-decision-log.md) for the question, alternatives and unresolved issues.
2. Read [the full mathematical model](docs/01-model.md), including the source-code audit and implementation appendices.
3. Open [the self-contained notebook](notebooks/cad-duration-momentum.ipynb). Its input cells are deliberately blank; Run All defines the implementation and reports awaiting data.
4. Read [the English thesis lessons](thesis/lessons-english.md), then the six full English [physics essays](thesis/README.md).
5. Use [the arXiv catalog](papers/arxiv-catalog.md) for actual paper titles, version-specific links and verification dates.

## Contents

| Folder | Contents |
|---|---|
| `docs/` | Full model, Step 1 specification, earlier research context, decisions, measurement and predictor contracts |
| `notebooks/` | Complete new CAD notebook with embedded implementation and empty data inputs |
| `src/momentum/` | Reusable measurement, modeling and separate execution-accounting modules |
| `tests/` | Deterministic software integration fixture; no empirical performance claim |
| `audits/` | Exact source-code audit, source inventory, software checks, math checks and link verification records |
| `papers/` | arXiv catalog and the earlier complete research-note union |
| `thesis/` | English teaching guide and six complete English physics essays |
| `reference/` | Original six Fractal X notebooks and supporting code, plus the earlier Step 1 reference code |
| `data/` | Input instructions; no market dataset |

## Mathematics and code

All explanatory documents are Markdown. Equations use inline dollar delimiters or display double-dollar delimiters outside code fences. Read them in a Markdown preview that supports LaTeX math, such as Jupyter's Markdown renderer. A plain-text editor naturally shows the equation source. No HTML or notebook-building script is included.

The notebook is self-contained. The same implementation is also organized as an importable Python package. Install it into your chosen environment with `python -m pip install -e .`; `requirements-tested.txt` records the library versions used for the software checks. A notebook environment is needed to open `.ipynb` interactively. The current code uses CPU by default; CUDA is an explicit configuration choice.

Run `python tests/verify_pipeline.py` for the deterministic software exercise. It checks timing, prefix consistency, target eligibility, inference and accounting. It does not demonstrate alpha or generate a market backtest. The synthetic exercise remains inside the verification script, not in notebook inputs or research results.

## Research boundary

The current forecast combines a fitted local-drift model and XGBoost heads for actual future CGB movement. Current descriptive phases are distinct from future labels. Bond and futures costs use prices in a separate accounting layer. The core CGB baseline is implemented; additional US, CAD futures, curve, OIS, swaps, forwards, book, VWAP and scalar context modules are explicitly enabled after their coverage is inspected.

The original reference notebooks retain their historical outputs and assumptions. They are supplied for reading and audit, not as certified results or dependencies of the new notebook. The source audit identifies material timing and interpretation issues. New CAD work is clearly distinguished from Karim's original implementation.
