# CAD duration momentum — Step 1 mathematical specification

Historical baseline: this document records an earlier experiment. Use [the current model derivation](../../docs/10-structural-model-derivation.md) and [iteration protocol](../../docs/12-iteration-and-improvement.md) for active research.

Updated 24 September 2026. This document replaces the earlier conceptual Step 1 note with a mathematical contract. The intended holding window is one to four hours, based on the user's wording and subsequent adoption of that specification. The model is a live indicator for outright CGB duration. No market dataset has been supplied, no parameters have been estimated, and no predictive or trading performance has been established.

The accompanying [reference implementation](../reference/cad_momentum_step01.py) implements selected definitions and synthetic consistency checks. It is not a fitted indicator or a market-data loader. The original Fractal X repository is unchanged.

## 1. Purpose and status of each mathematical statement

The question is: given information usable now, does an observed duration adjustment imply further useful CGB movement over the next one to four hours, and what adverse path could accompany it?

The source framework's contribution to this construction is the starting order: define the exposure and environment, construct a reference, then investigate departures and their propagation. The equations below are our explicit CAD application. Accepting that research framework does not supply measured Canadian coefficients or a validated CAD forecast.

We distinguish four kinds of statement throughout:

| Kind | Meaning | Example |
|---|---|---|
| Definition | We choose the object and its convention | Midpoint, residual, forecast horizon |
| Identity | Follows algebraically from the definitions | Common component plus residual reconstructs the observed move |
| Hypothesis | Needs evidence; can be wrong | Remaining pressure predicts subsequent local movement |
| Design convention | Chosen to make the research reproducible | Fixed contract, as-of execution benchmark, horizon grid |

No identity below is evidence of forecasting skill. Our sign tables enumerate the cases of the declared coordinates; they do not claim to enumerate every possible economic mechanism.

**Decision:** the research target is future CGB movement and its path. CAD–US relationships, the Canadian curve, swaps and liquidity are explanatory observations, not mandatory extra traded legs. We do not define momentum by a VWAP pattern or by the name of an account.

## 2. Notation, units and clocks

| Symbol | Definition | Unit |
|---|---|---|
| $t$ | Decision time | Timezone-aware timestamp |
| $k$ | Index of a completed observation interval | Index; interval length not yet selected |
| $\ell$ | Assumed decision-to-entry delay | Time |
| $e=t+\ell$ | Scheduled entry benchmark time | Timestamp |
| $x=e+h$ | Scheduled exit benchmark time | Timestamp |
| $b_u,a_u$ | Usable bid and ask of the frozen CGB contract | Quoted price points |
| $m_u=(b_u+a_u)/2$ | Midpoint | Quoted price points |
| $\tau=0.01$ | CGB quoted tick size | Price points/tick |
| $V=10$ | CGB tick value | CAD/contract/tick |
| $d\in\{-1,+1\}$ | Short or long direction being evaluated | Sign |
| $Q$ | Quantity in an execution benchmark | Contracts |
| $\Delta y_j$ | Yield change at tenor $j$ over a declared interval | Basis points |
| $\mathcal F_t$ | Information available to the model at $t$ | Information set |

The tick size and value come from [Montréal Exchange's CGB specification](https://www.m-x.ca/en/markets/interest-rate-derivatives/cgb). A midpoint may lie on a half tick. Do not round midpoint returns to whole ticks. For one contract, a one-point price change is CAD 1,000. These price mechanics do not determine the contract's current DV01.

The primary horizon range is one to four hours. For reproducible illustrations we use $\mathcal H=\{60,120,240\}$ minutes, a declared grid within that range. This does not establish that one of those horizons is best, and the research must not choose the winning horizon after looking at outcomes.

Observation frequency, feature lookback, forecast horizon and execution latency are four different clocks. An event-level input can support an hourly question, but its usefulness at that horizon must be demonstrated.

## 3. What can be known at the decision time?

For a record $i$ and its revision $v$, retain the observed/event time $o_i$, available-at time $a_{i,v}$, value $z_{i,v}$, source and version identity. Define

$$
\mathcal F_t=\sigma\{(i,v,z_{i,v},o_i,a_{i,v}):a_{i,v}\le t\}.
$$

This is the information boundary. A feature used at $t$ must be $\mathcal F_t$-measurable. A position held over the following interval must be determined before earning that interval's return. In discrete-time terminology, information known at the current close supports an adapted current estimate and a decision for a subsequent interval; it does not retrospectively determine the position over the interval just ended.

If a 09:00 observation is corrected at 10:00, the 09:30 decision uses the version available at 09:30. The later correction can be preserved in the archive without rewriting the decision snapshot. A late correction to an old event also must not replace a newer observation merely because it arrived later.

For a derived feature,

$$
a_{\mathrm{derived}}\ge\max_i a_{\mathrm{input},i},
$$

with additional processing delay included. Ties between observations and decisions require an explicit sequence convention; equal coarse timestamps do not prove availability in the right order. Historical reconstruction must preserve vendor vintages where applicable.

A useful consistency requirement is prefix invariance: with the model version and fitted parameters frozen, appending future records must leave already issued historical feature values unchanged. Re-estimating the entire historical model after new data arrives is a different operation and must not overwrite the original forecast record.

**Objection:** exchange event time is precise, so why retain receipt time? Because the model cannot react before the event becomes available to it. Clock errors, reporting delay and data processing can otherwise appear as predictive lead–lag.

**Decision:** all model inputs are reconstructed as known at the decision. Future outcomes live in separate records and mature only once the required observations are available.

## 4. Fix the contract and eligible horizon

Let $c_t$ be the CGB contract selected using information at decision time. The entry, exit and path for this observation must refer to the same contract $c_t$. A front-contract switch is not a return of that fixed position. Historical rolls need their own declared treatment.

Let $S$ be the account's operating-session start and $T_{\mathrm{flat}}$ its chosen flat-by time. Define planned horizon eligibility:

$$
E_{t,h}=\mathbf1\{S\le t,\ t+\ell+h\le T_{\mathrm{flat}}\}.
$$

The account's operating session is not assumed identical to the exchange's full trading session. Exact session parameters remain unset.

If only two hours remain, a four-hour outcome is ineligible under this intraday contract. We do not truncate it to two hours and preserve its four-hour label. A later halt, data gap or unusable exit snapshot makes the relevant outcome unavailable/censored. It does not imply a zero return.

For the initial execution benchmark, use valid as-of quotes at scheduled $e$ and $x$, subject to an explicit freshness limit. If those quotes are unusable, mark the benchmark unavailable. A first-valid-quote-after-target policy is a different benchmark with different entry/exit timestamps; it is not silently substituted here. Actual fills, when available, require separate accounting with actual timestamps.

## 5. Three meanings of beta

| Meaning | Our object | What it does not imply |
|---|---|---|
| Carried exposure | Outright CGB duration | A second traded leg is required |
| Shared movement | A candidate common-duration component | US movement is necessarily the causal origin |
| Regression coefficient | A unit-aware relationship estimated from earlier observations | The residual is stationary, profitable, or future-independent |

Positive CGB price movement is favorable to a long position; rising yields generally have the opposite sign under a local positive-duration approximation. A cash ten-year yield is not an exact futures-price transformation. Delivery-bond choice, conversion factors, basis and key-rate sensitivities matter if we later map price movement into yield risk.

**Decision:** retain price ticks as the primary CGB outcome unit. Use consistent basis-point units for yield/curve observations. Any DV01 conversion needs its own dated inputs and assumptions. No current DV01 is invented.

## 6. Common duration and local deviation: a complete sign partition

Over a completed interval, define the CGB move in ticks $r_k^C$, a chosen US move $r_k^U$ in declared units, and a coefficient estimated strictly before that interval:

$$
c_k=\widehat\beta_{k-1}r_k^U,
\qquad e_k=r_k^C-c_k,
\qquad r_k^C=c_k+e_k.
$$

The coefficient has units of CGB ticks per US move unit. The last equality is an identity because the residual is defined by subtraction. It explains a completed interval, not the next one. Future US returns cannot be inserted as if known now.

| Common $c_k$ | Local $e_k$ | Outright CGB implication |
|---:|---:|---|
| Positive | Positive | Positive; components reinforce |
| Positive | Zero | Positive; all measured movement is common |
| Positive | Negative | Depends on magnitudes; positive, zero or negative are possible |
| Zero | Positive | Positive; all measured movement is residual |
| Zero | Zero | Zero measured movement |
| Zero | Negative | Negative; all measured movement is residual |
| Negative | Positive | Depends on magnitudes; positive, zero or negative are possible |
| Negative | Zero | Negative; all measured movement is common |
| Negative | Negative | Negative; components reinforce |

Zero here means numerical zero in the mathematical partition. A practical near-zero band is a separate parameter. Missing data never occupies the zero row.

The illustrative combinations $(-4,0)$, $(0,-4)$ and $(+2,-6)$ all produce a four-tick CGB decline. Opposing components that sum to zero can represent substantial activity even though the endpoint is flat. Repeated cancellation is not the same observation as both components being inactive.

**Objection:** a large residual proves a local opportunity. It does not. It may reflect a local disturbance, a stale quote, a poor coefficient, a changed relationship or omitted common information. The coefficient's estimator and stability are later research decisions.

**Decision:** use both components as coordinates; do not hedge away the common component merely because it is common.

## 7. Canadian curve coordinates without losing direction

Let $(\Delta y_2,\Delta y_5,\Delta y_{10})$ be synchronized changes in comparable CAD yields, all in bp. Choose a transparent invertible representation:

$$
L_5=\Delta y_5,
\qquad s_{25}=\Delta y_5-\Delta y_2,
\qquad s_{510}=\Delta y_{10}-\Delta y_5.
$$

Then

$$
\Delta y_2=L_5-s_{25},\qquad
\Delta y_5=L_5,\qquad
\Delta y_{10}=L_5+s_{510}.
$$

This is lossless bookkeeping. $L_5$ is a five-year anchor, not an estimated common factor, orthogonal principal component or proven parallel shift. It is chosen to keep the distinction between direction and rotation explicit.

Examples for $s_{25}$:

| 2y change | 5y change | Slope change | Interpretation at those two tenors |
|---:|---:|---:|---|
| +5 | +2 | −3 | Both yields rise; flattening |
| −1 | −4 | −3 | Both yields fall; flattening |
| +2 | +5 | +3 | Both yields rise; steepening |
| −4 | −1 | +3 | Both yields fall; steepening |
| +2 | −2 | −4 | Opposite directions; flattening |
| −2 | +2 | +4 | Opposite directions; steepening |
| +2 | +2 | 0 | Parallel rise at these tenors |

None determines the ten-year move. The exact reconstruction covers all real-valued combinations, including unchanged and mixed-tenor cases beyond the examples.

Cash yields, OIS par rates, swap rates and forward-starting rates need instrument/convention labels; they are not interchangeable because their maturity labels match. If a set of forwards is derived from a common curve $z_t$, write $f_t=g(z_t)$. This makes their shared information origin explicit. More derived columns do not establish more independent observations.

## 8. Observable environment and hidden mechanism

The proposed observation vector is grouped by role:

$$
O_t=(O_t^{CGB},O_t^{CAD\ curve},O_t^{US},
O_t^{swaps/OIS},O_t^{book/trades},O_t^{context}).
$$

This notation is a schema, not a commitment to concatenate every field into a learner. Each block retains its source, unit, timestamps, validity and coverage.

| Observable when provided | What it can help describe | Latent claim it does not directly measure |
|---|---|---|
| Price/yield changes | Realized repricing | Remaining institutional orders |
| Signed completed trades | Aggressor-side activity under a defined classification | The participant's full portfolio intention |
| Displayed depth/updates | Quoted liquidity and its observed changes | All latent liquidity or committed future depth |
| Relative market movements | Common participation and divergence | A uniquely identified causal transmission path |
| OIS/forward changes | Changes in the particular quoted curve | Independent policy forecasts from each derived tenor |
| Reported named flow | A timestamped report | The institution's full strategy or private model |

Aggregate L2 snapshots support different claims from order-by-order event messages. Individual order lifetime/modification analysis requires suitable identifiers and events. Eventual lifetime is future information; only age and modifications observed so far are usable live. Trade signing itself may be inferred rather than supplied and must retain that provenance.

## 9. A minimal mathematical expression of pressure and absorption

This section proposes a small model family to expose assumptions. It does not choose a fitted state-space model for production.

Let $p_k$ denote latent remaining effective local duration pressure that can influence the next interval, positive for upward CGB pressure. Let $\kappa_k\ge0$ be sensitivity in CGB ticks per pressure unit. A candidate local response model is

$$
e_{k+1}=\kappa_k p_k+\eta_{k+1},
\qquad p_{k+1}=\rho_k p_k+u_{k+1}.
$$

Here $u$ is new pressure innovation, $\rho$ describes persistence/feedback at the selected interval length, and $\eta$ includes other local influences and measurement error. This pressure is not simply declared equal to the latest signed trade volume. The observation relationship between trades/book and $p_k$ is not yet established.

Smaller $\kappa$ means a given pressure generates less movement within this simplified component. We can interpret that as stronger effective absorption only after considering competing influences. If an estimated coefficient is negative, inspect timing, sign conventions and the model hypothesis; do not clip it and declare the absorption story proved.

The simplest identifiability problem is already visible:

$$
\kappa p=(\kappa/c)(cp),\qquad c>0.
$$

Price response alone cannot distinguish larger pressure from greater sensitivity. Additional observations and a scale convention are necessary. Even with L2, the hidden state may remain only partly identifiable.

Under the additional illustrative assumptions that $\rho,\kappa$ stay fixed over the horizon and future innovations have zero conditional mean, the expected cumulative local response over $H$ intervals is

$$
\mathbb E\!\left[\sum_{j=1}^{H}e_{k+j}\mid\mathcal F_k\right]
=\kappa\widehat p_k\sum_{j=0}^{H-1}\rho^j
=\begin{cases}
\kappa\widehat p_k(1-\rho^H)/(1-\rho),&\rho\ne1,\\
H\kappa\widehat p_k,&\rho=1,
\end{cases}
$$

where $\widehat p_k=\mathbb E[p_k\mid\mathcal F_k]$. No such estimate exists yet. If coefficients are uncertain and vary, the relevant expectation contains joint products; multiplying separate means is not generally justified.

This equation explains why the forecast horizon matters. A strong short-lived response can have little additional expected movement left after the first intervals. A smaller persistent response can accumulate over hours. It is not enough to observe a large current impact.

| Persistence case | Consequence within this illustrative model | Research objection |
|---|---|---|
| $\rho=0$ | Existing pressure contributes once, then vanishes absent new input | A recent move need not imply a long holding opportunity |
| $0<\rho<1$ | Same-sign influence decays | How quickly, and is the remainder larger than costs? |
| $\rho=1$ | Influence persists under frozen assumptions | Why should coefficients and constraints remain unchanged? |
| $\rho>1$ | Same-sign amplification | Local feedback can amplify, but an unbounded long-run extrapolation is unjustified |
| $-1<\rho<0$ | Alternating, decaying response | A monotone trend description is inappropriate |
| $\rho=-1$ | Persistent alternation | Endpoint behavior depends on horizon parity |
| $\rho<-1$ | Alternating amplification | The fixed-coefficient model is unstable and needs a limited domain |

For $p>0$, $\kappa>0$ gives positive local expected response; $p<0$ gives negative local response; $p=0$ or $\kappa=0$ removes this component. Common duration and other components can still move CGB in every case. Low observed movement does not identify which factor is small.

In a fixed-coefficient special case with independent, zero-mean pressure innovations of variance $\sigma_u^2$, $|\rho|<1$ admits stationary pressure variance $\sigma_u^2/(1-\rho^2)$ under the appropriate stationary initialization. That conditional mathematical result does not establish stationarity of CGB prices, the observed residual, or actual market pressure.

The reference condition is: if the local remaining-pressure component has zero conditional mean and the residual error does too, this model supplies no local expected drift. Common duration may still supply an outright move. This is our explicit reference hypothesis, not a universal market invariance.

## 10. Competing explanations and their discriminating questions

| Explanation | Mathematical representation to investigate | What weakens the explanation | What remains ambiguous |
|---|---|---|---|
| Continuing local adjustment | Nonzero $\widehat p$, continuing input $u$, and response not fully offset | Observed pressure repeatedly produces less subsequent movement and stronger recovery | It may continue through another channel |
| Continuing common repricing | Future common-duration movement contributes materially | Common movement stops supporting CGB and no local continuation emerges | A shared shock need not be caused by the US instrument |
| Completed adjustment in a channel | Little remaining conditional response in that channel | Subsequent sustained supported movement remains forecastable from current observations | New shocks can arrive after completion |
| Liquidity disturbance | Changing $\kappa$ for comparable measured pressure proxies | Response is unchanged when liquidity conditions normalize | Proxy pressure may also have changed |
| Curve/basis rotation | Relative coordinates change without a corresponding broad move | Broad outright duration dominates the account's outcome | Rotation and an outright move may coexist |
| Mixed/unidentified | Several explanations fit the same observations | Additional independent observations discriminate them | Better prediction does not guarantee causal identification |

These are overlapping mechanism hypotheses. They are not automatically a softmax with probabilities summing to one. Completed repricing in one channel can coexist with continuing adjustment in another. No observation above is a decisive causal experiment by itself.

Our strongest research question is whether observed pressure-response and cross-market distinctions add information about future CGB outcomes after accounting for the price setup. A meaningful failure would be that they only describe the interval already completed, or add nothing beyond the baseline at the chosen horizon.

## 11. VWAP events: freeze what can be known

For actual trades $(p_i,q_i)$ within a declared session and available by $t$,

$$
VWAP_t=\frac{\sum_i q_i p_i}{\sum_i q_i}.
$$

No positive traded volume means this VWAP is undefined. Bar approximations must be labeled as approximations. Any dispersion band needs an explicit formula; a chart's one-standard-deviation line is not automatically a probability boundary.

A rejection is a sequence, not an instant. Define an approach time $\tau_a$, an explicit reference convention (moving VWAP or frozen at approach), and a causal confirmation predicate $C$. Then

$$
\tau_c=\inf\{s>\tau_a:C(O_{\le s};\theta)=1\}.
$$

The parameters $\theta$ and reference convention must be declared before outcomes. If the event is not confirmed, it is not a confirmed rejection. The signal becomes available at confirmation, allowing processing latency; it cannot be entered retrospectively at the approach price.

At least four cases must remain distinct: an approach followed by successful reclaim; an approach followed by observed failure; no approach during a continuing move; and an approach that is unresolved because of insufficient time or data. The no-approach case can still contain momentum. Observed failure with meaningful buy-initiated activity differs from an absence of buying; trade data are needed to distinguish them.

## 12. Define the future outcome and its path

For a fixed anchor $a$, direction $d$, horizon $h$ and the same CGB contract, define the directional midpoint path:

$$
Z^d_a(u)=d\frac{m_{a+u}-m_a}{\tau},\qquad 0\le u\le h.
$$

Then

$$
R^d_{a,h}=Z^d_a(h),\qquad
MFE^d_{a,h}=\max_{0\le u\le h}[Z^d_a(u)]_+,
\qquad MAE^d_{a,h}=\max_{0\le u\le h}[-Z^d_a(u)]_+.
$$

An anchor of $a=t$ gives a decision-time diagnostic. An anchor of $a=e$ gives an entry-time midpoint diagnostic. They are different labels. Movement during latency belongs to the first but is not earned by the trade entered later. The implementation takes an ordered midpoint path anchored by its first observation; the caller must supply the declared anchor and complete horizon.

| Future path relative to anchor | Endpoint | Excursion interpretation |
|---|---|---|
| Monotone favorable movement | Favorable | Little/no midpoint MAE |
| Adverse movement followed by favorable endpoint | Favorable | Potentially large MAE |
| Favorable movement followed by full reversal | Flat/adverse | MFE can be large despite poor endpoint |
| Little movement throughout | Near zero | Small observed excursions |
| Repeated large moves ending near anchor | Near zero | Both MFE and MAE can be large |
| Missing endpoint or incomplete path | Unavailable for affected target | Never infer zero movement or a safe path |

For a hypothetical short, both paths $120.00\to119.96\to119.90$ and $120.00\to120.30\to119.90$ end +10 ticks in the chosen direction. Their midpoint MAE values are 0 and 30 ticks. Equal endpoints do not imply equal usefulness.

On sampled data, these are observed extrema. Gaps can hide worse excursions. MFE is not an executable profit from an oracle exit; OHLC extrema alone also do not determine which barrier was hit first.

Labels use fixed anchors, directions and ex-ante conventions together with subsequent realizations. None of those subsequent realizations may enter the same decision's features. If the endpoint exists but intermediate data are missing, the endpoint target may be valid while the path target is unavailable; validity belongs to each target separately.

## 13. Executable benchmark and costs

For $Q$ contracts, usable quotes at scheduled $e$ and $x=e+h$, and adequate displayed size, the quote-touch benchmark is:

$$
G^+_{t,h}=QV\frac{b_x-a_e}{\tau}-C^+_{t,h},
\qquad
G^-_{t,h}=QV\frac{b_e-a_x}{\tau}-C^-_{t,h}.
$$

Here $C$ contains fees and modeled additional slippage beyond quoted prices. Bid/ask crossing already accounts for the quoted spread. Do not charge it again. One explicit convention is

$$
C^d_{t,h}=Q\bigl(f^d_{\mathrm{roundtrip}}+V\,s^d_{\mathrm{extra}}\bigr),
$$

where $f$ is CAD per contract and $s$ is additional round-trip slippage in ticks. This is a small-size reference, not a general linear market-impact law.

At an unchanged one-tick-spread market, either direction loses one tick before fees. If the midpoint stays unchanged but the spread widens, the midpoint label stays zero while liquidation becomes more expensive. If size exceeds displayed liquidity, the top-of-book benchmark is unsupported; deeper-book execution or an impact model is required. Displayed size sufficiency does not guarantee a fill because of latency, cancellation and competition.

The benchmark assumes a fresh entry from flat followed by exit. Managing an existing position requires a different comparison, including the incremental cost of holding, closing or reversing. No automated order placement, portfolio sizing or stop policy is specified here.

## 14. The prediction object and the research null

For an eligible horizon, the desired object is a conditional distribution such as

$$
\mathcal L\left(R^d_{e,h},MFE^d_{e,h},MAE^d_{e,h},G^d_{t,h}
\mid\mathcal F_t,E_{t,h}=1\right).
$$

Entry prices and future fills are uncertain at decision time; their eventual realizations are part of the outcome, not inputs. No distributional family or calibrated probabilities have been chosen.

A possible later path-aware event is

$$
A^d_{t,h}=\{G^d_{t,h}>g_*,\ MAE^d_{e,h}\le a_*\},
$$

with the profit and midpoint-excursion thresholds fixed before evaluation. The two thresholds have different units. This event is a descriptor, not a stop-order simulation. The thresholds are unset. Even a high probability of a favorable event is insufficient if losses outside it are large; expected payoff and tails remain relevant.

Let $B_t$ be a declared price/context baseline and $X_t$ the proposed added environment/response observations. For the outcome vector $Y$, a strong informational null is

$$
H_0:\quad\mathcal L(Y\mid B_t,X_t)=\mathcal L(Y\mid B_t).
$$

Rejecting a suitable version of this null would support incremental predictive information under the tested conditions. It would not identify the physical mechanism or establish executable profits. A risk predictor can add distributional information without improving mean return; that contribution must be named accurately.

With a month of futures and roughly four swap sessions, the specification can be implemented and challenged, but stable model performance is unestablished. Core and optional-input comparisons must use the same overlapping periods when attributing differences to the optional input. Closely spaced and overlapping forecasts do not constitute independent sessions.

## 15. Balance, uncertainty and missing information

Keep at least three output attributes separate:

$$
\text{output}_{t,h}=
(\text{directional forecast},\text{uncertainty},\text{data status}).
$$

Data status is itself a vector across input blocks; disagreement among valid observations is another useful diagnostic. These attributes are not mutually exclusive market regimes.

| Situation | Meaning | Incorrect substitution |
|---|---|---|
| Valid observations; little predicted net movement | Estimated directional balance | Guaranteed quiet market |
| Valid but conflicting observations | Mixed evidence | Average them into false confidence |
| Broad/noisy future distribution | Outcome uncertainty | A precise zero forecast |
| Missing/stale/invalid critical observation | Measurement limitation | Zero pressure or flat price |
| Missing optional swaps | That channel is unavailable | Disable all futures history or invent swaps |

We do not yet have a calibrated uncertainty model. Arbitrary score dispersion is not automatically a probability of being wrong. Which feeds are critical for which output remains a declared operating choice.

## 16. Measurement contract and reference implementation

Every scalar observation needs instrument/contract, measured quantity, unit, observed time, available-at time, source/version and validity. For trades and order-book reconstruction, event type, identifiers, sequence numbers and appropriate sizes are additionally required. The reference scalar selector does not reconstruct L2.

For age $A_j(t)=t-o_j^*(t)$ of the latest eligible observation and source-specific freshness limit $\eta_j$, a basic usability condition is

$$
M_j(t)=\mathbf1\{\text{record exists, valid, available by }t,\ A_j(t)\le\eta_j\}.
$$

Source/version/order conventions remain necessary beyond this simple indicator. Freshness limits differ across feeds and cannot be set honestly from their names alone.

The reference implementation includes:

| Function | Object implemented |
|---|---|
| `asof_reading` | Scalar vintage-aware availability, revision order and missing/stale/invalid distinctions |
| `horizon_eligible` | Full horizon after latency must fit the operating session |
| `common_local` | Observed common/residual decomposition |
| `curve_coordinates`, `reconstruct_curve` | Exact five-year-anchor/two-slope transformation |
| `path_outcome` | Directional endpoint and observed MFE/MAE |
| `quote_touch_pnl` | Same-contract, fresh-quote, size-aware quote-touch benchmark and explicit costs |
| `frozen_pressure_response` | Geometric response under stated hypothetical frozen coefficients |

The code has no trained model, signal weights, live feed, estimated beta, L2 reconstruction or calibrated latent state. Input order/path completeness and external session calendars are caller responsibilities. Numerical tests cannot validate economic assumptions.

Run the synthetic checks with:

```powershell
python -X utf8 C:\Users\mn262\Downloads\math\cad_momentum_step01.py
```

There are 16 tests, including nested checks of all nine common/local sign pairs and 27 curve-change combinations. They address revisions, delayed records, missing versus zero, invalid timestamps, session truncation, opposite directions, half ticks, unequal adverse paths, unchanged-price trading losses, spread widening, latency, fees, slippage, contract changes, stale quotes, insufficient displayed size and pressure-model boundary cases. Passing these establishes internal consistency of the selected definitions on the supplied examples, not market performance.

## 17. Decisions, assumptions and unresolved parameters

| Item | Status | Consequence |
|---|---|---|
| Outright CGB target | Defined | Other markets explain rather than replace the traded object |
| One-to-four-hour range | Adopted working objective | Illustrations use 1/2/4 hours, without selecting a winner |
| Units/signs and curve reconstruction | Defined and checked synthetically | No silent price/yield or slope/direction confusion |
| Information and fixed-contract boundary | Defined; examples checked | Real provider timing/version conventions still needed |
| Outcome versus executable benchmark | Defined and checked synthetically | Actual execution costs/fills remain unmeasured |
| Pressure-response equations | Hypothetical model family | No estimated pressure, sensitivity or persistence |
| Common/local estimator | Unselected | Residual is an observable construction once a coefficient is supplied |
| Input feed granularity/coverage | Unknown | Cannot claim lifecycle reconstruction or particular sampling fidelity |
| Operating session/flat-by time | Unset | No live eligibility decisions yet |
| Latency and freshness limits | Unset | No claim that historical quotes were actionable |
| Actual contract/roll convention | Unset | No continuous-series backtest yet |
| Fees, size and extra slippage | Unset | Synthetic numbers are examples only |
| Risk/excursion thresholds | Unset | No deployment decision rule yet |
| Predictive edge | Untested | No claim of a validated momentum indicator |

Step 1 is complete as a parameterized mathematical specification. It is not operationally instantiated until the required feed/session/execution parameters are supplied. Step 2 concerns measurable estimators and features for the specified objects; it must not quietly redefine the target to improve a result.

## 18. Source and reasoning record

**Files inspected :** previous Step 1 note; Fractal X PHYSICS 01–04 and the earlier notebook/model audit, with PHYSICS 03–04 revisited for this specification; gitos-lenses causal-deployment-ordering and evidence-reproducibility-reporting; official CGB specification.

**Passages used :** environment and beta in [01 beta.md](../../logic/physics/01-beta.md); exposure coordinates in [02 smart beta.md](../../logic/physics/02-smart-beta.md); hidden state and propagation in [03 zureck.md](../../logic/physics/03-zureck.md); information timing and absorption in [04 zureck vs laplace.md](../../logic/physics/04-zureck-vs-laplace.md).

**Extracted logic :** define exposure, environment, reference and information boundary before a signal; connect structural names to measurable objects; distinguish current explanation from a forecast and a forecast from executable results. These methodological connections are supported by the [deployment lens](https://github.com/wizzo-gmb/gitos-lenses/blob/main/causal-deployment-ordering.md) and [evidence lens](https://github.com/wizzo-gmb/gitos-lenses/blob/main/evidence-reproducibility-reporting.md).

**Derived decision :** retain outright CGB as the outcome; preserve common/local/curve coordinates; represent pressure-response as a testable family rather than a measured fact; use causal timestamps and separate path and execution outcomes. Algebraic derivations and the small linear pressure model in this document are our CAD design, not quotations from the original notebook or a claimed application of a proven CAD law.

**Uncertainties or contradictions :** no market data inspected; mechanisms underidentified; temporal/execution parameters unset; no numerical forecasts, likelihood calibration or profitability claim. Only synthetic consistency checks were run. The user's source repository was not modified.

## 19. Cognitive checklist

### Defined or checked in Step 1

- [x] The traded exposure is outright CGB duration.
- [x] Carried exposure, common movement and a hedge coefficient have separate meanings.
- [x] Price ticks, cash P&L and yield basis points are distinguished.
- [x] The observation clock, decision clock, entry latency and holding horizon are separate.
- [x] A later revision cannot enter an earlier decision snapshot.
- [x] The contract is frozen across an outcome window.
- [x] A four-hour target is not silently shortened at session close.
- [x] Missing or invalid information is not converted into a zero market observation.
- [x] The common/residual sign cases include agreement, opposition and cancellation.
- [x] Curve slope changes are accompanied by explicit yield-direction coordinates.
- [x] Pressure and sensitivity are not claimed to be identifiable from price alone.
- [x] Persistent flow and profitable future price movement are separate claims.
- [x] The pressure model's persistence cases and simplifying assumptions are explicit.
- [x] Mechanism hypotheses may overlap; they are not forced into exclusive probabilities.
- [x] VWAP approach, confirmation, failed confirmation and no approach are distinct.
- [x] Future path outcomes do not enter contemporaneous features.
- [x] Terminal movement, MFE and MAE are separate quantities.
- [x] Decision-time movement is not credited to a trade entered after latency.
- [x] Quote-touch costs do not double-count the bid/ask spread.
- [x] A high event probability is not equated with positive expected profit.
- [x] Synthetic arithmetic/timing checks are separated from empirical validation.

### Assumptions still requiring evidence

- [ ] Our observations contain information about remaining adjustment at a one-to-four-hour horizon.
- [ ] The chosen common-duration relationship remains useful on subsequent data.
- [ ] Pressure proxies help distinguish response strength from the amount of pressure.
- [ ] Added observations improve the declared baseline rather than duplicate it.
- [ ] Any latent-state or distributional assumptions are supported in the relevant domain.
- [ ] Gains survive subsequent sessions and plausible execution conditions.

### Parameters/data needed before live or historical operational claims

- [ ] Exact symbols, contracts, feed types and coverage inspected.
- [ ] Actual timestamp, revision and event-sequence conventions established.
- [ ] Trading session and flat-by policy specified.
- [ ] Latency, freshness and data-gap policies specified per feed.
- [ ] Trade/order-book granularity and aggressor-side classification established.
- [ ] Costs, quantity/capacity assumptions and roll treatment specified.
- [ ] Horizon priority and any path/risk thresholds fixed before evaluation.

Before accepting any future result, ask: are we looking at an observation, a constructed identity, a hypothesis, a forecast, or an executable outcome? Which part was known when the decision was made? What competing explanation remains? What would make us change the interpretation?
