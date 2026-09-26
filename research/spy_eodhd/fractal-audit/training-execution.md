# Fractal X training and execution audit

Read-only source audit. Notebook cells below use **one-based JSON cell numbering**, and line numbers are local to each cell. No notebook was executed. No API request, credential read, training run, or original source modification was performed. Inspection date: 26 September 2026.

Files consulted: `0.1 AGENTS.md`, `0 README_MODEL.md`, `agents/sub_a.md`, `agents/sub_a1.md`, `agents/sub_b1.md`, `5 algo fractal x.ipynb`, `6 signaux.ipynb`, and the SPY study `REPORT.md`, `EDGE-REVIEW.md`, `run_study.py`.

Logic extracted: distinguish the object being observed, the future target being predicted, the calibrated probability, and the executed position. The source's actual executable code is required to interpret the descriptive documentation. Decision deduced: transfer specific, testable design principles; do not treat the source checkout or its saved console output as an independently verified profitable strategy. Uncertainties: the required DuckDB and produced run artifacts are absent, so output provenance, numerical impact of identified issues, and real predictive/trading performance cannot be reproduced in this audit.

## What the source actually trains

The original model is daily and multi-instrument. Notebook 5 consumes the selected universe, the daily distribution measurements, the beta/spread pack, and the seven 22-state matrices. Its 11 lifecycle tags distinguish range, precursor, start, trend, tentative end and end in each direction. The SPY experiment is a five-minute, single-instrument, five-observed-state conditional-path adaptation. A score for one is not the score for the other.

In notebook 5 cell 147 lines 171–176, the teacher target is explicitly `graph_tag.shift(-h)` for horizons 1–5. Cell 80 `xgb_train_tag` fits those future graph lifecycle labels. It does not fit the subsequent cumulative price change directly. Separately, cells 123–124 construct real-market audit targets by shifting the **single-bar** return at t+h, rather than computing a cumulative h-bar return.

Cell 147 lines 318–341 defines the official evaluation against future graph labels. Cell 130 lines 19–30 aggregates class-specific rows with support weights, so the saved field `test_accuracy_mean_by_tag_horizon` is micro accuracy across evaluated graph labels and horizons, despite its name. Therefore the saved approximately 0.54–0.65 accuracies cannot be compared to the SPY experiment's three-class endpoint accuracy.

The right inference is that the source tries to predict the continuation and transition of an explicitly constructed lifecycle. High lifecycle persistence can make that task easier without producing useful future price discrimination. A persistence baseline must use the same graph target and evaluation cohort.

## Actual training and calibration sequence

Notebook 5 cell 64 defines a chronological 60/20/20 outer split, snapping boundaries to cycle ends when available. Horizon purge plus embargo is `max(7, H_MAX) + H_MAX - 1`, or 11 bars for H_MAX=5. The held-out test tail excludes five unlabeled rows.

Cell 147 lines 40–48 further separates the outer TRAIN into an inner fitting set and its final approximately 20% `train_cal`, with an intervening gap. Contrary to several stale docstrings saying VAL, the call at lines 213–215 passes these inner fit/calibration sets to XGBoost. Outer VAL and TEST are then evaluation sets.

However, graph construction, law composition, the feature scaler, and several training-weight reference statistics use all outer TRAIN, including the inner `train_cal` segment (cell 147 lines 55, 81–95, 168–170). This does not contaminate outer TEST, but the inner calibration sample is not wholly untouched by fitted preprocessing or label construction. Calling it an independently unseen calibration set overstates that separation.

Cell 117 builds features from current graph nodes/edges, numeric measurements, current phase/state one-hot columns, graph memory, **soft per-tag construction evidence**, and phase-specific frontier measurements. The most transferable idea is exposing the quantities that construct a state, not only its hard label. A precursor probability can vary meaningfully before a hard state changes. Duplicate feature columns are removed using TRAIN rows.

Cell 80 training performs:

1. Effective-number class weights on inner training targets; transition-family and horizon boosts; bounded row weights.
2. Three regularization candidates, with depth, shrinkage, rounds and leaf-weight heuristics dependent on training size.
3. Early stopping on inner calibration log loss.
4. Selection using macro graph log loss plus overfit-gap, predicted-support/entropy and approximate market-posterior terms.
5. Retraining the selected candidate with per-class calibration feedback for undercovered or poorly predicted tags.
6. Choosing between original and feedback fits on the same inner calibration score.

Exact locations: cell 80 lines 31–86 weights, 89–180 candidate fit and score, 214–253 candidate construction and selection, 255–347 feedback and reselection. The “no constants” comments are not a literal property of the code: bounds and numerical coefficients are architecture choices. For example, the transition boost at line 60 uses 0.20 and the selection score at lines 147–168 uses several fixed penalties. A bounded search is sensible; these formulas are not uniquely derived by the available sample count.

The feedback is a controlled training-weight intervention, not a new independent source of predictive information. Reusing one inner calibration segment for early stopping, selection, feedback, temperature and operating thresholds creates selection pressure that outer evaluation must reveal.

Cell 147 lines 279–306 fits a per-horizon temperature on the inner calibration set over T in {1, 1.15, 1.35, 1.6, 2, 2.5, 3, 4}. This can flatten overly sharp distributions while preserving each distribution's argmax. It cannot create direction information missing from the observations. Our SPY forecasts are already close to balanced, so copying this softening mechanism is not an obvious repair.

## Physics-inspired mechanisms as numerical operations

The cybernetic weight constructor (cell 116) measures spread variety, distribution entropy, frontier activity, graph recognition reliability, tail/fragility statistics, structural stress and memory. It exponentiates a weighted sum, normalizes by TRAIN mean and clips to [0.25, 3]. Those weights change which training observations matter in the classifier's loss. The gains in line 152 are expressly architecture hyperparameters (lines 148–151), not a mathematical consequence of the physics terminology.

The sequential Monte Carlo routine (cell 110) simulates geometric Brownian price paths from current close using lagged EWM drift and volatility. Each simulated path follows a discrete lifecycle whose transitions depend on price crossing phase-specific boundaries, frontier activation and structural law probabilities. Paths are reweighted by the one-step classifier's likelihood and propagated to later horizons. The output is a distribution over lifecycle tags, not an independently observed order-flow process.

The posterior routine (cell 146) combines a current-state structural row, frontier weights, projected path probabilities and classifier likelihood. Disagreement and current price agitation affect temperature; squared normalized amplitudes define the probabilities. Source comments describe these through Born/Zurek and related physical ideas. For research transfer, the testable content is **a constrained state transition model with disagreement-sensitive concentration and a shared path representation**. These mechanics should be compared component by component with simpler models on the same target.

## Important source contradictions and potential defects

Status: the stated operations and contradictions are **confirmed by static source inspection**. Their numerical effect on the saved June run is **unresolved without its artifacts and execution**. In particular, the same-bar sizing finding does not establish that all reported Sharpe is spurious or quantify how much would remain after repair.

| Finding | Exact source | Implication |
|---|---|---|
| README describes `tag_post_t1` as posterior prediction; actual export uses current graph lifecycle sequence | Notebook 5 cell 147 lines 1056–1069 | A current observed state/continuation assumption must not be presented as posterior argmax. Notebook 6 cell 2 lines 240–246 calls the exported value a next-close head signal, preserving the mismatch. |
| Dynamic sizing uses information from the end of the interval it earns | Cell 77 lines 75–78; unshifted posterior passed by cell 147 lines 511–541 | Current completed-close posterior multiplies close[i]/close[i−1]. Pending entry is lagged, but that does not fix the size applied to an already realized return. Source code supports a timing defect; absent artifacts prevent measuring performance impact. |
| Entry-threshold score uses current return direction | Cell 147 lines 424–439 | This optimizes recognition alignment, not future net opportunity. |
| `exec_side_hit_test` and `exec_side_pnl_test` use current graph side against the same current return | Cell 147 lines 551–558 | These are recognition diagnostics; the latter is a signed sum of log returns, not a costed execution ledger. |
| Independently tempering state and tag probabilities breaks their aggregation identity in general | Cell 147 lines 303–306 | For T != 1, summing normalized powered state probabilities need not equal normalizing powered tag sums. Evaluation/export uses one probability while execution aggregates another. Temper one canonical joint distribution, then aggregate. |
| MC warm-up sigma fills with the full-history return standard deviation | Cell 110 line 21 | Prefix invariance fails for early rows. This is not proof of an effect on reported TEST performance; require a future-poison/prefix test to localize any propagation. |
| Adjusted OHLC is approximated using a rolling median(adjusted_close/open) factor | Cell 158 lines 19–27 | The correct corporate-action factor requires raw close, not open. Forcing highs/lows to enclose adjusted close does not recover true traded extrema. Stops/TP cannot be independently reconciled without original raw prices. |
| Allowed long entry U is excluded from the `entry_leg_up` flag | Cell 77 line 129 versus lines 138–143 | U can enter long but use down-leg exit membership, potentially causing unintended early exit. Requires a small trajectory test. |
| Dynamic exposure changes incur no separate turnover charge | Cell 77 lines 76–78, 110, 151 | Round-trip cost is charged at exit at the contemporaneous confidence size; intermediate increases/decreases are not an inventory ledger with turnover costs. |
| Causality column audit checks names | Cell 37 | It blocks obvious future/target columns but cannot prove the values of innocently named columns are causal. |

The backtest does have useful explicit choices: one-bar pending entry, stops from prior completed extrema, gap-aware adverse stop fills, stop-first resolution when stop and target both occur, round-trip and overnight assumptions. These are worth retaining as explicit assumptions, but they do not resolve the dynamic-sizing defect above. Default equity/other cost is 0.00050 round trip and overnight cost 0.00002 per day in cell 17, with broker fee override when present. These are assumed costs, not measured quote slippage.

## What actual result artifacts exist

The checkout has saved cell 159 console output for 27 symbols. Examples: BA.US Sharpe 1.7609, MaxDD −0.0200; GM.US Sharpe −0.1335; NZDUSD.FOREX Sharpe −0.2787. A warehouse message names a 28 June 2026 run and lists 27 summary rows but 100 live/deploy records. No `fractal.duckdb`, `STAGE3_OUT`, `data`, `outputs`, `STAGE1_OUT` or `beta` folder exists in this checkout.

Therefore we can report what the console says, but cannot inspect the returns, fills, chronology, model identities or corresponding feature/label contracts for those results. Saved notebook output is insufficient to establish reproduction of the present code or profitable deployment.

## Concrete next modifications for the separate SPY model

1. Keep the tested SPY version frozen. It has no established directional edge. The positive interval-score result is post-hoc and should receive a separate future test, not rescue the directional claim.
2. Preserve three distinct outputs: current observation, future probability/path distribution, and optional executable action. Give each an explicit availability time and target definition.
3. Replace the vague question “more accurate states?” with two separately evaluated hypotheses: future lifecycle transition prediction and economically useful path continuation. For continuation, declare an adverse-excursion condition or first-passage competition in advance. Retain unconditional price class forecasting as an unchanged baseline.
4. Add continuous formation evidence before adding more hard states: normalized boundary distance, pace of approach, failed recovery depth, deceleration, state age and asynchronous broad-market confirmation. Compare continuous evidence alone, hard state alone and both. The source's soft construction channels motivate this experiment; they do not determine its winner.
5. Evaluate persistence on the exact future-state target and simple volatility-scaled distributions on the price/path target. The state expert's zero CAL weight says this current expert did not add the chosen objective's information; forcing a nonzero weight would hide the finding.
6. If state transitions are rare, use bounded training weights only in a declared comparison, with unweighted proper forecast scores and probability recalibration. Reweighting changes the target distribution learned by the classifier and can produce false confidence if the probabilities are read literally.
7. Use separate inner windows or nested chronological folds for fitting, early stopping, feedback and calibration. All transforms and state-threshold estimates should be fitted only on the corresponding inner fitting window. The already inspected SPY TEST period is diagnostic from now on; it is not an untouched confirmation set for these changes.
8. Test disagreement-sensitive concentration only if calibration plots identify overconfidence. Calibrate a canonical joint/path distribution and derive every marginal from it. Do not separately modify class and state probabilities.
9. Add a minimum execution ledger if the objective is trading evidence: position known before each earned return interval, delayed order/fill timestamp, overlapping-signal policy, inventory, turnover, spread/slippage assumptions and same-session exit. Compare risk-matched simple policies. No strategy return should be reported from current-state recognition accuracy.
10. For cross-sectional breadth/context, use the existing basket design with lagged membership/weights and synchronized timestamps. Change only that measurement family first; keep model and labels fixed to identify its contribution. A full original-model replication is a separate experiment requiring the missing artifacts or regeneration of the entire source pipeline.

The source's useful lesson is a layered, measurable system: construct the exposure, define observable lifecycle mechanics, forecast their evolution, calibrate uncertainty, and separate execution. Its implementation also contains decisions and contradictions that warrant correction before replication. Neither admiration of the design nor a poor SPY adaptation score establishes the original strategy's edge.
