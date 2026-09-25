# Building the CAD duration momentum model

Historical baseline: this document records an earlier experiment. Use [the current model derivation](../../docs/10-structural-model-derivation.md) and [iteration protocol](../../docs/12-iteration-and-improvement.md) for active research.

24 September 2026 · Research design and mathematical companion to **cad-duration-momentum.ipynb**

The object is a live estimate of the direction, magnitude and adverse path of **CGB over the next 60, 120 and 240 minutes**. Canadian yields, US duration, swaps, forwards and liquidity describe the environment of that exposure. Buying or selling a cash bond instead of a future is a subsequent execution and risk-mapping decision.

The notebook contains the implementation, with its market-data inputs deliberately empty. Its equations and transformations are research choices, not estimates from Canadian data. It has no measured trading performance. It is a new CAD application informed by the source framework; it does not replace or silently rewrite his six notebooks.

The most important decision is this: **describe the state of the market, forecast an observable future, and keep those two objects separate.** Otherwise a model can become extremely good at predicting the persistence of its own labels.

## 1. What I take from the source author, and what the code actually does

His useful starting question is about the system's reference and the conditions under which its behavior remains stable. For this account, the exposure is already chosen: Canadian duration through CGB. We do not need to discover a basket before studying that exposure.

The original pipeline nevertheless gives us an ordering worth retaining:

| Original stage | Actual work | CAD translation |
|---|---|---|
| 1 — leader universe | Select baskets, weights and leaders within an exposure environment | Freeze CGB as the forecast object; declare contextual instruments and units |
| 2 — metrics | Estimate return shape, tails, entropy and state descriptors | Measure multiscale movement, variability, directional efficiency and liquidity observations causally |
| 3 — beta | Build a reference basket relationship and departures from it | Keep observed common US duration and Canadian residual movement separately visible |
| 4 — matrices | Specify seven structural transition laws over 22 states | Inspect descriptive phase transitions; use an explicit estimated persistence model as a separate forecasting expert |
| 5 — model | Construct current graph states, forecast future states with XGBoost, combine with structural and Monte Carlo components | Forecast actual future CGB outcomes; combine a drift expert and an ML expert without pretending they are independent evidence |
| 6 — signals | Read persisted forecasts and expose the state/action view | Produce a timestamped indicator, path estimates, disagreement and data status |

There are **three kinds of learning** here. Rolling covariances and distribution fits already estimate quantities from data. A state tagger then imposes a representation. Supervised ML learns a mapping from that representation and other features to future outcomes. Saying that learning only starts at XGBoost misses the first two choices.

In the original, the supervised target is a future graph tag. That can be a legitimate target: the future tag requires future observations. But a manually persistent tag grammar can make tag accuracy look impressive without establishing useful price prediction. Our primary supervised target is therefore a future price outcome. Current phase remains an explanatory feature and a diagnostic.

We retain the distinction between reference, disturbance, response and state. We change the original daily horizon, universe, state vocabulary and final combination deliberately. A daily 252-observation memory is not a justified 252-minute memory merely because the number is convenient.

## 2. The physics: useful structure, then an observation problem

The Smart Beta essay models capital as a distribution over exposures, not as the path of a single investor. In its notation,

$$
\int_\Omega \rho(w,t)\,dw=1,
\qquad
H(w,\rho,F)=-w\cdot F+\frac{\gamma}{2}\lVert w\rVert^2+\lambda(K*\rho)(w).
$$

Here $w$ is an exposure vector; $F$ favors some exposures; the quadratic term penalizes concentration; the interaction kernel represents how crowding affects other participants. The proposed individual and population dynamics are

$$
dw_t=-\nabla_w H\,dt+\sqrt{2D}\,dB_t,
$$

$$
\partial_t\rho=\nabla_w\cdot(\rho\nabla_w H)+D\Delta_w\rho.
$$

There is a substantive mathematical idea behind this. For fixed coefficients, a symmetric interaction kernel, suitable regularity and no flux through the boundary, define

$$
\begin{aligned}
\mathcal F[\rho]
&=\int\left(-w\cdot F+\frac{\gamma}{2}\lVert w\rVert^2\right)\rho(w)\,dw\\
&\quad+\frac{\lambda}{2}\iint K(w-w')\rho(w)\rho(w')\,dw\,dw'
+D\int\rho(w)\log\rho(w)\,dw.
\end{aligned}
$$

Writing the evolution as a gradient flow gives

$$
\frac{d\mathcal F}{dt}
=-\int\rho\left\lVert\nabla_w\frac{\delta\mathcal F}{\delta\rho}\right\rVert^2dw
\leq0.
$$

This calculation explains the attraction of the dissipation language. It does **not** establish that a CGB position earns the negative derivative of this functional. P&L has units of money and requires holdings and executable prices. A chosen free-energy functional has its own units and assumptions.

Nor is the inequality unconditional when the environment changes. If $F$ and $D$ vary with time, additional explicit-time terms include

$$
-\dot F_t\cdot\mathbb E_{\rho_t}[w]
+\dot D_t\int\rho_t\log\rho_t\,dw.
$$

Those terms need not be negative. This is precisely why changes in the surrounding constraints matter.

The hard step is the observation map. We do not observe the distribution of all investors' duration exposure, their funding constraints, or their remaining orders. Four days of swap quotes do not reveal those hidden objects. A full mean-field model would require an identified measurement equation and estimates for its interaction structure.

Our smaller, testable interpretation is: **directional adjustment may persist, observation noise may hide it, and the relationship between context and subsequent movement may change.** We estimate an observable consequence of that idea. The notebook calls its hidden variable *drift*, because price data can support an estimate of conditional movement; calling it physical selling pressure would add an identification claim that the data have not earned.

The same discipline applies to quantum language. The repository's final implementation combines nonnegative scores and normalizes them. An amplitude-and-square construction can be mathematically well defined without identifying financial observations with measured quantum amplitudes. We can study its forecasting behavior without importing a physical theorem as a financial probability guarantee.

## 3. Define the future before inventing features

Let $m_t$ be the midpoint of one fixed CGB contract, and let $\tau=0.01$ be its price tick. The endpoint outcome is

$$
Y_{t,h}=\frac{m_{t+h}-m_t}{\tau}.
$$

A positive outcome benefits long duration through that future. This quantity is in CGB ticks, not yield basis points and not net profit.

We also retain adverse paths in both directions:

$$
A^+_{t,h}=\max_{0\leq u\leq h}\left[-\frac{m_{t+u}-m_t}{\tau}\right]_+,
\qquad
A^-_{t,h}=\max_{0\leq u\leq h}\left[\frac{m_{t+u}-m_t}{\tau}\right]_+.
$$

$A^+$ is adverse excursion for a long; $A^-$ is adverse excursion for a short. They are different targets, not the negative of each other. A lower endpoint after a large rally can be directionally correct and unpleasant to hold.

The implementation uses a regular observation grid. Its excursion labels measure the worst **observed grid midpoint**, so they can miss a more extreme move between grid points. They must not be described as exact tick-level excursions or guaranteed stop requirements.

For a three-class forecast, define a neutral band using information known now:

$$
b_{t,h}=c\,\widehat\sigma_t\sqrt{n_h},
\qquad n_h=h/\Delta,
$$

$$
C_{t,h}=
\begin{cases}
0,&Y_{t,h}<-b_{t,h},\\
1,&|Y_{t,h}|\leq b_{t,h},\\
2,&Y_{t,h}>b_{t,h}.
\end{cases}
$$

$\Delta$ is the grid interval and $\widehat\sigma_t$ is a past-only one-step volatility estimate in ticks. The initial $c=0.35$ is an editable resolution convention. The square-root scaling defines comparable thresholds; it does not assert that actual four-hour returns are independent Gaussian minute returns.

This label asks whether future movement is materially directional relative to the current scale. It does not subtract the spread and call the remainder a market state. Endpoint and path regressions retain continuous outcomes alongside these classes.

A target is absent if its full horizon crosses the explicit session close, a contract change, or missing/invalid observations. We do not turn a late-session four-hour target into a shorter target without changing its name.

## 4. Time is part of the model

Each observation has an event time and a time when the model could first use it. The information set is

$$
\mathcal F_t=\sigma\{z_i:\operatorname{available\_at}_i\leq t\}.
$$

The notebook builds snapshots from the most recent event known at the decision time, using the latest available version of that event. A late revision of an old event cannot replace a newer market observation. Invalid and stale quotes remain invalid; the loader cannot rescue the row by silently falling back to an older attractive value.

The canonical inputs are atomic bid/ask quote records, rate records expressed in basis points, an explicit session schedule, optional trade records and optional scalar SPX/VIX marks. An explicit timezone-aware `AS_OF` cutoff identifies the current decision; the grid never extends into the future session. A vendor adapter is deliberately left to the empty input cells because no feed schema has been supplied. In particular, receipt timestamps must not be fabricated from exchange timestamps.

The session table is the account's permitted research/trading window. It is not an inferred exchange calendar. Prices must identify a contract. Rolling transformations reset when the session or contract changes; missing minutes stay in the grid. A switch between contracts is not a duration return.

This has a practical cost: a 120-minute reference estimate may be unavailable early in the session. The first implementation exposes that warmup instead of manufacturing a prior-session link. A later cross-session reference model would be a separate, explicit design change.

The forecast at $t$ uses completed information at $t$. It concerns movement after $t$. A trade benchmark uses the bid/ask available after its chosen latency. These are separate clocks.

## 5. Transform price into questions about movement

For each completed interval,

$$
r_t=\frac{m_t-m_{t-\Delta}}{\tau}.
$$

For several lookbacks $W$, we ask three different questions:

$$
M_{t,W}=\sum_{j=0}^{W-1}r_{t-j\Delta},
$$

$$
Z_{t,W}=\frac{M_{t,W}}{\widehat\sigma_t\sqrt W},
$$

$$
E_{t,W}=\frac{|M_{t,W}|}{\sum_{j=0}^{W-1}|r_{t-j\Delta}|},
\qquad 0\leq E_{t,W}\leq1.
$$

Raw movement says how many ticks changed. Scaled movement compares it with recent variability. Efficiency distinguishes a relatively direct path from travel that mostly cancels itself. A perfectly flat window has zero efficiency by convention; a missing window is missing, not flat.

These are not three independent witnesses. They are related views of the same path. The reason to keep them is that a five-tick decline through repeated failed rebounds differs from a five-tick decline in one jump followed by silence.

The initial lookbacks are 5, 15, 30 and 60 minutes. These are research resolutions around the intended holding horizon, not discovered optimal constants. Their point is to separate a recent impulse from established movement. Comparing horizons is preferable to assuming that a fast signal remains valid for four hours.

The volatility denominator uses preceding returns, with a declared floor to prevent numerical explosions. It does not use the future outcome window. Floors, lookbacks and phase thresholds are stored in configuration so they cannot disappear into unreviewable notebook state.

A useful objection is that normalization can make a tiny move in a quiet market look enormous. That is why the model retains both tick movement and its scale. Another objection is that price-derived variables may merely restate recent direction. The persistence baseline later asks exactly that question.

## 6. A reference frame that does not remove the trade

The Canadian movement can have an imported component and a local deviation. With comparable, available intervals, estimate a reference coefficient using prior paired returns:

$$
\widehat\beta_{t^-}
=\frac{\widehat{\operatorname{Cov}}_{t^-}(r^{C},u^{US})}
{\widehat{\operatorname{Var}}_{t^-}(u^{US})}.
$$

In this implementation $r^C$ is CGB ticks and $u^{US}$ is a US futures log-price change multiplied by $10^4$. The latter is **log-price basis points, not yield basis points**. Accordingly, beta has units of CGB ticks per US log-price basis point.

The observed decomposition is

$$
r^C_t=\underbrace{\widehat\beta_{t^-}u^{US}_t}_{\text{reference component}}
+\underbrace{\left(r^C_t-\widehat\beta_{t^-}u^{US}_t\right)}_{\text{local residual}}.
$$

Both terms remain features. We are forecasting outright CGB, so a US-led CGB selloff is still relevant. The residual is a diagnostic coordinate, not an instruction to hedge away the common movement.

The identity does not prove that the US market caused the Canadian move. Simultaneous reactions, stale observations and changes in hedge sensitivity are alternatives. Nor can a future US return appear on the right-hand side of a forecast unless that return itself is forecast. The notebook only feeds completed observed components into the predictor.

For the Canadian yield curve, use a lossless change of coordinates:

$$
L=\Delta y_5,\qquad S_{25}=\Delta y_5-\Delta y_2,
\qquad S_{5,10}=\Delta y_{10}-\Delta y_5.
$$

$$
\Delta y_2=L-S_{25},\qquad
\Delta y_5=L,\qquad
\Delta y_{10}=L+S_{5,10}.
$$

$L$ is a five-year anchor, not an assertion that we extracted a pure statistical level factor. This coordinate system lets us distinguish outright movement from rotation without inventing three independent signals out of three algebraically related curves.

For example, 2s5s flattening can occur because two-year yields rise faster than five-year yields, because five-year yields fall faster, or because one rises while the other falls. The same spread change cannot, by itself, establish relief for a CGB short. We preserve the component movements so the model can distinguish these cases.

Swaps and forwards extend that reference environment. A forward derived from the same discount curve is a transformation of existing information, not another independent vote. OIS-versus-government movements also include basis and instrument differences. They are not automatically clean observations of monetary-policy expectations.

## 7. Liquidity and VWAP: observable response, not a story about a firm

An aggregate depth snapshot can answer what was displayed at that moment. It does not reveal every cancellation, execution, hidden order or queue position.

At the best bid and ask, let displayed sizes be $q_b,q_a$. Two optional measurements are

$$
I_t=\frac{q_b-q_a}{q_b+q_a},
\qquad
\mu_t=\frac{a_tq_b+b_tq_a}{q_b+q_a}.
$$

$I_t$ is displayed imbalance. $\mu_t-m_t$ is the displacement of a size-weighted quote reference from the midpoint. These are best-quote measurements, not proof of actual aggressor flow, and not a calibrated probability of the next price move.

The first notebook version uses snapshots honestly. Reconstructing order-flow imbalance from events, cancellation intensity, replenishment or queue survival requires a defined event feed. That adapter and its exchange sequence semantics cannot be filled in reliably from a statement that L2 exists. The design records that boundary instead of coding invented event semantics.

When actual trade records are supplied, VWAP from the displayed fixed-contract anchor is

$$
\operatorname{VWAP}_t=\frac{\sum_{i:\,a_i\leq t}v_ip_i}{\sum_{i:\,a_i\leq t}v_i},
$$

where only received trades from the displayed anchor and contract enter. If the first known contract begins after session open, this anchor is later than the open; the output exposes that distinction rather than calling a partial tape the full session. A corresponding volume-weighted price dispersion is

$$
s^2_{V,t}=\frac{\sum v_i(p_i-\operatorname{VWAP}_t)^2}{\sum v_i}.
$$

This is a dispersion band, not a standard error or a universal probability interval. Its construction must match the chart being discussed before “one standard deviation” means the same thing on both screens.

The notebook can observe distance from VWAP and that dispersion reference. It does not define momentum as touching a line. A failed retest would be a later event label whose confirmation time must be recorded; a model cannot know at the first touch that the retest will fail. Such a pattern can be added as an explicit event detector after its rules are agreed, without becoming the whole definition of momentum.

The informative question is: after a recovery attempt, did price regain ground, did that recovery persist, and was the surrounding duration environment supportive? Identifying who supposedly traded is unnecessary for those measurements. A named-account anecdote can motivate a hypothesis; it cannot supply its probability.

## 8. Describe phase without making it destiny

The notebook uses seven descriptive phases: balanced, upward forming, upward persistent, upward weakening, and the corresponding three downward phases. Invalid or insufficient observations have a separate code.

Direction comes from scaled 30-minute movement. Persistence versus formation uses directional efficiency. Weakening uses the reduction of aligned recent momentum. The implementation makes the precedence and thresholds explicit.

These are a compact description of current observations. They are not seven proven natural kinds. They are also not the three supervised outcome classes: an upward-weakening phase can be followed by an upward, neutral or downward one-hour outcome.

An empirical transition matrix summarizes the description:

$$
\widehat P_{ij}=\frac{N_{ij}+\alpha}{\sum_kN_{ik}+K\alpha},\qquad K=7.
$$

Counts use only eligible successive observations in TRAIN. Additive smoothing prevents a never-seen transition from being declared physically impossible. The matrix is a diagnostic in this implementation; it is not secretly fed into the final forecast as another independent prior.

This is a deliberate departure from the original structural matrices. Its benefit is that we can ask whether apparent state persistence was created by thresholds and overlapping windows. Its cost is that we have not implemented the source framework's complete 22-state theory as a CAD market law. Copying that theory without Canadian identification would hide the most consequential research decision.

## 9. Implement a model of continuing adjustment

The first forecasting expert is a local drift model. It separates a slowly changing directional tendency from immediate price noise:

$$
d_t=\phi d_{t-\Delta}+\eta_t,
\qquad \eta_t\sim\mathcal N(0,Q),
$$

$$
r_t=d_t+\epsilon_t,
\qquad \epsilon_t\sim\mathcal N(0,R).
$$

$d_t$ has units of expected ticks per grid interval. $Q$ describes variation in the latent tendency. $R$ describes observation variation around it. This is a specified reduced model, not a derivation of price from the full exposure-density equation.

The training procedure estimates $\phi,Q,R$ from TRAIN observations by equal-session-weighted Gaussian innovation likelihood. Parameters then remain frozen through calibration and test. The filter can update its current estimate as new returns arrive; that is causal state updating, not refitting against the eventual test result.

For filtered mean $\widehat d_t$ and variance $P_t$, the prediction and update are

$$
\widehat d_{t|t-\Delta}=\phi\widehat d_{t-\Delta},
\qquad P_{t|t-\Delta}=\phi^2P_{t-\Delta}+Q,
$$

$$
v_t=r_t-\widehat d_{t|t-\Delta},\qquad
S_t=P_{t|t-\Delta}+R,\qquad
K_t=P_{t|t-\Delta}/S_t,
$$

$$
\widehat d_t=\widehat d_{t|t-\Delta}+K_tv_t,
\qquad P_t=(1-K_t)P_{t|t-\Delta}.
$$

A large surprise changes the state according to how much uncertainty the model assigned to drift and observation noise. There is no hindsight smoother. A future price cannot revise the state that was available at 10:15.

The fitted likelihood minimizes, up to constants,

$$
\frac12\sum_{t\in\mathrm{TRAIN}}\omega_t\omega_t\left(\log S_t+\frac{v_t^2}{S_t}\right).
$$

The implemented parameter bounds $0\leq\phi\leq0.999$ express a decaying-persistence family. Negative autocorrelated drift and explosive drift lie outside that family. That is an explicit model restriction, not a claim those markets are impossible. ML and the baseline comparison can reveal situations in which the restriction is inadequate.

For $n$ future intervals, define

$$
A_n=\sum_{j=1}^n\phi^j,\qquad B_k=\sum_{j=0}^k\phi^j.
$$

Then the conditional terminal distribution under this model is

$$
Y_{t,h}\mid\mathcal F_t
\sim\mathcal N\left(A_n\widehat d_t,
A_n^2P_t+Q\sum_{k=0}^{n-1}B_k^2+nR\right).
$$

This equation shows exactly what persistence buys us. The current drift contributes repeatedly, but with decay. Uncertainty accumulates from the uncertain starting drift, future drift innovations, and future observation noise.

With $\phi=0$, the current drift has no predictive carry into the next interval. With $\phi$ near one, it matters for much longer. With a small $Q/R$, the filter treats isolated noisy prints cautiously. These mechanisms are inspectable rather than hidden behind the word momentum.

The Gaussian assumption is vulnerable to jumps, fat tails and changing volatility. Simulated paths from this expert are scenarios conditional on those assumptions. They are not evidence that actual CAD tails are Gaussian. The optional simulation cell runs only for a selected current forecast; it does not manufacture a historical performance sample.

## 10. Where machine learning enters

The second expert uses XGBoost to learn how the currently observed configuration relates to the actual future outcome. For each horizon it learns

$$
p^{ML}_{t,h}(k)=\Pr(C_{t,h}=k\mid X_t),\qquad k\in\{0,1,2\}.
$$

The input $X_t$ contains only declared feature modules. The initial runnable baseline uses CGB features. US duration, the Canadian curve, the book, swaps, VWAP and context are explicit additions, each requiring real historical coverage. The data cells and module selection are separate so that four swap sessions cannot masquerade as a month of swap evidence.

The three-class model minimizes weighted cross-entropy plus tree regularization:

$$
\mathcal L=-\sum_i\omega_i\log p^{ML}_{i,h}(C_{i,h})+\Omega(\text{trees}).
$$

Weights give sessions equal total weight. They are not inverse-class weights. Reweighting classes would change the probability target; it is not an innocuous way of making the market more predictable.

Small fixed trees provide a starting capacity. They can learn interactions such as: a downward CGB move with a negative local residual and persistent curve repricing differs from the same CGB move during a supportive US reversal. We do not impose those illustrative signs as truths. The data can fail to support them.

Separate regression heads estimate endpoint movement and the 80th conditional percentile of adverse excursion for each direction. The excursion loss is pinball loss,

$$
\ell_q(y,\widehat y)
=(y-\widehat y)\left(q-\mathbf1_{\{y<\widehat y\}}\right),\qquad q=0.8.
$$

A conditional 80th-percentile estimate is not a risk limit or a guaranteed coverage statement. Its coverage and pinball loss must be checked on untouched outcomes. Sparse tail examples make it especially uncertain with a short history.

This is where ML earns its place: learning nonlinear combinations and horizon-specific associations that a fixed drift equation cannot represent. It does not get to redefine the target after observing the test period. The initial notebook does not conduct a search for whichever feature set and horizon happens to win.

## 11. Combine experts without counting a story twice

The drift expert and ML expert observe related price information. Their outputs are conditional forecasts, not independent measurements. Multiplying them and calling the result Bayes would require assumptions we do not have.

Instead, use a declared logarithmic opinion pool:

$$
z_k=w\log p^{ML}_{t,h}(k)+(1-w)\log p^{D}_{t,h}(k),
$$

$$
p^*_{t,h}(k)=\frac{\exp(z_k/T)}{\sum_j\exp(z_j/T)},
\qquad 0\leq w\leq1,\quad0.5\leq T\leq5.
$$

$w$ controls the combination. $T$ controls sharpness. Both are fitted on a chronologically later calibration block, never on TEST. Numerical probability floors avoid taking a logarithm of zero; they do not prove that an outcome is physically possible with that exact probability.

The convex weights have a useful property: if the two experts give the same probability vector and $T=1$, the pool returns that same vector. Agreement alone does not square the probabilities and invent additional certainty. Calibration may still overfit a short block, so the report preserves both experts separately.

This is our CAD combination, not the repository's Born/Zurek posterior. The source audit at the end describes the latter precisely. Substituting this pool is an explicit research choice: it lets a small amount of calibration data estimate two inspectable quantities while exposing dependence between the experts.

The live directional indicator is

$$
I_{t,h}=p^*_{t,h}(2)-p^*_{t,h}(0),\qquad -1\leq I_{t,h}\leq1.
$$

It is a directional probability contrast. It is not expected ticks, a contract quantity or a trade recommendation. A 60-minute bearish indicator and a 240-minute neutral indicator can coexist. Averaging them into one compelling color would erase useful disagreement.

## 12. Three uncertainties that should not share one label

The output preserves three separate objects:

| Object | What it tells us | What it does not tell us |
|---|---|---|
| Market-outcome probabilities | Down/neutral/up probabilities within the fitted model | Whether the model itself is correct |
| Expert disagreement and forecast entropy | Whether experts disagree and whether the distribution is concentrated | A complete posterior over model uncertainty |
| Observation and history status | Freshness, missing feeds, warmup, session eligibility and training coverage | That a well-observed market must be predictable |

Normalized forecast entropy is

$$
H_t=-\frac{\sum_{k=0}^2p_k\log p_k}{\log3}.
$$

A forecast concentrated on the neutral class is different from a diffuse forecast spread across all three outcomes. Both can have an indicator near zero. A missing feed is different again.

The notebook also reports disagreement between the two expert vectors. This does not replace epistemic uncertainty analysis. Parameter uncertainty, missing mechanisms and distribution changes remain outside a single three-number probability vector.

Fresh data with contradictory signals can be economically informative. Contradiction is not automatically a broken model. Conversely, stale data that look harmonious are not confirmation.

## 13. The evaluation has specific objections to answer

We do not need a pile of disconnected significance tests. We need comparisons that could invalidate the reason for adding each layer.

| Claim being made | Comparison that can defeat it |
|---|---|
| Recent movement contains directional information | Compare against a zero-drift volatility-scaled forecast and simple momentum baseline |
| The drift model improves on raw persistence | Compare its held-out probability loss against the simpler momentum forecast |
| Nonlinear context matters | Compare XGBoost with the simple baseline and with the drift expert on the same eligible times |
| Combining experts is useful | Compare the pool against both components separately on untouched TEST |
| A new module adds information | Freeze its definition, then compare matched-period versions with and without it |
| Forecasted adverse excursion is meaningful | Inspect held-out pinball loss, realized coverage and error by session |
| The indicator is usable for trading | Only after the above, apply a declared position rule and price-based execution assumptions |

TRAIN estimates transforms that require fitting and learns model parameters. CAL fits the pool's weight and temperature. TEST supplies the final untouched comparison. Splits are chronological whole sessions, with explicit embargo and horizon eligibility; forward outcomes do not cross split boundaries.

Targets from neighboring minutes overlap. Thousands of one-minute rows do not become thousands of independent one-to-four-hour experiments. Reports therefore retain per-session losses and sample counts. A minimum number of sessions is an engineering gate, not a theorem of statistical adequacy.

For three-class probabilities, the two primary losses are

$$
\operatorname{LogLoss}=-\frac1N\sum_i\log p_i(C_i),
$$

$$
\operatorname{Brier}=\frac1N\sum_i\sum_{k=0}^2
\left(p_i(k)-\mathbf1_{\{C_i=k\}}\right)^2.
$$

The Brier convention here sums across classes without dividing by three. Smaller values are better for both losses. Accuracy alone ignores how strongly wrong forecasts were expressed.

The first serious result could be that the simple baseline matches the elaborate model. That would mean the extra structure has not earned its complexity on the available data. A second serious result could be that swaps help on four sessions but the evidence is too narrow to generalize. Neither result should be disguised by selecting a flattering chart.

## 14. Execution remains separate, but eventual value depends on it

You are right that bond bid/offer is paid in **price**. Yield can describe a signal or approximate risk; it is not the cash amount exchanged at the quote.

For a CGB benchmark buying $Q_c$ contracts at an entry ask and selling at an exit bid,

$$
\Pi^{long}=Q_c\frac{b_x-a_e}{\tau}V-C,
$$

$$
\Pi^{short}=Q_c\frac{b_e-a_x}{\tau}V-C.
$$

Here $V=10$ CAD per tick, and $C$ contains fees and **additional** adverse slippage. The bid/ask crossing is already inside the quote prices. Subtracting another spread would double count it. The tick mechanics follow the [Montréal Exchange CGB specification](https://www.m-x.ca/en/markets/interest-rate-derivatives/cgb).

For a cash bond with face amount $N$ and clean quoted prices per 100 face, the marked cash-price change uses dirty prices:

$$
P^{dirty}=P^{clean}+AI,
$$

$$
\Pi^{long}_{bond}=\frac N{100}
\left(P^{dirty,bid}_x-P^{dirty,ask}_e\right)
+\text{cash flows}-\text{financing}-\text{fees}.
$$

Settlement, accrued interest, coupons, funding and borrow must be supplied consistently for a full ledger. The notebook includes a simple price-touch accounting helper and names these additional cash-flow inputs explicitly. It does not pretend to be a settlement engine.

The rough risk relation

$$
\Delta\Pi\approx-\operatorname{DV01}\,\Delta y_{bp}
$$

helps compare exposure, but an outright cash bond and CGB are not identical positions. Cheapest-to-deliver, conversion factors, basis and key-rate exposures matter. The current notebook forecasts CGB; a cash-bond implementation needs its own exposure mapping and observed price benchmark.

This preserves the distinction you asked for. A market forecast can be right and still be too small to monetize. Execution does not have to define momentum for costs to matter when deciding whether to trade it.

## 15. What is deliberately not smuggled into the implementation

There is no assertion that four days identify a universal swap-flow law. There is no reconstruction of a firm's inventory from its reported trade. There is no global normalization across future data, no backward-smoothed state, no adjustment that turns a contract roll into momentum, and no same-interval confidence sizing.

The baseline does not fit daily EVT, Hurst or Lyapunov machinery to a few intraday sessions and preserve the original names. Their potential usefulness is a research question, but their estimation scales and assumptions would need their own case. In the source code, some of these named quantities are explicitly proxies. Copying a function name is not transferring its mathematical interpretation.

Likewise, SPX and VIX are contextual observations, not fixed-sign trading rules. A risk-off equity move does not compel a duration rally under every inflation and policy environment. Context modules must earn their contribution on matched data.

The notebook contains a full path from supplied canonical observations to fitted forecasts and diagnostics. It does not contain a vendor connection, live order routing, inferred event-book semantics, or measured alpha. Those are concrete boundaries, not unfinished equations hidden behind impressive vocabulary.

## 16. How to use the notebook

Run the cells in order. With inputs left as `None`, it defines the implementation and reports that it is awaiting data. It does not silently substitute an example dataset.

Populate the input cells with the documented quote, rate, session and optional trade tables. Choose a feature-module set before inspecting its test outcome. Begin with the CGB-only version as a baseline, then explicitly compare the duration-environment version on a common eligible period. The short swap history remains a separate research version until its coverage supports the chosen split.

Inspect the coverage and freshness tables before fitting. The fitted result reports each horizon separately, retains the individual experts, and produces a live view only for eligible current observations. A stale latest observation cannot be replaced with an old successful forecast and called live.

Only after the market forecast is understood should the execution helper be used with a stated entry delay, quantity and actual bid/ask observations. Its function is to connect a forecast to a price-based benchmark, not to prove fills or choose a trade automatically.

## 17. Cognitive checklist

- [ ] I can state the target in ticks and distinguish it from net profit.
- [ ] I know which future outcomes the three classes represent.
- [ ] I know the decision time, availability time, forecast horizon and possible entry time.
- [ ] I can identify which transforms are definitions and which parameters are learned.
- [ ] I can explain why common duration and local residual are both retained.
- [ ] I am not treating related curve/forward quantities as independent votes.
- [ ] I can distinguish displayed depth, actual executed flow and an unobserved position.
- [ ] I know whether VWAP came from actual trades and what its band measures.
- [ ] I understand that a descriptive phase can predict any future outcome class.
- [ ] I can explain what the Kalman state measures and what it does not identify.
- [ ] I know why a one-hour and four-hour forecast can disagree.
- [ ] I can say where XGBoost first uses labels and exactly what those labels are.
- [ ] I know which partition fitted every parameter, including combination weights.
- [ ] I can find the simple baseline that could make the elaborate model unnecessary.
- [ ] I am counting independent sessions and events, not just overlapping rows.
- [ ] I can distinguish neutral outcomes, diffuse probabilities and missing information.
- [ ] I have not mistaken scenario simulation or software checks for market evidence.
- [ ] I can account for the spread once, in price, and recognize cash-bond/CGB risk differences.
- [ ] I know which assumptions would fail during a jump, roll, stale feed or changed regime.
- [ ] I can name the next observation that would weaken the model's interpretation.

The intended result is a forecast whose meaning survives inspection: a defined exposure, a causal description, a specified persistence hypothesis, an ML comparison, and a visibly uncertain forecast of an observable future.

## Source and decision record

**Files inspected :** Fractal X `0 README_MODEL.md`, `0.1 AGENTS.md`, agent contracts, notebooks 1–6, and the core PHYSICS essays 01–06; the detailed code map is in the linked source audit. The original repository remains unchanged. That audit records exact files, zero-based notebook cells and functions.

**Passages used :** exposure/reference construction; distribution and constraint equations; causal timing; stationarity distinctions; metric transforms; current graph tags; multi-horizon XGBoost; structural/Monte Carlo/Born fusion; signal readout and execution timing.

**Extracted logic :** define the environment before the predictor, preserve the reference and its departures, separate observation from future state, and make every probabilistic transformation inspectable.

**Derived decision :** construct a separate CAD model with available-at snapshots, direct future CGB targets, a filtered drift expert, supervised nonlinear forecasts, an explicit dependent-expert combination and a separate execution ledger.

**Uncertainties or contradictions :** source claims and implementations are not interchangeable; source state tags and physical quantities require an observation map; some source metrics are named proxies; source backtest timing needs repair before its performance can establish the CAD case; no supplied Canadian data identifies coefficients or predictive value here.

The [gitos-lenses repository](https://github.com/wizzo-gmb/gitos-lenses) supplies research-ordering and evidence-discipline guidance rather than an implementation of this CAD predictor. The [XGBoost parameter documentation](https://xgboost.readthedocs.io/en/stable/parameter.html) describes the probability and quantile objectives used by the implementation. These links are references for the design, not evidence of trading performance.

## Implementation index

Open the [self-contained notebook](../notebooks/cad-duration-momentum.ipynb) to run the design. Its data cells are blank.

| Code entry point | Role |
|---|---|
| `ResearchConfig`, `FEATURE_MODULES` | Editable conventions and explicitly activated measurements |
| `prepare_panel(..., as_of=AS_OF)` | Available-at observations, explicit session grid and current cutoff |
| `build_features` | Causal price, reference, curve, book, VWAP and context transformations |
| `make_targets` | Future price and sampled-path outcomes, excluded from predictors |
| `split_sessions` | Chronological TRAIN / CAL / TEST contract |
| `fit_local_drift`, `filter_local_drift` | Parameter fitting and subsequent forward-only state updates |
| `fit_research` | Three XGBoost horizon families, combination fitting, baselines and reports |
| `latest_readings`, `predict_frozen` | Current output and reuse of already fitted models |
| `simulate_current_path` | Optional conditional Gaussian scenarios |
| `futures_touch_benchmark`, `cash_bond_touch_benchmark` | Separate price-based accounting |

Activated modules are `cgb`, `us`, `cad_futures`, `curve`, `ois`, `swaps`, `forwards`, `book`, `vwap`, and `context`. The default `('cgb',)` is the initial baseline, not a claim that the surrounding market is irrelevant. Enabling a module changes the research version and requires training coverage. `ois` and `swaps` currently require their complete 1y–5y sets when activated; adjust the declared registry before an experiment if the actual universe is narrower.

The endpoint-mean and adverse-excursion outputs are separate regression heads. They are not advertised as moments of a single joint distribution reconstructed from the pooled three-class forecast. The prototype is a transparent batch replay and research indicator, not a production event-processing service.

## Canonical supporting documents

The source audit and implementation contracts are maintained once rather than repeated as appendices here:

- [Source audit](../../audits/source-audit.md)
- [Measurement and input contract](../../docs/05-feature-contract.md)
- [Earlier predictor contract](06-predictor-contract.md)
