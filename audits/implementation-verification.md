# Conditional-path implementation: evidence and limits

This record concerns the independent implementation described in [the derivation](../docs/10-structural-model-derivation.md), not a claim that it reproduces the source framework's private judgment or proves a trading edge. Market inputs remain blank. The software exercise is deterministic and synthetic.

## What changed following the source review

The earlier baseline used a local-drift model and endpoint classifiers. The new main experiment uses observed states, direct horizon-specific state forecasts and complete empirical future paths. It preserves the account's CGB target and existing causal measurements. All probability, endpoint and adverse-excursion summaries now derive from the same scenario mass within a horizon.

The source's 22 states, seven manually specified matrices, score squaring and Monte Carlo grammar propagation are not dependencies. The five-state count follows two directional observations plus balance; its thresholds remain engineering conventions. Direct horizon transitions avoid claiming that this reduced description is a sufficient homogeneous Markov state. Exact scenario sums avoid adding sampling error to a known finite distribution.

Source teaching and coverage evidence remain in [the source audit](source-audit.md), [the lesson review evidence](lesson-review-evidence.md), and guides 07–09. All 47 lesson files were inventoried and their scope recorded. The core essays and relevant notebook cells received deeper review; this is not a claim of line-by-line verification of every paper in the catalog. The [gitos lenses](https://github.com/wizzo-gmb/gitos-lenses) inform the research ordering and evidence discipline; their methods do not certify this particular model.

## Decision-to-code trace

| Requirement | Implementation | Evidence or explicit boundary |
|---|---|---|
| Receiver-time observations | Existing panel and feature layer | Prefix and late-revision checks |
| Distinguish state from outcome | `states.py`, horizon target construction | Current state is past-only; labels mature later |
| Keep pressure separate from price | Classified flow and response columns | Missing/unclassified/late flow is unavailable |
| Learn state relationships | `transition_distribution`, future-state tree | TRAIN-only direct horizon rows, shrinkage prior |
| Preserve path information | Per-horizon normalized TRAIN bank | Endpoint and adverse-excursion path identities |
| Coherent probabilities | Conditional mass redistribution and convex expert mixture | Class sums and scale identities |
| Do not tune using TEST | TRAIN/CAL/TEST interfaces | TEST-price mutation leaves banks, trees and weights unchanged |
| Reject absent enabled environment | Module coverage gates | Explicit missing-module test |
| Respect account's session | Complete path targets and live horizon guard | Late-session unavailability test |
| Freeze a reproducible artifact | Hash-checked models, arrays and configuration | Saved/loaded forecasts exactly agree |
| Preserve forecast history | No-overwrite publication; read-only consumer | Overwrite attempt rejected |
| Evaluate only known outcomes | Matured feedback | One-hour outcome appears only after its horizon completes |
| Bid/ask economics | Existing `execution.py` | Spread counted once in a known accounting example |

## Commands and results

The new model is exercised with `python -m unittest discover -s tests -p test_scenarios.py -v`. **All 14 tests passed in the final run** (49.489 seconds), including all three horizons, future mutation, exact frozen save/load, history revision rejection, maturity timing, unclassified/delayed flow, missing selected environment, late-session horizons, and the no-data CLI. The test fixture reduces tree count and minimum session gates explicitly for software execution; it does not estimate the default model on market data.

The existing `python tests/verify_pipeline.py` regression exercise passed. It checks source prefix invariance, revision semantics, horizon/partition endpoints, all three horizons executing, frozen mid-session inference, late-session unavailability, probability normalization/idempotent baseline pooling, and spread counted once.

The current notebook validates against the notebook schema. Every code cell executes with the blank inputs, reports awaiting data and writes no model artifact. The package installs successfully in editable mode; all package modules compile. The CLI returns awaiting data and writes no artifact when its required files are absent. Its initial status-reporting syntax error was found by the separate entry-point check, fixed, and covered by the added CLI regression test. Tests and notebook validation use local packages; the notebook-generation and rendering helpers remain outside the project.

All local Markdown links resolve. The three older machine-specific source links now point to the English lesson files inside the project. No HTML deliverables are present.

The equations in the teaching guides and current derivation are rendered SVG images embedded in ordinary Markdown. The source LaTeX is preserved in the images. [The math check](teaching-math-check.md) records parsing and preview verification; it does not prove the equations' financial applicability.

## What these checks do not establish

- They do not establish predictive accuracy, profitability, statistical significance or superiority to the source implementation.
- They do not establish local scale transfer or that a historical path bank covers an unseen event.
- Equal-session loss weights do not make overlapping paths independent. Effective scenario count is not effective sample size in days.
- One chronological split is not repeated purged walk-forward validation. Exposure-preserving nulls and event-matched controls remain actual research work.
- The new suite exercises the complete path machinery using an explicitly reduced CGB-only fixture. It checks rejection of missing default environment inputs, not a fitted real CAD/US/curve relationship.
- Full L2 event reconstruction, queue replenishment, passive fills, cash/futures risk equivalence, and automatic refitting are not implemented.
- Hash validation checks consistency against the supplied manifest. It is not cryptographic publisher authentication. Dependency versions are recorded, not compatibility-certified.
- No real model artifact or broker connection has been created. The repository contains the means to run a declared test once actual data is supplied.

## Source attribution versus independent decisions

We retain environment before prediction, explicit references, state-aware questions, pressure/response reasoning and versioned feedback. We independently derive the CGB path target, receiver-time contracts, five-state observation, empirical transition shrinkage, group-aware similarity, conditional path redistribution, convex calibration and deployment interface. The numerical windows, cutoffs and regularizers are labeled provisional in the derivation's parameter ledger. They are not represented as mathematical necessities or the source author's recommendations.

## Documentation and organization update

The [iteration protocol](../docs/12-iteration-and-improvement.md) combines data onboarding, failure diagnosis, framework-derived questions, experiment records and subsequent evaluation. Proposed additions are distinguished from implemented behavior.

Seven earlier experiment files were moved into the [archive](../archive/README.md). Three appendices, totaling 679 lines, were confirmed identical to their canonical audit/contracts after heading normalization and replaced with links. Source authorship remains in provenance and the original essays; repeated personal references were removed from the model explanations.

Verification for this documentation-only update: all local Markdown and notebook links resolve; both notebooks validate and their code cells compile; the archived notebook's code cells are unchanged; active package, tests and dependency files are unchanged. The five rendered guides contain 142 mathematical expressions, all parsed and loaded in light and dark previews without formula code boxes. The existing 14-test result above remains the latest model-suite run; it was not presented as a new market-data evaluation.
