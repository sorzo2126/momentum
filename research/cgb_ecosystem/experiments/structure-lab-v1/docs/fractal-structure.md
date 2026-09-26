# Fractal X and the CGB momentum indicator: the actual structural relationship

This is a source-code comparison for a trader decision-support product. It uses the completed thesis review and newly inspects the deployable source contract and important notebook functions. It does not claim access to the author's private thoughts. Statements about what his framework would ask are interpretations tied to its written construction.

The current CGB work is a promising research prototype with a particularly encouraging one-hour result in its designed synthetic environment. It is close to Fractal X in the separation of observation, prediction, structured futures, artifacts and presentation. It is substantially different in its state system, probability construction, target exposure and timescale. No honest percentage describes that relationship. Reproducing more of the original engine is not itself a readiness criterion.

## Evidence used before deciding

**Files consulted:** the source repository's `0.1 AGENTS.md`, all of `0 README_MODEL.md`, code-cell inventory for notebooks 1–6, selected actual functions in notebooks 5 and 6, and the CGB `model_snapshot/momentum/{states,scenarios,deployment,cli}.py`. The source location is `C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main`. Existing thesis synthesis and saved-result evidence are in [the completed review](../../../docs/thesis-review/REPORT.md), [the research plan](../../../docs/thesis-review/research-plan.md) and [fitted weights](../../../fitted-weights.csv).

**Sections used:** the six-stage contract; notebook 5's observed graph, native XGBoost weighting, sequential Monte Carlo, official posterior and cybernetic diagnosis; notebook 6's read-only loader, current signal, table construction and chart. Cell indices below are zero-based JSON notebook indices; line numbers are within that cell's source.

**Logic extracted:** the original system constructs a persistent observed condition, asks how it changes, combines future evidence with a path structure, and preserves one official output for downstream consumers. It separates several diagnoses from active control. The CGB adaptation should preserve that separation and derive its own financial meaning.

**Decision:** use the original architecture to organise a transparent intraday continuation instrument. First establish which existing components contribute; then add structure that discriminates unfinished adjustment, completed repricing and changing capacity.

**Uncertainty:** the supplied Fractal X checkout contains source and theses, but no `STAGE3_OUT` directory or deployed-output database was available in the inspected root. Comments and the README call the model deployable and mention historical performance; this comparison does not independently verify those performance claims. It does verify the inspected code paths. The earlier complete thesis review provides corpus coverage; this focused update does not claim to reread all 47 papers.

## What is retained, adapted, and still missing

| Layer | Fractal X implementation | CGB implementation | Appropriate next decision |
|---|---|---|---|
| Economic object | Daily selected buy/sell universe and a constructed beta spread | Outright Canadian duration through CGB, with US duration and curve context | Keep outright CGB as the target. Common US-driven movement remains useful movement. |
| Reference | Constructed spread, deformation, coupling and fragility | Lagged CAD–US relationship and common/local movement coordinates | Test reference failure and changing propagation; never silently turn the account into a hedged relative-value trade. |
| Observation | Persistent sequential eleven-tag leg automaton, two blocks, separate instantaneous market observer | Five price states, state age, pressure/response and recovery observations | Ask which distinctions predict continuation versus exhaustion. Five or eleven states should follow that answer. |
| Memory | One 252-day graph memory reused by head, path dynamics and other channels | Rolling features, state age, recovery history, historical path neighbourhood | Match memory to intraday adjustment duration. A 252-day value is a source-specific timescale, not a transferable constant. |
| ML target | Future observed leg tag at horizons one through five daily bars | Future five-state condition plus direct endpoint price class at 60, 120 and 240 minutes | Retain direct price and path scoring. Evaluate state anticipation separately from persistent-state recognition. |
| Structural law | Seven 22-by-22 matrices composed using training counts, frontier and spread information | Smoothed learned state-transition distribution | Derive candidate laws from inventory, constraints, response and timing. Compare their predictions before selecting a law family. |
| Future paths | Sequential simulated price paths move through a leg cycle; horizon histograms enter the posterior | Historical normalised price paths reweighted by state/class and local neighbourhood | Empirical paths are a sensible small-data construction. Test path transportability, support and shared-prefix consistency. |
| Official probability | Sequential MC, composed structure, frontiers, temperature and selected transition factors enter an amplitude-squared normalisation | CAL-selected convex combination of three empirical-path experts | These are different probability constructions. Compare useful consequences under identical information and scoring. |
| Cybernetic learning | Structural and memory-derived native training row weights are active | Session-balanced training weights; matured outcome records | Add any rare-transition weighting only with calibration checks on the natural distribution. |
| Cybernetic control | Several named interventions record diagnosis while leaving strategy parameters unchanged | Feedback records do not retrain or alter decisions | Monitoring is already a coherent first product. Any later intervention needs a tested response and recovery rule. |
| Output contract | Shared run ID, state hash and version across model, live and signal artifacts | Immutable saved models, hashes, versioned live readings | Preserve and extend identity checks to the actual trader display. |
| Display | Read-only consumer; predicted tag table and observed-tag chart | Read-only live JSON consumer and research reports | Build a read-only horizon strip, price/path panel and evidence ledger. |
| Execution | Raw leg and executable side/position distinguished | Indicator explicitly says `indicator_only_no_orders`; touch-cost benchmarks kept separately | This matches the requested use case. Explain decision relevance without generating an order instruction. |

## What is genuinely active in the original source

Notebook 5, cell 59, `build_transition_graph_tminus1_t`, distinguishes a persistent leg state (`graph_tag_t`) from an instantaneous OHLC observer (`graph_observer_tag_t`). Its state is refined by frontier information, while its block is held during a leg and updated at range states. This is stronger than attaching a new label independently to every bar. Its practical question is whether the current episode is continuing, beginning, weakening or finishing.

Notebook 5, cell 108, `graph_memory_252_from_tags`, constructs past regime fractions, conditional next-tag frequencies and state occupancy. In cell 109, `monte_carlo_leg_propagation`, that memory influences an ambiguous range-to-direction fork. The simulated price process uses historical exponentially weighted drift and volatility; paths cross support/resistance or return toward a moving centroid, and the automaton advances through its phases. The composed structural law can alter the probability that a preliminary move confirms. Frontier observations alter transition timing. This is an explicit construction of possible sequences.

Notebook 5, cell 145, `born_bayes_posterior_by_horizon`, is the official posterior. In the ordinary MC path it consumes horizon-specific MC histograms, the composed structural row, frontier weights, temperature and transition-specific evidence. Agreement between construction evidence and XGBoost changes diffusion temperature. Some evidence applies differently to transition states and persistent states. A legacy helper in cell 85 has a simpler class-conditional construction; using that helper alone to describe the official engine would be wrong.

There are also clear active/diagnostic distinctions:

| Item | Inspected behaviour | Consequence for our adaptation |
|---|---|---|
| `FullCyberneticTradingSystem.adapt`, cell 101 | Diagnoses, records memory and returns the current strategy unchanged | A sophisticated diagnosis is not necessarily a parameter-changing controller. |
| `cyber_diagnose`, cell 102 | Publishes Ashby attenuation/tighten/explore in the trace; comments explicitly exclude threshold/position/bias changes | Publish contradictions and health before adding autonomous reactions. |
| `CyberneticMemory.training_weight_pressure`, cell 99 | Produces a bounded scalar from structural history; excludes trading metrics | Distinguish training adaptation from a live response to recent P&L. |
| `build_xgb_direct_weight_cybernetic_architecture`, cell 115, and training cells 79/146 | Structural row weights feed native training sample weights | This channel actually affects learning. Its numeric gains are implementation choices, explicitly described as architecture hyperparameters. |
| Reachability masks in cell 145 | Used to report out-of-topology mass; not multiplied into the final probability | Do not add hard prohibitions just to imitate a verbal description of sequential states. |
| GAS/FLUIDE amplitude | Excluded from the official posterior amplitude; some underlying channels remain active elsewhere in observation, path construction and execution | Trace the exact downstream effect of each channel rather than calling it globally active or globally dead. |
| `PerformativeFeedback`, cell 98 | Summarises cycle and action statistics | This class does not itself simulate participants reacting to the strategy. |

The transferable discipline is to identify where each mathematical object changes the computation. The source's numerous named objects are not all independent predictive inputs.

## The most consequential departure in the CGB results

All three base one-hour fits allocate essentially all final path-expert weight to the supervised price-class expert. Local historical path weights still operate *within* the predicted endpoint class. Consequently, that expert can supply a useful forecast of magnitude and adverse movement, while the final up/down/neutral probabilities reproduce the price head when the bank contains all classes.

This is not a reason to force the transition expert back into the forecast. It is a reason to ask a sharper question: **does transition structure help predict the path or the moment of failure even when it does not improve endpoint direction?**

The current mixture is selected by endpoint-class log loss. That objective cannot distinguish two experts with the same endpoint-class probabilities but different paths inside each class. An additional claim about path value requires proper path/magnitude/excursion evaluation. It should not be inferred from the attractive language of a state model.

For the trader product, one defensible baseline is therefore the small price head plus class-conditioned empirical paths, with the state observer displayed separately. A more elaborate structural expert earns production responsibility when it improves a predefined quantity on held-out mechanisms and eventually received market data.

## What the framework would ask about this use case

These questions are a reconstruction from the written architecture and thesis review, not quotations or private thoughts:

1. **What is invariant enough to provide a reference?** If US duration explains the move, the outright CGB trader may still want the exposure. If that relationship breaks, what observable distinguishes local pressure from a bad reference?
2. **What has not finished?** A price trend is a record. Remaining inventory adjustment, an unfinished cross-market response or a constrained dealer balance sheet is a candidate source of continuation.
3. **What marks a boundary?** Does recovery become easier, replenishment change, a US rally begin to transmit, or curve movement cease supporting the decline? Which of these can change before the CGB endpoint reverses?
4. **What information survives observation?** Simultaneous values in a research table may have reached the trader at different times. Several derived forwards may describe one underlying curve update.
5. **Which memory is necessary?** Repeated failed recoveries, an ageing execution episode and a recent one-bar shock can have the same current return but different futures.
6. **Which disagreement is meaningful?** Fresh conflicting witnesses should be visible. Missing or stale witnesses should have a different status. Neither should be averaged silently into “balanced.”
7. **What is the model allowed to change?** A read-only indicator can inform a trader without autonomously changing a trading threshold, position, or its own parameters.
8. **What observation would make us revise the construction?** A model that cannot articulate this will tend to explain every outcome retrospectively.

For CGB, the use case is a continuously revised assessment of *remaining directional opportunity and the risk of continuation failing*, with a clock and a documented information basis. The one-hour product is presently the strongest candidate. Two and four hours remain separate, less consistent research outputs; averaging the three into one confidence number would hide that distinction.

## The display lesson from notebook 6

Notebook 6 reads stored predictions and observed state; it does not recompute the forecasting model. That separation should be retained exactly in spirit. Its own table combines a predicted tag with long-horizon price extension and the selected buy/sell leg to mark a possible entry. That displayed entry flag is not the executable position exported by notebook 5. For intraday CGB, we should not inherit those one-year and ten-year extension rules.

The trader should see four separable questions:

| Question | First-line display | Drill-down |
|---|---|---|
| What is happening now? | Observed CGB direction, response/weakening state and episode age | Price, VWAP/recovery attempts, received flow and common/local duration decomposition |
| What does the model expect? | One-, two- and four-hour up/down/neutral probabilities with forecast timestamp | Endpoint interval, expected movement and conditional paths |
| What could hurt the view? | Adverse-excursion estimate and named current contradictions | Changes in recovery effectiveness, reference relationship, liquidity and support |
| How much trust does this reading deserve? | Freshness, selected-feed availability, support and model version | Historical calibration by horizon, out-of-support diagnostics and matured forecast journal |

A signed probability imbalance is useful as a compact directional number. It should not be labelled “probability the trade wins”: it is up probability minus down probability. Similarly, predictive entropy is uncertainty across outcome classes; it is not a certificate that the model is correct. Effective scenario count measures concentration of scenario weights, not the count of independent historical trading days.

The headline can be “CGB selling pressure persists; recovery evidence improving,” followed by the numerical horizon forecast. A deterministic sentence assembled from measured fields is preferable to an unconstrained narrative generator. Causal words such as “forced seller” require a supported mechanism inference; a directly observed price/flow relationship can be stated as such.

## How to move faster without weakening the research

1. **Separate a research runtime from a display runtime.** Training, full replay, plots and inventory simulation run offline. The display reads a completed, immutable forecast record. Refreshing a chart must never refit a model.
2. **Keep the one-hour indicator as the initial centre of attention.** Continue scoring all horizons, but make unsupported or late-session horizons unavailable instead of filling a mandatory screen slot.
3. **Reuse the finite path bank.** Exact weighted sums already avoid unnecessary Monte Carlo noise. Add new simulation machinery where it creates a missing mechanism, not where an exact sum already answers the question.
4. **Profile before replacing hardware.** The original project's CUDA requirement applies to its own implementation. A shallow model for one instrument every five minutes does not inherit that requirement. Measure update and startup time before selecting CPU or GPU changes.
5. **Replace full replay only after parity is established.** Current `predict_scenarios` reconstructs observed states and verifies the historical origin and fingerprints. A faster streaming state store should first match batch replay for rolling features, session resets, recovery tracking, late observations and restart. Keep full replay as the reference implementation.
6. **Use small paired mechanism experiments.** Share random innovations when comparing one changed mechanism; reserve new generator families and seeds for untouched evaluation. This isolates decisions faster than repeatedly sweeping every parameter.
7. **Evaluate source-inspired candidates individually.** Start with age-dependent continuation, a persistent episode observer and a coherent path construction. Do not import seven matrices, eleven labels and many coupled weights simultaneously: failure would then be difficult to diagnose.
8. **Reuse the existing completed corpus audit.** New coding choices should cite the specific lesson and actual failure they address. Another full reading is warranted when a new claim depends on unread material, not for every experiment run.

These are architecture recommendations, not measured runtime claims. No timing benchmark was run during this focused comparison.

## What would make it ready for a trader

| Gate | Evidence needed | Current position |
|---|---|---|
| Research logic | The target, information clock, path meaning and competing mechanisms are explicit | Substantial foundation already exists. |
| Synthetic discrimination | Controls, paired worlds and new mechanism families reveal where the model has information and where it cannot distinguish causes | Structure-lab experiments address this; the original favourable generator alone is insufficient coverage. |
| Live data semantics | Correct contracts, timestamps, corrections, session/roll treatment, stale-feed behaviour and a documented observation map | Must be verified when actual feeds arrive. |
| Real-data forecast validity | Frozen chronological evaluations against simple alternatives; calibration and errors assessed by independent sessions/events and horizon | Not supplied by synthetic experiments. The required sample follows event coverage and uncertainty, not an arbitrary number of days. |
| Operational validity | Freshness expiry, artifact identity, restart recovery, batch/stream parity, reproducible history and deterministic failure states | Hash-checked artifacts and read-only consumption exist; continuous operating behaviour remains to be built and exercised. |
| Trader usefulness | Shadow readings arrive in time, are understood correctly, expose relevant risk and add information to a trader's existing process | Requires observed use and a forecast/decision journal. |

Passing synthetic experiments can justify a better prototype and a real-data shadow trial. It cannot make unknown feed behaviour or real-market calibration disappear. For a decision-support product, this path is appreciably narrower than building automated order submission, queue management and portfolio execution. Costs still help the trader judge whether the indicated movement is economically meaningful, but the product need not choose or execute a trade.

The next valuable milestone is an indicator whose displayed claims can be reconstructed exactly from its saved observation and forecast record, whose uncertainty changes sensibly in competing worlds, and whose one-hour view survives a frozen real-data shadow evaluation. That is a concrete deployment target, and it uses the strongest organisational lesson of the source framework.

## Focused source index

| Source location | Inspected object |
|---|---|
| Notebook 5, cell 59 | Persistent graph versus instantaneous observer; state construction and graph-memory export |
| Notebook 5, cells 79 and 115; cell 146 lines 148–215 | Native training weights; graph-teacher targets; fit and model-selection wiring |
| Notebook 5, cell 92 | Composition of the seven structural laws |
| Notebook 5, cells 98–102 | Feedback signature, memory, diagnostic homeostasis and unchanged-strategy adaptation |
| Notebook 5, cells 108–109 | Shared graph memory and sequential MC leg paths |
| Notebook 5, cell 145 | Official multi-horizon probability path, temperature, active evidence and diagnostic masks |
| Notebook 6, cell 1 lines 74–110 | Read-only DB loading and closure |
| Notebook 6, cell 1 lines 187–246 | Separate observed and predicted tag readers |
| Notebook 6, cell 1 lines 301–360 and 411–437 | Entry-screen rule and observed-state chart |
| CGB `scenarios.py` | Learned state/price heads, local path conditioning, CAL mixture and forecast summaries |
| CGB `deployment.py` and `cli.py` | Hash-checked frozen artifacts and indicator-only read-only output |
