# Earlier experiments and decisions

These files preserve the research history. Active work starts with [the current derivation](../docs/10-structural-model-derivation.md), [current notebook](../notebooks/cgb-conditional-paths.ipynb), and [iteration protocol](../docs/12-iteration-and-improvement.md).

| File | Historical role |
|---|---|
| [Earlier model](docs/01-model.md) | Filtered drift, seven phases, direct outcome heads and logarithmic pooling |
| [Step 1](docs/02-step-1.md) | Initial system, exposure and information contract |
| [Research context](docs/03-research-context.md) | Initial pressure, response and continuation hypotheses |
| [Decision log](docs/04-decision-log.md) | Alternatives considered for the earlier baseline |
| [Earlier predictor contract](docs/06-predictor-contract.md) | API and fitting details for the baseline |
| [Baseline notebook](notebooks/cad-duration-momentum.ipynb) | Self-contained earlier implementation with blank data inputs |
| [Step 1 reference code](reference/cad_momentum_step01.py) | Selected initial definitions and consistency checks |

The three duplicated appendices in the earlier model were replaced with links to their canonical audit and contracts after exact text comparison. Unique lessons, research papers, mathematics and executable source were retained. Older files use math delimiters and require a math-capable Markdown preview.

The baseline package module remains in `src/momentum/model.py`: the current model uses its target, split and scoring helpers, and the baseline remains a useful comparator. Archiving the notebook does not remove those dependencies or alter the current estimator.
