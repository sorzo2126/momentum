# CAD intraday duration momentum: pressure, absorption and continuation

Research note prepared 23 September 2026 from the supplied Fractal X repository, its relevant thesis sources, and linked primary research. This is a proposed research design. No CAD market dataset was supplied, no indicator was fitted, and no trading edge was established.

The central hypothesis is that an intraday duration trend persists while directional pressure continues to move prices and counter-pressure fails to recover the lost ground. A VWAP rejection is one observable part of that process. Its usefulness depends on what happened before it, which other markets confirm it, how liquidity responds, and whether the next executable move is large enough to cover costs.

The research question is therefore: **following an already observable downward VWAP retest, is subsequent CGB downside continuation stronger when duration markets confirm the move, selling pressure persists, and buying attempts have weak price impact?** The comparison is with the same price setup without those conditions. This is a conditional prediction hypothesis, not an assertion that the proposed mechanism is proven causal.

## What comes from Karim's writing

The most directly relevant sentence is: “Microstructural absorption decides whether the bias becomes movement.” It appears in [04 zureck vs laplace.md](<C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main/theses/source/PHYSICS/04 zureck vs laplace.md:206>). The surrounding passage distinguishes directional forcing, the capacity to absorb it, leverage constraints and liquidity. Earlier in that document, a sequential likelihood-ratio test accumulates evidence of a departure from a reference distribution.

In [03 zureck.md](<C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main/theses/source/PHYSICS/03 zureck.md:62>), he writes: “The dominant constraint defines the effective law.” Later he describes positioning as a hidden state inferred from observable flows, open interest and liquidity. The useful implication is that the same chart pattern can behave differently under different constraints. A policy repricing, a temporary liquidity shortage, a relative-value rotation and sustained directional execution can all initially produce falling CGB prices.

In [01 beta.md](<C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main/theses/source/PHYSICS/01 beta.md:101>), he writes: “Alpha is the excess generated above a beta built under constraints and consistent with your environment.” For this project, that means defining the exposure and comparison before declaring a signal useful. The exposure is outright CAD duration through CGB. A sensible comparison is a simple CGB momentum/VWAP rule operating at the same times and costs. A cross-market component can then show whether context improves that rule.

My interpretation of these passages is: specify the exposure, observe the environment that supports it, measure whether that environment still produces movement, and revise the state when the response changes. This is an application of the writing; it is not a quotation or a claim about what Karim would personally recommend for CAD swaps.

The thermodynamic and quantum terminology is a modeling analogy. It does not establish that a financial “free energy” decreases, that a fitted spread is stationary, or that normalized model scores are calibrated probabilities. Those are separate mathematical and empirical questions.

## Read the selloff as a sequence

Consider the reported sequence: CGB opens lower, rallies toward VWAP or its lower band, fails to recover, and continues lower while someone pays five-year swaps.

Opening lower identifies an initial condition. Trading below VWAP identifies the current price relative to executed business. A failed recovery supplies new information only once the failure is observable. A later downside extension supplies additional evidence that the move is continuing. None of these, individually, tells you the entire session's final shape.

The especially useful observation is a difference between the effect of buying and selling. If sell-side pressure repeatedly produces fresh downside movement while buy-side pressure produces only small, short-lived recoveries, there is a measurable response asymmetry. A possible mechanism is persistent directional execution combined with inadequate opposing liquidity. It remains possible that the move is nearly exhausted; that competing explanation must be tested.

This suggests watching three things together:

1. **Pressure:** signed executed volume and order-book changes, including depletion and replenishment.
2. **Response:** how much and how persistently price moves after that pressure.
3. **Confirmation:** whether US duration, Canadian tenors and fresh swap/OIS observations support the same interpretation.

Selling with continued price declines is different from selling that no longer makes new lows. In the second case, replenishing bids and improved recoveries would be evidence consistent with absorption. Equally, slowing declines alone do not establish a bullish reversal. The live state can move from “downward continuation” to “uncertain” before there is enough evidence for “upward continuation.”

The named account is not an explanation of the mechanism. A pay-fixed swap generally contributes short-duration exposure, but the transaction might be one leg of a hedge, spread or portfolio adjustment. Futures and pay-fixed swaps can explicitly be combined in spread trades; [CME's invoice-swap description](https://www.cmegroup.com/education/featured-reports/cme-clearing-invoice-swaps-margin-efficiencies) illustrates this. The anecdote cannot reveal Two Sigma's or Citadel's private model, complete position or execution objective.

## Give each market a specific job

| Observation | Research role | Interpretation to avoid |
|---|---|---|
| CGB trades, bid/ask and volume | Target price, executable costs, VWAP, realized continuation | A price pattern is already a forecast |
| Canadian 2y, 5y and 10y futures and cash yields | Separate broad duration movement from curve rotation | Equal price changes mean equal rate risk |
| US duration futures | Common rate shock, lead/lag candidate, cross-market confirmation | Every apparent lead survives timestamp alignment |
| CAD OIS, swaps and forwards | Local policy/curve repricing and optional confirmation | Several derived forwards are independent evidence |
| L2 depth and trades | Pressure, replenishment and price response | Displayed depth is committed future liquidity |
| SPX and VIX | Conditional cross-asset context | Higher VIX always predicts a duration rally |
| Reported flows | Timestamped contextual observations | The participant's identity establishes motive |

Separate timescales. Macro information and scheduled events can supply session context. Several-minute to tens-of-minutes observations can describe continuation. Order-book events can help characterize immediate absorption or entry conditions. Evidence about the next quote change does not automatically predict the next half hour.

For a first experiment, a 15-minute forecast horizon is an explicit example, not an optimized recommendation. Choose the operational horizon before searching for attractive results. Additional horizons should be secondary, recorded experiments.

## Fix units before combining signals

Let $F_t$ be the CGB futures midpoint in quoted price points. CGB has a 0.01-point tick worth C$10 per contract, so a one-point move is C$1,000 per contract. These are [Montréal Exchange contract specifications](https://www.m-x.ca/en/markets/interest-rate-derivatives/cgb).

The midpoint change in ticks is

$$
x_t=\frac{F_t-F_{t-1}}{0.01}.
$$

Positive $x_t$ means a gain for a long CGB position before trading costs. Rising yields normally correspond to negative CGB price changes, so raw yield changes and futures changes have opposite directional signs.

If $D_t>0$ is the current CGB contract's dollar loss for a one-basis-point rise in the relevant yield, a local duration approximation gives

$$
\Delta y_t^{\mathrm{equiv}}
\approx -\frac{1000\,(F_t-F_{t-1})}{D_t}
\quad\text{basis points}.
$$

This is a first-order mapping, not an exact futures pricing identity. Use the contract's relevant delivery-bond risk and conversion-factor treatment; do not substitute a generic ten-year par-bond duration. Delivery conversion factors are specified by [Montréal Exchange](https://www.m-x.ca/en/markets/interest-rate-derivatives/bond-futures-conversion-factor). Five-year swap exposure and CGB exposure also differ by key-rate sensitivity and basis.

For a transparent curve representation, begin with observed yield changes:

$$
L_t=\frac{\Delta y_{2,t}+\Delta y_{5,t}+\Delta y_{10,t}}{3},
\qquad
C_{25,t}=\Delta y_{5,t}-\Delta y_{2,t},
\qquad
C_{5,10,t}=\Delta y_{10,t}-\Delta y_{5,t}.
$$

$L_t$ is a descriptive average level move, not the return of a risk-balanced portfolio. The other two coordinates describe rotations. Later, risk weights or factors estimated on earlier data may improve the representation. With four swap sessions, a transparent decomposition is preferable to a large fitted factor system.

Define the 2s5s slope explicitly as $s_{25}=y_5-y_2$. Then

$$
\Delta s_{25}=\Delta y_5-\Delta y_2.
$$

Both examples flatten the curve by three basis points:

| Example | Change in 2y yield | Change in 5y yield | Change in 2s5s |
|---|---:|---:|---:|
| Both yields rise | +5 bp | +2 bp | −3 bp |
| Both yields fall | −1 bp | −4 bp | −3 bp |

Thus flattening can accompany selling or buying of duration. Neither example specifies the ten-year move. To investigate “flattening after a selloff predicts a rally,” condition on the prior selloff, the individual yield changes, the ten-year response and contemporaneously available flow. Treat it as a hypothesis, not a sign identity.

## Keep common duration and Canadian relative movement separate

A simple descriptive relationship is

$$
x_t^{\mathrm{CAD}}=\widehat\beta_{t-1}x_t^{\mathrm{US}}+\varepsilon_t.
$$

Estimate $\widehat\beta_{t-1}$ using only earlier, synchronized observations in clearly specified units. The first term describes the part of the current CAD move associated with US duration. The residual describes relative CAD movement within this fitted relationship.

Keep both terms. Your target is outright CGB momentum. If US selling drives a broad duration selloff and CAD follows normally, the residual may be near zero while the CGB trade has a large directional move. Automatically removing the common factor would remove part of the exposure you want to identify.

This equation explains an already observed interval. To demonstrate predictive value, features known at time $t$ must improve a forecast of a later interval. A good contemporaneous fit is insufficient. Apparent US-to-CAD lead/lag must also survive quote-age, exchange-clock and receipt-time checks.

## Make VWAP and rejection observable

Using actual trades $(p_i,q_i)$ from a defined session start through time $t$, calculate

$$
V_t=\frac{\sum_{i\le t}q_i p_i}{\sum_{i\le t}q_i},
\qquad
\sigma_{V,t}^{2}=\frac{\sum_{i\le t}q_i(p_i-V_t)^2}{\sum_{i\le t}q_i}.
$$

A normalized distance is

$$
d_t=\frac{F_t-V_t}{\max(\sigma_{V,t},0.01)}.
$$

These definitions specify one possible VWAP band calculation. Chart packages may use different conventions. A one-standard-deviation band is a measure of historical dispersion under that definition; it is not automatically a Gaussian probability boundary or a confidence interval for fair value.

Record distance, VWAP slope, time spent below VWAP and the observed response to approaches separately. A live rejection rule needs a causal sequence. For example: identify an approach to a pre-specified tolerance around the reference, then wait for a specified failure to reclaim and a subsequent retreat. The signal begins when confirmation has occurred. It must not be backdated to the attractive touch price.

The tolerance, observation interval and failure condition are research parameters. Record them before evaluation. Compare the same rule with and without the extra market and flow context. Count overlapping retests as dependent events rather than pretending each is a new independent trial.

## Use the book to study response, not just imbalance

For aggregate displayed bid and ask quantities $B_t$ and $A_t$ over a defined number of levels,

$$
\mathrm{OBI}_t=\frac{B_t-A_t}{B_t+A_t},
$$

when the denominator is positive. This measures a stock of displayed liquidity. Order-flow imbalance measures changes caused by book events. Signed executed volume measures completed transactions. They are related but different observations.

Begin with a small feature set: signed trade pressure, depth-adjusted book pressure, replenishment after depletion, and the price response during completed windows. Ask whether positive pressure produces a weaker recovery than comparable negative pressure produces a decline, after accounting for volatility and depth. An estimated response coefficient or matched-event comparison is safer than dividing returns by near-zero signed volume.

Do not count correlated measurements as independent votes. Negative price momentum, selling imbalance and a falling VWAP may all reflect the same recent move. The empirical question is whether the added feature improves future outcomes after the price-only information is already included.

The feed determines what is possible. Aggregate L2 snapshots can support depth and coarse response measures. They cannot reconstruct every individual order's lifetime, cancellations or modifications. Exact lifecycle analysis requires suitable event messages and order identifiers. At decision time, use age-so-far and modifications-so-far; an order's eventual lifetime and later execution are future information.

## Define what the indicator is estimating

Let $\mathcal I_t$ contain information actually received and usable at decision time $t$. For a horizon $h$, define

$$
R_{t,h}=\frac{F_{t+h}-F_t}{0.01}.
$$

For illustrative symmetric estimated round-trip friction $c_t$ in ticks, a directional forecast could be

$$
p_t^- = \Pr(R_{t,h}<-c_t\mid\mathcal I_t),
\qquad
p_t^+ = \Pr(R_{t,h}>c_t\mid\mathcal I_t),
\qquad
I_t=p_t^+-p_t^-.
$$

The probability between those boundaries is the chance that the midpoint move does not clear that cost threshold. This is a target definition, not a calibrated model. Actual evaluation should use side-specific bid/ask executions and latency rather than treating a midpoint forecast and a constant cost as a complete fill simulator.

Moreover, directional probability alone is insufficient: a high chance of a small gain can coexist with negative expected profit if occasional losses are large. Track expected net move, adverse excursion and uncertainty alongside the direction estimate.

With the currently described history, begin with an auditable evidence indicator: upward continuation, downward continuation, range/rotation, or insufficient/conflicting evidence. Show its component observations and their freshness. Do not label an arbitrary weighted score “82% probability.” Probabilities require subsequent calibration on unseen sessions.

A compact display could say: “Downward continuation evidence; US/CAD duration aligned; recovery attempts weak; swap confirmation unavailable; evidence weakening as bid replenishment rises.” That is an example of the information to display, not a reading of today's market.

## Accumulate evidence sequentially

Karim's sequential-testing idea can be illustrated with a simple drift detector. Let

$$
z_t=\frac{x_t}{\widehat\sigma_{t-1}},
$$

where the scale is positive and estimated from earlier observations. Under an illustrative null $z_t\sim N(0,1)$ and a downward alternative $z_t\sim N(-\delta,1)$, with $\delta>0$, the single-observation log-likelihood ratio is

$$
\ell_t^-=\log\frac{f_{-\delta}(z_t)}{f_0(z_t)}
=-\delta z_t-\frac{\delta^2}{2}.
$$

A resettable accumulation is

$$
S_t^-=\max\left(0,S_{t-1}^-+\ell_t^-\right).
$$

Repeated negative surprises raise the accumulated evidence; contradictory observations reduce it. This is a CUSUM-style illustration, not the exact backward-confidence-sequence method cited below and not a calibrated CGB alarm. Intraday dependence, changing volatility and scheduled announcements invalidate a casual transfer of independent-Gaussian false-alarm thresholds. Detecting an existing drift also does not establish that it will continue; that remains the forecast test.

## Use the short histories without overstating them

Develop a core using the futures history that actually overlaps. Keep swaps/OIS as an optional observation layer while collecting more sessions. Do not reduce a month of usable futures data to four days merely to obtain a rectangular feature table. Do not backfill missing swaps or silently carry stale quotes forward.

On the four overlapping sessions, compare the futures core and the core plus swaps on the same observations. This can reveal data problems and whether the proposed interpretation occurs at all. It cannot establish robust performance across policy regimes and market conditions. Thousands of correlated intraday rows do not create thousands of independent trading days.

Immediate useful work is replay, alignment, event annotation and falsification of simple hypotheses. Separate whole sessions chronologically into development and subsequent evaluation. Keep training labels whose future horizon extends into the next evaluation segment out of training. Fit normalizers, thresholds and model parameters using past data only. Random row splits would mix overlapping events and market states across both sides.

Start with three comparisons: a simple price-momentum rule; the same rule with a defined VWAP recovery/rejection condition; and that same setup with duration confirmation and flow-response features. Keep the decision times comparable. Examine net executable outcomes, adverse excursion, coverage, detection delay and whether the improvement survives removing the strongest day. Use day-level uncertainty estimates and recognize that a month still produces wide uncertainty.

Timestamp receipt and event times, specify the session reset, retain quote age, handle futures rolls explicitly, and distinguish actual trades from indicative rate marks. If the alleged edge disappears after these corrections or reasonable costs, that is a useful research result.

## Papers to read for this specific problem

1. [The Price Impact of Order Book Events — Cont, Kukanov and Stoikov](https://arxiv.org/abs/1011.6402). In US equities, the authors link short-interval price changes to order-flow imbalance, with impact related to depth. This motivates measuring pressure together with liquidity. It is not evidence that the same measurement forecasts profitable CGB continuation fifteen minutes later.

2. [Trade arrival dynamics and quote imbalance in a limit order book — Lipton, Pesavento and Sotiropoulos](https://arxiv.org/abs/1312.0514v1). The model relates bid/ask queue dynamics and quote imbalance to market-event probabilities. It is relevant to immediate event timing and book state; a session-long momentum claim needs separate evidence.

3. [Order-Flow Filtration and Directional Association with Short-Horizon Returns — Anantha, Jain and Maiti](https://arxiv.org/abs/2507.22712v2). This paper is in the new repository. Across three selected BankNifty futures sessions, standing-book filters show modest/inconsistent gains, while selected executed-order measures show stronger directional association. It is a diagnostic study, not a demonstrated CGB trading strategy. Any adaptation of its lifecycle filters must respect information availability.

4. [Sequential change detection via backward confidence sequences — Shekhar and Ramdas](https://arxiv.org/abs/2302.02544). This supplies a formal framework for ongoing change detection and false-alarm/detection-delay guarantees under its assumptions. It is relevant to when evidence warrants changing the indicator's state. It does not provide a ready-made financial predictor. The [published version](https://proceedings.mlr.press/v202/shekhar23a.html) uses “Changepoint Detection” in its title.

5. [Towards a Systems Theory of Algorithms — Dörfler and coauthors](https://arxiv.org/abs/2401.14029v2). This is the architecture/philosophy connection: view an algorithm as a dynamic component interacting with its environment. For this application, observation, state estimation, forecasting, execution and monitoring should remain distinct. The paper is not empirical evidence of trading alpha.

The first two connect most directly to market microstructure, the third to data construction, the fourth to online state changes, and the fifth to system design. None establishes a particular CAD VWAP rule. These links were checked against their primary arXiv/PMLR pages during this review.

## What the downloaded code does and does not establish

The read-only code review covered all six notebooks, the database bridges and the model documentation. Its pipeline builds macro baskets, daily metrics, beta/spread features, structural transition matrices, future-regime forecasts and signal displays. It has eleven trend/range phase tags crossed with two engineered regimes, making 22 states. Its target forecasts graph labels at horizons one through five; a correct future label is not automatically a profitable future trade.

The implementation is daily: it uses 252-observation memory, daily schemas and daily annualization. Its current training constants include 400 minimum training observations and 160 minimum test observations. The inspected notebook sources do not implement CGB contract risk, OIS, VWAP or L2 processing. Intraday use requires a new data contract and an explicit target, not simply substituting minute bars.

Historical console logs exist in notebook 5, including positive and negative reported Sharpes. The downloaded copy lacks the underlying database/data/output artifacts needed to reproduce those results. Some feature names are expressly marked in code as proprietary proxies rather than academic estimators.

There is also a concrete source-level timing concern. In notebook 5, zero-based JSON cell 146 computes posterior inputs using the current close-to-close return, extracts the same indexed posterior rows, and passes them to the backtest. Cell 76, lines 75–78, uses current-index confidence to scale the close-to-close return ending at that index. An after-close estimate cannot retrospectively choose the size held over the interval that just ended. This channel requires correction and a rerun before the reported performance can support an alpha claim. Its numerical impact was not measured, and the correspondence between saved logs and current code is unverified.

The relevant transferable structure is recognition of the current phase, prediction of a future outcome, and execution after that prediction becomes available. Keep those three timestamps separate in the CAD project.

## Source and decision record

**Fichiers consultes :** `0 README_MODEL.md`, `0.1 AGENTS.md`, `0.2 README_THESES.md`, relevant agent protocol files, `requirements.txt`, notebooks 1–6, `fractal_db.py`, `matrices.py`; the thesis inventory; in-depth reading of PHYSICS 01–06 and the relevant sections of CYBERNETICS 29. The whole thesis corpus was not line-by-line validated.

**Sections ou passages utilises :** PHYSICS 01 on the beta reference; PHYSICS 02–03 on selected exposures and changing constraints; PHYSICS 04 on sequential evidence and absorption; PHYSICS 05–06 on reference frames and stationarity; CYBERNETICS 29 on filtration and its limited empirical sample. Notebook 5 cells 76, 109, 125 and 146 were used for the mathematical/timing audit; notebook 6 distinguishes current graph recognition from future predictions.

**Logique extraite :** distinguish exposure, environment, observable pressure, realized response, current-state recognition, future prediction and executable action. Use the physics language as a source of hypotheses, with empirical tests for the proposed financial relationships.

**Decision deduite :** research a small, causal CGB continuation indicator with a futures-based core and optional fresh swap/OIS context. Test whether flow-response asymmetry and cross-market confirmation add information beyond the price/VWAP setup.

**Incertitudes ou contradictions :** no supplied market data, unknown L2 granularity and timing, very short histories, no audited live alpha evidence, source-level backtest timing concern, and no evidence identifying the named firms' decision rules. Forecast horizon and feature thresholds remain design choices. No source repo files were changed and no model was executed.
