# What Fractal X actually does, and what should change in the SPY model

**The first repair is to align the measured system, the forecast target and the decision.** Our SPY adaptation used a narrow information set and a coarse endpoint objective. The source Fractal X pipeline constructs an exposure environment and models the lifecycle of movements. That is a substantial difference, and it suggests concrete experiments. It does not make the original implementation or its saved performance automatically correct.

This report combines three independent source reviews: [exposure and measurements](fractal-audit/exposure.md), [states and structural probabilities](fractal-audit/state-model.md), and [training and execution](fractal-audit/training-execution.md). Those notes contain notebook-cell/function evidence, implementation caveats and isolated counterexamples. The [source manifest](fractal-audit/source-manifest.json) identifies the exact notebook versions inspected. Original sources, fitted SPY models and forecast records were not changed. We did not run the original six-notebook pipeline or fetch another market dataset.

The judgement below is our interpretation of the source. It does not claim access to the author's private thoughts. The source library contains both his essays and papers by other authors. This review reads the six-notebook workflow, relevant code, the six market-framework essays and selected passages from the cybernetics papers; it does not claim to have reread every page of the entire research-paper library.

## Start with what failed and what did not

The [edge review](EDGE-REVIEW.md) finds no established SPY directional trading edge. The full model trails the price-only learner at one and two hours; its four-hour point advantage has an interval crossing zero. Its predicted mean price changes do not improve on zero-change forecasts. The state-conditioned expert received effectively zero CAL weight.

The engineering pipeline itself ran: the tree heads have nonzero splits and use multiple features. The output is not a failed fit returning a constant array. Most class probabilities are simply close to balanced.

There is a narrower positive finding: post-hoc endpoint interval scores improve by about 1–2% over a TRAIN distribution rescaled by current volatility. Preserve that as a separate uncertainty-forecast hypothesis. It is not a directional trading result.

The research question is therefore not how to make the indicator look more decisive. It is which observable distinctions and target definitions allow a model to make more useful forecasts.

## 1. The source constructs the market object before applying machine learning

Notebook 1 forms predefined long and short baskets. Lagged volatility controls their weights, and a lagged regression coefficient aligns the two return legs. A relative momentum selector chooses a current quadrant universe. Notebook 3 then constructs return residuals, synthetic level spreads, hedge instability, and ticker-to-spread relationships.

The Beta essay's operational idea is to define a reference exposure under a specified environment, then study departures from that reference. Its imbalance-carry discussion explicitly permits persistent drift when a force continues to act; it does not require every deviation to revert.

That helps distinguish two otherwise similar SPY declines:

- Broad constituents fall together, participation strengthens and rebounds weaken.
- A few large constituents pull down the index while the rest stabilise and dispersion rises.

These are proposed distinctions to measure, not conclusions we can recover from SPY OHLCV alone. Our current adapter sees the index's recent path, unsigned volume and bar VWAP proxy. It lacks the cross-sectional observations needed to tell these stories apart.

**Proposed change:** preserve SPY as the traded/forecasted object and add a small, declared environment block from synchronized basket observations. Begin with breadth, dispersion, relative strength and common-versus-local movement. First compare price-only against price-plus-environment with the original target and model capacity held fixed.

For example, with member simple returns and weights known before interval t:

$$
R_t^B=\sum_i w_{i,t^-}r_{i,t},\qquad
B_t=\sum_i w_{i,t^-}\mathbf{1}_{\{r_{i,t}>0\}},
$$

$$
V_t^B=\sum_i w_{i,t^-}(r_{i,t}-R_t^B)^2.
$$

These equations describe a return, weighted breadth and dispersion for a nonnegative normalized reference basket. Long and short legs need their own separately specified normalization; we should not silently feed negative weights into the breadth definition.

A fixed configured basket is a legitimate conditional research universe, but it is not point-in-time historical index membership. A separate experiment can trade the basket itself. Its result must not be conflated with forecasting SPY.

## 2. Slow context and intraday evidence need different clocks

Fractal's measurement layer uses **252 daily observations**, not 252 arbitrary rows. It also uses 63-day comparisons, 126-day centering and expanding estimates. The original head horizons are one to five daily observations.

Our SPY dataset contains 241 sessions in total and 144 TRAIN sessions. It cannot support a faithful 252-day warm-up followed by meaningful original-model training. Our fast features instead reset each session and mainly look back 5–60 minutes.

**Proposed change:** use multi-year daily history to build a slow environmental state, available only after its observation day, alongside fast intraday measurements. Keep slow and fast state updates explicit:

$$
E_t=E_{d-1},\qquad
X_t^{\mathrm{fast}}=f(\text{completed intraday observations through }t).
$$

Here d is the current session. A daily state constructed with today's eventual close must not influence today's noon forecast. Replacing every daily window with the same number of five-minute bars would create a different model and must be justified as such.

There are two distinct future experiments: a faithful daily Fractal reference run after resolving its contracts, and an explicitly adapted intraday SPY model. They answer different questions.

## 3. The original state represents a movement's lifecycle

Fractal defines range plus five upward and five downward phases: preparation, start, established trend, tentative exhaustion and end. Two regime blocks create 22 states. A sequential automaton advances or retreats through the phases and can return from tentative exhaustion to continuation. The regime block is retained during a leg and refreshed in range.

The source uses continuous evidence such as boundary distance, compression, breakout, drift relative to dispersion, spread deformation and changes in distribution measurements. Its graph joins consecutive dates and records evidence changes; it is not a graph neural network that discovers a stock network.

Our observer is much simpler. A 30-minute standardized move chooses direction; a five-minute velocity comparison assigns weakening. A routine pullback and an actual termination can therefore receive the same description.

**Proposed change:** first expose continuous formation and failure evidence, then test a small persistent phase observer. Relevant quantities include distance to a past boundary, pace of approach, depth and recovery of a pullback, elapsed phase duration and basket participation. Compare continuous features alone, hard phase alone and both. A larger label vocabulary earns its place only if it distinguishes different future paths.

The cybernetics lesson we take from the inspected memory/requisite-variety passages is specific: memory should retain distinctions that matter to the response. Adding states indiscriminately is not that principle. A highly persistent label also needs a persistence baseline; predicting the same label again can be easy without identifying profitable movement.

## 4. Our future-state target does not match our return target

This is a particularly concrete weakness. Our future state at t+h describes the last 30 minutes before t+h. Our endpoint label measures the entire next 60, 120 or 240 minutes.

A path can rise strongly for three hours, fall during the last half-hour, and still finish well above its origin. Its terminal observed state is downward, while its four-hour return class is upward. Forecasting that final state better need not improve the full-horizon endpoint class used to choose the mixture weights.

The zero state-expert weight could therefore reflect limited new information, a poor state partition, target mismatch, estimation noise, or some combination. It does not justify forcing the weight above zero.

**Proposed change:** retain the old endpoint objective as a comparator and define useful continuation directly. One candidate, for direction d_t observed at the decision time, is:

$$
Y^{\mathrm{cont}}_{t,h}
=\mathbf{1}\left\{
d_t(P_{t+h}-P_t)>b_{t,h},\quad
\operatorname{MAE}^{d_t}_{t,h}\le a_{t,h}
\right\}.
$$

The two thresholds have price units and must be specified from the intended use and development data. They are not numbers to choose by maximising this already inspected TEST period. This endpoint-plus-path target can use future OHLC extrema without pretending to know their within-bar order.

A different candidate is continuation-before-invalidation, expressed as competing first-passage times. That target is closer to a stop/target decision, but simultaneous barrier crossings within a five-minute bar require finer observations or an explicit ambiguous-bar convention. Do not silently choose the favourable order.

A third candidate predicts the hazard of a leg ending, conditional on its current phase and age. That directly asks whether the move is likely to survive, instead of predicting only its eventual state. These alternatives require separate experiments rather than an ensemble built before we know which question matters.

## 5. What its machine learning actually learns

The original XGBoost heads learn future graph lifecycle tags. They are trained with class/transition weighting, candidate regularization, early stopping and a bounded feedback pass that changes training weights. The source then combines learned and structural information. Its saved lifecycle accuracy is not comparable to our three-class cumulative-return accuracy.

The strongest transferable design is that **the features include the continuous evidence used to construct the state**, not just the state name. This gives the learner access to degrees of formation and exhaustion before a threshold flips.

There is also a warning: class weighting changes the distribution represented by the fitted classifier. A reweighted model's output should not automatically be read as the natural event frequency. Any such change needs subsequent probability calibration and evaluation on the unweighted target population.

The actual original code uses an internal calibration tail of outer TRAIN for candidate choices and temperatures. Some preprocessing uses all outer TRAIN, including that internal tail. A redesigned experiment should fit preprocessing and label thresholds on the corresponding fitting window and reserve a separate calibration window, or use nested chronological folds.

**Proposed change:** hold the learner simple while testing improved evidence and targets. Add bounded capacity or transition-weight comparisons only when the failure diagnostics justify them. More trees cannot reconstruct breadth that was never observed.

## 6. The structural mathematics is an explicit model that can be inspected

Notebook 4 supplies seven literal 22-by-22 stochastic matrices. It does not contain the derivation or estimation of those entries. Their diagonal entries are about 0.972–0.987, so their per-step assumption strongly favours persistence. Carrying those values directly from a daily model to a five-minute model would change their implied duration.

Notebook 5 scores these candidate laws with TRAIN transition evidence and blends them. Its Monte Carlo branch generates price paths, evolves their lifecycle through phase-dependent boundaries, weights paths with the first-horizon head, and propagates those weighted phases to longer horizons. Distribution and spread inputs are held fixed along that simulation; they are not a simulated joint market ecosystem.

Ignoring numerical floors, the active pre-calibration state posterior can be written:

$$
\widetilde p_{t,h}(s)
=\left[q^{\mathrm{MC}}_{t,h}(s)P_{z_t,s}F_t(s)\right]^{1/D_{t,h}}
c_{t,h}(s)^2\ell_{t,h}(s)^2,
\qquad
p_{t,h}(s)=\frac{\widetilde p_{t,h}(s)}{\sum_u\widetilde p_{t,h}(u)}.
$$

The factors have concrete roles: simulated phase mass, structural transition row, frontier tilt, disagreement temperature, construction evidence and selective direct-head influence. The first-horizon likelihood already enters Monte Carlo weights, so the normal h=1 branch does not multiply that direct likelihood again. The [state audit](fractal-audit/state-model.md) documents active versus fallback branches and exact source cells.

This is where the source's physical intuition becomes code: constraints shape phase accessibility, propagation carries current state forward, and disagreement changes probability concentration. The correct research question is which of those operations contributes useful information on a fixed target.

Our empirical-path approach can express a comparable sequence without copying the literal matrices: define observed phase evidence, estimate transition hazards from past episodes, propagate a coherent path distribution, and evaluate the resulting outcomes. A more elaborate simulator is warranted only when it represents something the empirical bank fails to preserve.

## 7. Our path bank is much broader than the parameter name suggests

The current `neighbor_count=64` determines a Gaussian-kernel bandwidth from the 64th distance. It does not retain only 64 paths. Every TRAIN path receives at least a small floor weight, and the final mixture can have broad effective support.

| Horizon | TRAIN paths | Median effective paths in final forecast | Median normalized class entropy |
|---|---:|---:|---:|
| 60 minutes | 7,776 | 3,830 | 0.9970 |
| 120 minutes | 6,048 | 3,140 | 0.9974 |
| 240 minutes | 2,592 | 1,565 | 0.9951 |

These are actual frozen-forecast diagnostics, recorded in [edge-diagnostics.json](edge-diagnostics.json). High entropy means the class forecast is close to uniform; it is not the same as high uncertainty about model parameters. Broad scenario support can stabilise risk estimates and can also average away meaningful differences. The current results do not identify which effect dominates.

**Proposed change:** compare a small predefined set of bandwidth/support choices on development folds while monitoring probability scores, interval scores and tail coverage together. Sharper probabilities are not inherently better. Forcing confidence would conceal the very failure we are trying to understand.

## 8. Source issues that should be repaired before a faithful reference backtest

The original design contains useful ideas and concrete implementation issues. These findings are based on source tracing; two small isolated fixtures verify arithmetic/update-schedule counterexamples. They do not quantify how much any reported return would change.

| Finding | Source location | Consequence |
|---|---|---|
| Dynamic position confidence uses the current completed bar while earning the return ending on that bar | Notebook 5, cell 77 lines 75–78; unshifted call in cell 147 lines 511–541 | Pending entries are delayed correctly, but changing size with end-of-interval information requires a timing repair and a new ledger replay. |
| `tag_post_t1` actually exports the current graph leg | Notebook 5, cell 147 lines 1056–1069 | Recognition, persistence assumption and posterior prediction must have different field names and evaluation targets. |
| A `stationarity_ok` path checks nonmissing values and positive variance rather than ADF/KPSS acceptance | Notebook 5, cell 40 lines 3–24 | Data validity must not be interpreted as a stationarity test. |
| Intended 35% weight cap can return a 92.45% weight for a concentrated input | Notebook 1, cell 41 | The supplied fixture shows cap enforcement fails; repair the projection and assert its constraints. |
| State and tag distributions are temperature-scaled independently | Notebook 5, cell 147 lines 303–306 | Derive every marginal from one calibrated distribution so their probabilities remain coherent. |
| Warm-up volatility uses a full-history fallback; terminal cointegration recalculation changes historical prefix results | Notebook 5, cell 110 line 21; notebook 3, cell 21 line 21 | Use past-only initialization and fixed update schedules; test incremental/batch identity. |
| Final selected universe is processed over its history; some missing returns become zeros | Notebook 1, cells 40, 60 and 65 | Distinguish current-universe analysis from historical selection, and missing observations from zero movement. |
| Some corporate-action adjustments use open or mean OHLC rather than raw close as the denominator | Notebook 2, cell 62; notebook 5, cell 158 | Reconstruct consistent observed OHLC before evaluating barrier hits or traded returns. |

This table uses **one-based cell numbers including Markdown cells**, with line numbers inside the code cell. The exposure audit uses zero-based indices and states that explicitly. The source manifest maps both numbering conventions.

Other recorded questions include simulation drift convention, deterministic random streams by origin, stable category mappings, dynamic-resizing turnover costs, and the treatment of a long entry in the established-up phase. See the detailed audits for scope and evidence.

The downloaded checkout contains saved console performance output but lacks the corresponding data, DuckDB, prediction and trade-ledger bundle. We cannot reconcile its saved Sharpe figures to the currently inspected code. The audit neither establishes its original profitability nor establishes that every reported result disappears after correction.

## 9. A concrete sequence for fixing our experiment

The sequence below keeps cause and effect interpretable. Each row is a separate hypothesis; do not combine all changes and then attribute the result to the preferred narrative.

| Order | Question | Concrete change | Evidence required |
|---|---|---|---|
| A | Can we audit exactly what was known and earned? | Freeze current artifacts; define observation, forecast and optional action clocks; preserve cost and inventory accounting separately. | Prefix/future-poison checks; position fixed before its earned interval; no original-result overwrite. |
| B | Does a broader environment help predict the same SPY target? | Add one fixed block of basket breadth, dispersion and relative movement to the price-only baseline. | Incremental probability and path scores on chronological development folds and an unused final period. |
| C | Are we asking the right momentum question? | Compare endpoint direction with continuation subject to adverse excursion and episode survival. | Each target has a declared use; economic path diagnostics agree with its meaning; use matched samples. |
| D | Does lifecycle memory add information? | Small persistent observer plus continuous formation/failure evidence; include duration. | Beat persistence on phase targets and beat price-only on the unchanged economic target. |
| E | Does conditional propagation add anything? | Compare direct prediction, empirical-path conditioning and, only if warranted, explicit phase simulation. | Added component improves the fixed outcome; adequate support; coherent marginals; stable seeds and path identities. |
| F | Can the result support a decision after friction? | Freeze one selective policy, delayed fill convention, exposure limits, repeat-signal handling and cost scenarios. | Net outcomes and uncertainty versus risk-matched simple policies; report gross results and costs separately. |

The already inspected 49-session TEST interval is diagnostic from now on. New choices need a newly reserved chronological evaluation identity. Historical folds within development data are useful, but repeatedly relabeling the old test as untouched would not restore independence.

For an eventual one-position return ledger, the basic timing identity is:

$$
\operatorname{PnL}_{t+1}=q_t(P_{t+1}-P_t)-C_{t+1},
\qquad q_t\text{ is fixed before the earned interval begins}.
$$

Actual delayed fills may change the interval endpoints; the ledger must record those endpoints explicitly. Trading costs depend on executed inventory changes, including resizing, rather than only on a final exit. An indicator can remain useful without order routing, but a claim about trading edge requires this decision layer to be evaluated.

## What I would change first

I would keep the present SPY result frozen and make **basket context plus the unchanged price-only benchmark** the first information experiment. In parallel as a design task, I would specify useful continuation and a compact lifecycle observer. I would test the uncertainty-interval improvement separately.

I would not begin by transplanting seven fixed matrices, forcing a nonzero structural-expert weight, or widening a training search until the inspected period looks good. Those actions do not address the missing observations or the target mismatch.

The useful lesson from Fractal X is its order of construction: define the exposure and environment, measure how the structure forms and fails, forecast that evolution, then translate the distribution into a decision. The next version should make those links explicit and testable.
