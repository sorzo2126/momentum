# Building the CAD duration momentum model

24 September 2026 · Research design and mathematical companion to **cad-duration-momentum.ipynb**

The object is a live estimate of the direction, magnitude and adverse path of **CGB over the next 60, 120 and 240 minutes**. Canadian yields, US duration, swaps, forwards and liquidity describe the environment of that exposure. Buying or selling a cash bond instead of a future is a subsequent execution and risk-mapping decision.

The notebook contains the implementation, with its market-data inputs deliberately empty. Its equations and transformations are research choices, not estimates from Canadian data. It has no measured trading performance. It is a new CAD application informed by Karim Khemiri's Fractal X; it does not replace or silently rewrite his six notebooks.

The most important decision is this: **describe the state of the market, forecast an observable future, and keep those two objects separate.** Otherwise a model can become extremely good at predicting the persistence of its own labels.

## 1. What I take from Karim, and what the code actually does

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

Karim's Smart Beta essay models capital as a distribution over exposures, not as the path of a single investor. In its notation,

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

This is a deliberate departure from the original structural matrices. Its benefit is that we can ask whether apparent state persistence was created by thresholds and overlapping windows. Its cost is that we have not implemented Karim's complete 22-state theory as a CAD market law. Copying that theory without Canadian identification would hide the most consequential research decision.

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

**Fichiers consultes :** Fractal X `0 README_MODEL.md`, `0.1 AGENTS.md`, agent contracts, notebooks 1–6, and the core PHYSICS essays 01–06; the detailed code map follows in the source-audit appendix. The original repository remains unchanged. The appendix records exact files, zero-based notebook cells and functions.

**Sections ou passages utilises :** exposure/reference construction; distribution and constraint equations; causal timing; stationarity distinctions; metric transforms; current graph tags; multi-horizon XGBoost; structural/Monte Carlo/Born fusion; signal readout and execution timing.

**Logique extraite :** define the environment before the predictor, preserve the reference and its departures, separate observation from future state, and make every probabilistic transformation inspectable.

**Decision deduite :** construct a separate CAD model with available-at snapshots, direct future CGB targets, a filtered drift expert, supervised nonlinear forecasts, an explicit dependent-expert combination and a separate execution ledger.

**Incertitudes ou contradictions :** source claims and implementations are not interchangeable; source state tags and physical quantities require an observation map; some source metrics are named proxies; source backtest timing needs repair before its performance can establish the CAD case; no supplied Canadian data identifies coefficients or predictive value here.

The [gitos-lenses repository](https://github.com/wizzo-gmb/gitos-lenses) supplies research-ordering and evidence-discipline guidance rather than an implementation of this CAD predictor. The [XGBoost parameter documentation](https://xgboost.readthedocs.io/en/stable/parameter.html) describes the probability and quantile objectives used by the implementation. These links are references for the design, not evidence of trading performance.

## Implementation index

Open the [self-contained notebook](C:/Users/mn262/OneDrive/Desktop/momentum/notebooks/cad-duration-momentum.ipynb) to run the design. Its data cells are blank.

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


## Appendix A — Exact Fractal X source audit

### Source-to-model audit for an intraday CAD duration research notebook

Audit date: 2026-09-24. Source root: `C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main`. This is a read-only source inspection; the original models were not executed, packages were not installed, and original files were not changed. Notebook cell numbers below are **zero-based JSON cell indices**, including Markdown cells. The accompanying `source_inventory.json` records source SHA-256 hashes, cells, saved outputs, and 400 function/class definitions with within-cell line numbers.

This document distinguishes source behavior, mathematical interpretation, and proposed CAD extensions. Physical terminology in a comment is not evidence that the corresponding physical quantity has been identified in financial data. A deployable pipeline is not, by itself, demonstrated predictive alpha.

### 1. Source architecture and what the CAD notebook should inherit

The implemented pipeline is:

1. Daily adjusted prices and predefined baskets → inverse-volatility legs and a relative-return leader.
2. Returns → robust rolling moments, fitted tail laws, custom memory/propagation scores, and an engineered GAS/FLUIDE classification.
3. Basket returns → a time-varying reference exposure, residual return, centered level spread, and fragility/cointegration diagnostics.
4. Seven manually specified 22-state transition matrices → validated structural laws.
5. Engineered current-state grammar → future grammar labels → five weighted XGBoost heads → sequential Monte Carlo and structural score fusion → predictions and a separate trading simulation.
6. Saved predictions → a display table with additional current-price filters.

The useful transferable order is **define the exposure and its environment; measure them; construct explicit hypotheses; distinguish current recognition from future prediction; test whether predictions improve the economic target**. The CAD extension should retain outright CGB as the traded exposure. A common-duration factor and a CAD residual are explanatory coordinates; they do not compel a market-neutral spread trade.

### Philosophical passages and their implementation boundary

| Source | Extracted logic | Code connection | CAD decision and limit |
|---|---|---|---|
| `theses/source/PHYSICS/01 beta.md` | Ask which reference exposure is stable under the environment's assumptions. | Notebook 1 baskets; notebook 3 hedge ratio and residual. | Identify outright CGB duration exposure, then distinguish broad duration transmission from local repricing. The source does not supply a CGB-specific beta model. |
| `02 smart beta.md` | Exposure coordinates and crowding can change how a signal behaves. | Fragility, reference spread, regime proxies. | Curve shape, US duration, swaps, and L2 may contextualize CGB pressure. An observed covariance is not identified crowd density. |
| `03 zureck.md` | Effective constraints and stable states can change with the environment. | Hand-engineered state construction and structural law mixture. | Permit observations to contradict the state story. A free-energy decrease is not a theorem that a financial position earns positive PnL. |
| `04 zureck vs laplace.md` | Separate information available at the decision from the subsequent action and outcome; sequential evidence matters. | SPRT-inspired scores and future-state heads. | Use explicit `available_at`, revisions, and future horizon definitions. The financial use of the physical analogy remains a modeling hypothesis. |
| `05 zureck vs laplace part 2.md` | Pointer states, selection by environment, amplitudes, and tail behavior motivate the representation. | Squared positive amplitudes and eleven tags. | The eleven states are engineered in code; they are not derived uniquely from a physical principle. |
| `06 stationary time series.md` | Distinguish return residuals, accumulated levels, reference hedge ratios, and stationarity. | Notebook 3 separate return and level spreads. | Do not conflate residual return, level deviation, stationarity evidence, and the PnL of an executable hedge. |

The physics sources are an interpretable design language. For the new notebook, every financial quantity still needs units, a data construction, a timing rule, and a falsifiable use.

### 2. Notebook 1: reference universe and leader

File: `1 leader univers.ipynb`.

| Cell / function | Input → operation → output | Purpose and caveat |
|---|---|---|
| 16, `REGIME_MAP` | Predefined Q1/Q2 instrument lists → buy/sell baskets. | An imposed environment partition, not an estimated macroeconomic regime from inflation/growth observations. |
| 18, `filter_trading_session`; 28, `fetch_eodhd_daily` | Daily adjusted market data → weekday-filtered price panel. | Weekdays are not an intraday exchange-session calendar. |
| 38, `_inverse_vol_weights_tensor` | Returns → square-root EWMA of squared returns, halflife 63, shifted one row → inverse-volatility weights capped at 0.35 and normalized. | Risk-balancing a basket. The volatility estimate is based on a second moment rather than a demeaned variance. |
| 42, `_rolling_beta_tensor` | Two basket returns → rolling covariance/variance over 63 observations, clipped to [0.05, 3], shifted one row. | A lagged relative exposure estimate with a restrictive positive-beta prior. |
| 52, `build_spread_from_prices` | Log returns and basket weights → $S_t=R_t^+-\beta_tR_t^-$. | This `S` is a **return spread**. It is not the accumulated level spread of notebook 3. |
| 48, `stationarity_gpu` | Return-spread history → simplified Dickey–Fuller-style regression and approximate KPSS diagnostic. | The regression is not a general augmented Dickey–Fuller specification; stationarity of returns is weaker than proving a useful cointegrating price relation. |
| 59, `build_pure_momentum_rotation` | Rolling 126-row sum of spread / rolling spread standard deviation → maximum-score leader. | A relative momentum selector among the prescribed baskets. |
| 62, `backtest_leader_only` | Leader shifted one row × subsequent spread return. | A daily leader-rotation simulation. It does not establish intraday CGB performance. |

### 3. Notebook 2: measured returns, fitted tails, engineered memory

File: `2 metriques.ipynb`. Most windows assume 252 daily rows. Statistical estimation starts here; it is incorrect to say that nothing is fitted until XGBoost.

### 3.1 Returns and moments

Cell 16, `log_returns`, forms $r_t=\log(P_t/P_{t-1})$ and drops missing rows. Dropping rows compresses the observation index: 252 retained observations need not mean 252 exchange sessions or any fixed elapsed time.

Cell 17, `gaussian_roll`, calculates a rolling median and MAD scale, winsorizes each return with its **own** trailing-window threshold, and then computes rolling moments on that historically winsorized series. It is not equivalent to taking one current window and winsorizing all of its observations with the current window's common threshold. The clipping threshold is eight MAD-standardized units. Outputs are mean, sample standard deviation, bias-adjusted skewness, and bias-adjusted excess kurtosis.

These are descriptive features. Their numerical values depend on sampling interval, window length, missing-data treatment, price adjustments, and robustification. They are not instantaneous physical forces.

### 3.2 EVT fitting and hybrid VaR/ES

Cells 21–30 contain `_k_grid`, `_gpd_nll`, `_gpd_fit_mle_scipy`, `_gpd_pwm`, `_ks_gpd_distance`, `_fit_best_gpd_on_sorted`, `_fit_evt_windows`, and `evt_params_from_series`. The left tail is fitted to $-r$ and the right to $r$. Candidate exceedance fractions are approximately 6–20%, with count restrictions; positive exceedances $Y=X-u$ are modeled using a generalized Pareto survival function:

$$
\Pr(Y>y\mid X>u)=\left(1+\xi y/\beta\right)^{-1/\xi},
\qquad \beta>0,\quad 1+\xi y/\beta>0.
$$

Candidate selection combines PWM estimates, MLE refinement, stability, likelihood, and KS-style goodness of fit. It is not simply a universal maximum-likelihood tail estimator.

Cell 31, `evt_quant_es`, maps threshold mass $p_u$ and parameters to an upper-tail magnitude:

$$
q_\alpha=u+\frac{\beta}{\xi}\left[\left(\frac{\alpha}{p_u}\right)^{-\xi}-1\right],
\qquad
\operatorname{ES}_\alpha=q_\alpha+\frac{\beta+\xi(q_\alpha-u)}{1-\xi}.
$$

The $\xi=0$ quantile limit is $u+\beta\log(p_u/\alpha)$; finite ES requires $\xi<1$. The left side is returned with a negative sign. Extrapolation requires the target probability to lie within the fitted tail, not outside its threshold mass.

Cell 56, `hybrid_var_es`, adds empirical quantile/ES fallbacks, shifted and smoothed tail parameters, regime-dependent shape limits, continuity and fit checks, shock exceptions, and monotonicity corrections. These protections make the outputs hybrid estimates, not pure GPD predictions. Cell 57, `ensure_alpha_cols`, sets `alpha_minus` and `alpha_plus` to tail ES quantities and computes

$$
\texttt{alpha\_mu}=\frac{\mu-\alpha(\operatorname{ES}_L+\operatorname{ES}_R)}{1-2\alpha}.
$$

This is a central-body mean identity only when the mean and equal-probability tails form one consistent distributional partition. Mixing winsorized moments, empirical fallbacks, and fitted tails weakens that interpretation. The name `alpha_mu` does not mean investment alpha.

### 3.3 Entropy

Cell 38, `entropy_mixture_series`, uses a return window excluding the current observation and shifted tail parameters. For disjoint left-tail/body/right-tail components, it constructs

$$
h=-\sum_k w_k\log w_k+\sum_k w_k h_k,
\qquad h_{\rm GPD}=\log\beta+1+\xi.
$$

The formula is appropriate to a disjoint-support partition with internally consistent weights. It is not the entropy formula for an arbitrary overlapping mixture. Invalid tail mass is reassigned to the body.

Cell 51, `_gpu_entropy_body_batched`, sorts central observations and uses neighbor/boundary spacings with a digamma correction. Its spacing construction is custom and should be described as a nearest-neighbor-inspired entropy estimator, not automatically certified as a standard textbook estimator. Tied tick returns and a tiny effective body sample are consequential edge cases.

This is **differential entropy**, which depends on return units and can be negative. It should not be compared directly with the discrete maximum entropy $\log 3$. Notebook 5's separate discretized variety feature has a different interpretation.

### 3.4 `rolling_hurst` is a shock-memory proxy

Cell 32, `_expand_qnorm`, rescales a series using expanding 10th/90th percentiles shifted one row, clips to [0, 1], and uses 0.5 on unavailable values.

Cell 33, `rolling_hurst`, does **not** implement a conventional Hurst estimator. It combines normalized tail excess, kurtosis, volatility acceleration, binary-sign entropy defect, curvature, and kinetic activity. Its explicit source score is

$$
U=0.26T+0.22K+0.20A+0.16E+0.16C,
\qquad V=0.54Q+0.24C+0.22T.
$$

It accumulates $U(1-0.42V)$ with decaying memory, mixes the result with source and entropy-defect scores, then maps a bounded energy to $H=0.5+0.5E_H$. The range is [0.5, 1]. It therefore cannot report ordinary anti-persistence $H<0.5$, and it is not estimated from a scaling exponent.

**Timing concern:** a volatility-acceleration intermediate divides by `cp.nanstd(sd)` over the supplied series. Later positive-scale normalization may largely cancel that common factor, but epsilon terms and degeneracy prevent declaring this harmless without a prefix-invariance check. Retain the raw-source issue as a potential future dependence, not a proven large practical effect.

For CAD, either rename this quantity `shock_memory_proxy` and fully disclose its construction, or implement a separately defined conventional estimator with its own assumptions. Do not attach standard Hurst interpretations to this function's name.

### 3.5 `rolling_lyap_kernel` is a propagation proxy

Cell 34, `rolling_lyap_kernel`, builds normalized memory, compression, tail, stress, positive-change fronts, rolling correlations, and lead correlations. Its block combines front movement, target speed, propagation speed, propagation level, memory speed, and memory–receptor interaction, followed by an EWMA and quantile normalization.

It does not estimate exponential separation of nearby trajectories in a reconstructed dynamical system. Describe it as `propagation_instability_proxy`, not a measured Lyapunov exponent. A positive score does not establish deterministic chaos or a prediction horizon.

### 3.6 GAS/FLUIDE and exact timing differences

Cell 35, `classify_gas_fluid_linear_nonlin`, creates two weighted energies. GAS emphasizes body/diffusion/free-flow/calm-tail behavior and weak compression/crowding/memory; FLUIDE emphasizes compression/friction/crowding/tails/collective activity/memory. It reports

$$
p_{\rm gas}=\frac{E_{\rm gas}}{E_{\rm gas}+E_{\rm fluid}},
$$

and chooses the larger-energy regime. This is an engineered score ratio, not a learned regime probability, and it has no inherent long/short direction.

Cell 36, `premice_signals`, combines normalized deviations of short versus long tail/kurtosis summaries and memory/propagation scores. GAS and FLUIDE precursor scores are not exact complements; absolute deviations discard the direction of the deviation.

Cells 59 and 61, `build_M_pit_from_returns` and `build_daily_w252_frame`, require **column-specific** timing:

- Moments and exported returns are shifted one row.
- Exported Hurst proxy is shifted one row.
- Exported Lyapunov proxy is not shifted, so it can use the current completed bar.
- Entropy internally excludes the current return; its GAS input receives another shift.
- Raw versus shifted EVT columns differ; a column-name filter such as cell 58's `pit_only_cols` does not prove causal availability.
- OHLC scaling uses adjusted close divided by the mean of O/H/L, followed by `ffill().bfill()` and clipping. This is not standard corporate-action adjustment; initial backfilling can use later information.

The correct CAD rule is availability at the decision, not a blanket requirement that every feature be shifted exactly one row. Current completed-bar data can be causal if the decision and entry occur afterward.

### 4. Notebook 3: beta, residual, level spread, and fragility

File: `3 beta.ipynb`.

Cells 7–9, `capped_simplex_weights`, `inverse_vol_weights`, and `expanding_hedge_ratio`, estimate inverse-volatility basket weights and expanding covariance/variance ratios using lagged estimates. Cell 13, `compute_smart_spread_pack`, maintains **two distinct quantities**:

$$
R_t^+=\sum_i w_{i,t}^+r_{i,t},\qquad R_t^-=\sum_jw_{j,t}^-r_{j,t},
$$
$$
\alpha_t=R_t^+-\beta_tR_t^-,\qquad
L_t^\pm=\sum_{u\le t}R_u^\pm,\qquad
S_t^{\rm raw}=L_t^+-k_tL_t^-.
$$

Cell 10, `causal_stationary_level_spread`, subtracts a lagged rolling 126-row center from $S^{\rm raw}$. Centering is causal under its input assumptions but **does not prove stationarity or cointegration**. Cells 11, 17, and 18 add lagged standardizations, beta instability, level correlations, and spread deviations.

The level-spread increment is not automatically an executable hedge return:

$$
\Delta S_t^{\rm raw}=R_t^+-k_tR_t^--(k_t-k_{t-1})L_{t-1}^-.
$$

Recentring adds another change term. A portfolio-PnL interpretation needs holdings, rebalance timing, and financing; the code's separate residual-return series avoids that identity error only if users preserve the distinction.

Cell 12, `expanding_fragility_law`, regresses residual return $y_t=\alpha_t$ on its lagged expanding variance $x_t$. Estimates are lagged. The output `sb_alpha_sigma2` is the regression intercept, `sb_fragility_beta` is minus the slope, and `sb_fragility_inertia` divides variance by that negative slope. The last quantity can be negative or unstable near zero. It is not an identified physical relaxation time.

Cells 19–21, `_safe_coint`, `_expanding_coint_stats`, and `_add_ticker_spread_stats`, use Engle–Granger calculations on historical slices, with a minimum 126 rows and periodic recalculation. The special **always recompute the last row** rule means appending data can change which historical timestamps are refit in a full rerun. This is a prefix-consistency concern even if each individual fit only uses its past. Also, cointegrating a cumulative return level with an already centered spread is not automatically the standard two-I(1)-series setting.

Cell 14's ADF/KPSS diagnostic threshold of 0.35 is unconventional; the KPSS implementation's reported p-value range also constrains how that criterion can behave. The diagnostics are not a proof of a stable trading opportunity.

**CAD transfer:** common duration and local residual are useful measured coordinates. A residual need not be forced to be stationary, and the research target remains future outright CGB duration movement. CAD 2/5/10 changes can use the exact basis $L=\Delta y_5$, $s_{25}=\Delta y_5-\Delta y_2$, $s_{510}=\Delta y_{10}-\Delta y_5$; this is a proposed CAD representation, not a source notebook implementation.

### 5. Notebook 4 and persistence bridge

`4 matrices.ipynb`, cell 2, contains seven manually specified 22-by-22 transition matrices and validates row-stochastic structure. Cell 3 persists them and regenerates the loader bridge. `matrices.py`, `load_cell04_matrices`, loads matrices in a prescribed order and rejects missing artifacts.

`fractal_db.py` stores raw market observations using a `DATE` field and stores pipeline run metadata, states, posteriors, splits, and lineage. Relevant functions are `persist_cell04` around line 803 and the cell-05 artifact persistence path around line 1126. The lineage pattern is useful; the daily date schema is not a ready-made intraday market-data model. Choosing the latest successful run independently for different stages can combine incompatible versions unless run identifiers are explicitly reconciled.

### 6. Notebook 5: recognition, learning, and fusion

File: `5 algo fractal x.ipynb`. Important defaults in cell 9 include 252-row memory, horizons 1–5 rows, minimum train/test sizes 400/160, and embargo 7. None of these numbers transfers automatically to a 1–4-hour CGB application.

### 6.1 Current-state construction is engineered recognition

Cell 10 defines eleven tags: R, PTU, SU, U, PEU, EU, PTD, SD, D, PED, ED, duplicated over two environmental blocks for 22 states.

Cell 50, `_regime_motion_context`, residualizes ticker motion against changes in the reference spread, forms multiwindow drift and dispersion, and calculates a Mach-like ratio $|\text{drift}|/(\text{dispersion}+\epsilon)$. It also combines cointegration changes, lagged standardized returns, body-mean changes, compression, memory, and entropy proxies. These are engineered financial coordinates; the Mach analogy does not supply a dimensional physical derivation.

Cell 50, `zureck_tag_p11`, converts positive per-tag amplitudes into $p_j=A_j^2/\sum_k A_k^2$. Cell 53, `_zureck_pointer_filter`, recursively combines emissions, the previous state distribution, and a transition matrix. Positive real amplitudes have no phase interference; mathematically these are weighted score transformations and a recursive state filter.

Cell 47, `zureck_sprt`, uses sequential likelihood-ratio-inspired increments. Its interpretation as a calibrated SPRT requires the assumed null/alternative and dependence model to be appropriate; the code alone does not establish this. Cell 48, `zureck_variety`, discretizes spread behavior into bins; its entropy depends on that binning.

Cells 55–56, `_regime_refine`, `_regime_price_context`, and `build_tags_from_features_strict`, introduce a detailed grammar: prior 20-row breakout boundaries, volatility-scaled buffers, multiple momentum windows, past quantile thresholds, fakeout/rebound conditions, and legal phase sequences. A falling state cannot jump freely to every rising state. This can stabilize interpretation but can also make observed labels reflect the ontology rather than unconstrained market evolution.

Cell 59, `build_transition_graph_tminus1_t`, keeps distinct `graph_tag` (grammar), `graph_observer_tag` (more immediate price evidence), and market-truth diagnostics. It builds node features and adjacent-time edge changes. It is **not a graph neural network**. Cells 103 and 108 add deterministic recognition and 252-row graph memory. The current label is an observation-derived construct, not a forecast and not a trade instruction.

Cell 46, `zfc_block_series`, has a schema hazard: its string fallback uses `pd.factorize(sort=True)`. FLUIDE/GAS map according to the categories present, while other code constructs a block prior in `[p_gas, 1-p_gas]` order. Single-category history can also change the coding. Use an explicit permanent mapping in the CAD notebook; do not assume this fallback is semantically stable.

### 6.2 Feature timing, fitting, targets, and the first supervised ML

Cell 116, `build_dataset`, combines numeric metric/spread features, graph node/edge features, state indicators, and memory. Removing columns containing future/target names cannot prove absence of leakage, and removing direct `p_gas` does not remove the same information encoded in derived states.

Cells 25–29 include expanding past quantiles, shifted z-scores, and a current-inclusive normalizer. A current-inclusive transform can be causal after the current observation is available; it is inappropriate for a decision made before that observation. This must be decided by timestamps, not by the function's name.

Cell 66, `TrainOnlyScaler`, fits mean/std on the outer training set and clips transformed values. Cell 63 supplies chronological splits with cycle-aware boundaries, purge, and embargo. In cell 146, a calibration subset is subsequently taken from the training region. Therefore the scaler has seen the calibration subset's features even though the XGBoost fit uses a narrower fit subset. Affine transforms usually have little effect on trees, but this is not a wholly untouched calibration pipeline. A small-sample fallback can also overlap fit and calibration. Default fractional boundaries move when history grows unless anchor dates are supplied.

Cell 79, `xgb_train_tag`, is the first **supervised machine-learning estimator**. Cell 146, `train_joint7`, trains one `multi:softprob` head per horizon. The key target is the **future engineered `graph_tag`**, shifted by that horizon. Future returns appear separately in audit/evaluation machinery. Predicting a future grammar label accurately does not prove that the label identifies a profitable, persistent CGB move.

Training uses class-balance, transition, horizon, and cybernetic sample weights, plus candidate-selection penalties and calibration-error feedback. In the population limit a weighted cross-entropy classifier estimates a reweighted conditional distribution:

$$
q_w(j\mid x)\propto \mathbb E[w\mid X=x,Y=j]\Pr(Y=j\mid X=x).
$$

Its `predict_proba` output is not automatically a calibrated population probability. It is also **not** a generative likelihood $p(x\mid j)$, despite downstream variables named `L` or `likelihood`. Temperature calibration may improve reliability but does not turn a discriminative posterior into a generative likelihood.

### 6.3 Structural laws and Monte Carlo

Cell 92, `compose_laws`, scores the seven row-wise laws using weighted counts/feature statistics and their log transition values. It applies a softmax-like normalization to those scores and forms a weighted matrix mixture. The weights are fitted structural scores, not automatically a Bayesian posterior over physical laws.

Cell 109, `monte_carlo_leg_propagation`, simulates price paths and maps them through a sequential leg grammar. It uses an EWMA drift/volatility, prior high/low boundaries, at most a limited grammar progression per simulated step, and the current environment block. The first classifier head reweights simulated paths, so the resulting Monte Carlo histogram already carries classifier information.

Two implementation concerns matter for transfer:

- An early volatility fallback uses full-series return standard deviation. This can import future information where that fallback is active.
- The simulator subtracts $\sigma^2/2$ in a GBM log step even though its input mean is estimated from log returns. If that input is interpreted as mean log return, a second Itô correction is inconsistent. The intended drift parameterization must be fixed explicitly rather than copied by name.

The Monte Carlo distribution is conditional on the chosen simulator and grammar; more paths reduce simulation noise, not model misspecification.

### 6.4 Exact active fusion: a tempered product of scores

The active path is cell 145, `born_bayes_posterior_by_horizon`, called from cell 146. It is more complicated than “prior × classifier.” For state $s=(b,j)$, define:

- $q_h(s)$: Monte Carlo tag histogram placed in the current environmental block, with numerical flooring before the amplitude calculation; a grammar projection is the fallback.
- $S_s$: the current-state row of the composed structural matrix, floored positive.
- $F_s$: the frontier weight, floored positive.
- $c_j$: normalized current tag-construction evidence.
- $\ell_h(j)$: weighted XGBoost head output.

Disagreement is measured by the Bhattacharyya overlap and adjusts the diffusion temperature:

$$
B_h=\sum_j\sqrt{c_j\ell_h(j)},\qquad
D_h=\operatorname{clip}\!\left(D_{\rm base}[1+0.5(1-B_h)],1,D_{\max}\right).
$$

With $C_h(s)$ the bounded construction multiplier and $I_{\rm tr}(s)$ a transition-state indicator, the implemented amplitude is

$$
A_h(s)=\big[q_h(s)S_sF_s\big]^{1/(2D_h)}
\,C_h(s)\,\ell_h(j)^{a_h I_{\rm tr}(s)},
\qquad
P_h(s)=\frac{A_h(s)^2}{\sum_u A_h(u)^2}.
$$

Here $C=1$ on persistence states R/U/D; start-state construction multipliers are clipped to [0.5, 2]; finish-state multipliers receive an additional horizon-dependent increase and are clipped to [0.5, 3]. The direct classifier factor acts on transition states, not uniformly on every tag. It is omitted at the first horizon when `mc_carries_signal=True`, because the first head already weighted Monte Carlo paths. Direct-head decay remains at least 0.55 in the ordinary multihead branch.

Consequences:

- Temperature softens the $qSF$ product; it does **not** apply to all factors equally.
- Several factors reuse related inputs, so conditional independence and a coherent joint probability model have not been established.
- The explicit reachability mask is audit-only in this function. It does not force forbidden posterior states to zero. Numerical floors also soften support restrictions. Nevertheless, the engineered labels and Monte Carlo proposal grammar constrain which explanations and paths are readily represented.
- Calling this a **tempered product of expert scores** is a faithful mathematical description. Calling it a derived quantum probability model or ordinary Bayes update is stronger than the implementation establishes.
- Cell 85's older `zureck_born_pnext` is a separate construction that redistributes a tag probability between blocks. Do not substitute that legacy formula for the active multihead path.

Cell 146 later tunes an additional empirical temperature and separately transforms the eleven-tag and 22-state distributions. For temperature unequal to one, independently transforming both need not preserve `tag_probability = sum(state_probabilities over blocks)`. A new implementation should calibrate one coherent distribution and obtain the other by marginalization.

### 6.5 What is genuinely adaptive and what is a diagnostic

Cell 79 changes training weights using calibration errors; cell 115 constructs data-dependent cybernetic weights. Those are actual adaptation mechanisms. By contrast, cell 101's governor `adapt` records diagnostics without changing the strategy on that path, and cell 99's `feedback_degrading` returns false. The philosophical label “cybernetic” spans both active and inert mechanisms; inspect the call path rather than infer behavior from names.

### 6.6 Existing backtest timing is not suitable evidence for the CAD model

Cell 76, `run_trading_backtest`, computes the return from close $i-1$ to close $i$ while sizing with posterior row $i$. Cell 146 passes posteriors without the required shift; those posteriors can incorporate close $i$, current-return temperature, and Monte Carlo starting at close $i$. That creates retrospective sizing of an already realized return. Some pending-entry logic has a delay, but it does not remove this position-sizing issue.

The code also uses generic CFD/FX/crypto cost conventions, not CGB tick-value, contract, depth, and fill conventions. Keep execution and its timing audit separate from the research indicator.

### 7. Notebook 6 and saved evidence

`6 signaux.ipynb`, cell 1, is a display/consumption layer. `read_signal_tags` reads forecasts; `read_graph_tags_t` reads current recognition; `current_signal` selects the latest saved signal. `linreg_stats_on_returns` actually fits a price trend and residual z-score. `build_signal_table` combines forecast tags with price-deviation filters. Date-only formatting loses intraday resolution. It does not fit the model afresh.

No working DuckDB/data/model-output directories were present in the audited checkout. Saved notebook outputs do contain historical results; therefore “there are no results” would be inaccurate. For example, notebook 5 cell 158 includes varied test accuracy/Sharpe logs across equities, IEF, and FX, including negative Sharpe examples. These are saved logs, not independently reproduced results or verified CGB evidence. The source timing issue above further prevents treating those logs as clean proof of predictive alpha.

### 8. Transfer contract for a self-contained 1–4-hour CAD notebook

### Retain, with explicit definitions

1. Exposure/environment separation: outright CGB, common duration, CAD-local residual, and curve shape.
2. A transparent pipeline from observations to measured features to current descriptions to future outcomes.
3. Simple robust moments, explicit return/path summaries, missingness flags, and separate uncertainty.
4. Chronological fit boundaries, a versioned feature contract, and explicit artifact lineage.
5. Current-state diagnostics as interpretable context rather than automatically correct economic labels.

### Replace or defer

1. Replace date-only rows and daily 252/126/63 conventions with elapsed-time/session-aware windows and a minimum-history rule. A month of minute bars is not hundreds of independent daily environments.
2. Define 1/2/4-hour outcomes at actual timestamps. Do not silently truncate a four-hour label at session end or fill missing future observations with unchanged prices.
3. Use `available_at`, revision history, contract identity, and stale-data status. As-of joins must reflect what was known, not merely match exchange timestamps.
4. Keep common-factor exposure and the residual side by side. Do not neutralize away the very duration movement the strategy intends to trade.
5. Learn future CGB movement/path outcomes if that is the economic objective. Predicting the source's next grammar tag is an optional secondary task.
6. Give engineered memory/propagation quantities proxy names. Do not import standard Hurst, Lyapunov, entropy, or quantum claims through naming alone.
7. Defer extreme-tail fitting, high-dimensional states, and elaborate fusion when available history cannot support them. Missing/unestimable is different from neutral/balanced.
8. Separate overlapping mechanism hypotheses—US-led transmission, local repricing, liquidity absorption, and exhaustion need not be mutually exclusive softmax classes.
9. Keep model probabilities distinct from simulator probabilities and execution decisions. Entry latency, bid/ask, depth, costs, and cash PnL belong to an explicitly timed execution module.
10. Leave blank data cells genuinely blank. Definitions and synthetic invariance checks can run without market data; fitted results and performance claims must remain unavailable until real inputs exist.

### Highest-value reference checks

- Prefix invariance: appending future observations must not change historical features that were actually available then.
- Revision/as-of tests: revised yields or late swaps cannot appear in an earlier information set.
- Unit tests in the mathematical sense: basis points versus decimal yields; ticks versus quoted prices; seconds versus rows; log mean versus arithmetic GBM drift.
- Exact curve reconstruction from level and the two slope coordinates.
- Constant prices, zero variance, tied returns, one-category regime history, missing feeds, and interrupted sessions.
- Target separation: a future endpoint/path label never enters features; horizon eligibility is explicit.
- Probability normalization **and** tag/state marginal consistency after any calibration.
- A grammar contradiction can remain visible as evidence rather than being silently relabeled into agreement.

These checks establish that the research object is well defined. They do not establish predictive strength; that requires economically meaningful, chronologically held-out outcomes and comparison with simple persistence/momentum baselines.


## Appendix B — Measurement formulas and input contract

### Measurement and transformation implementation

This component implements `ResearchConfig`, `prepare_panel`, `build_features`, and `FEATURE_MODULES`. Its code is in `features_impl.py` and is intended to be embedded into the notebook. It does not fit an estimator or invent a market tape.

### Provenance

Fichiers consultes : `0.1 AGENTS.md`; `5 algo fractal x.ipynb`, zero-based cells 50, 55, 56; the shared CAD interface contract.

Sections ou passages utilises : `_regime_motion_context`, `_regime_refine`, `_regime_price_context`, `build_tags_from_features_strict`.

Logique extraite : the source constructs several time scales of normalized displacement, preserves a reference-relative velocity, separates direction from persistence/exhaustion, and uses explicit causal state rules. These are useful organizational ideas. Its state grammar is an implemented convention, and its normalized motion scores are engineered quantities.

Decision deduite : retain interpretable measurements, dimensional consistency, explicit time availability and descriptive phases. Replace source daily/basket assumptions with CGB ticks, observed US duration movement, CAD curve coordinates and optional liquidity/context measurements. Keep future CGB outcomes as the learning target. No original repository file is changed.

Incertitudes ou contradictions : the CAD phases are a new seven-phase research convention, not the source's 22-state GAS/FLUID graph. No claim is made that these definitions are unique physical states or proven predictors. Source Hurst, Lyapunov, entropy and EVT proxy machinery is not silently relabeled or copied into this small intraday data set.

### Input and time semantics

All event, availability and session timestamps must carry timezones. The adapter converts them to UTC and rejects naive timestamps and records with event time after availability time. The latter requires repairing the upstream clock definition, not guessing a correction.

`prepare_panel(..., as_of=...)` requires an explicit timezone-aware receiver cutoff. For a historical full sample, supply the last intended session close. For a live sample, supply the actual decision/receiver clock. Sessions whose opens are after that cutoff are excluded, and the current session grid ends at the cutoff rather than adding future invalid rows. The original scheduled `session_close` remains unchanged for full-horizon eligibility. The cutoff is never inferred from the last quote: a feed can be stale while wall-clock time continues. Omitting it raises an actionable error. `neutral_band_sigma` must also be finite and nonnegative.

Quotes are atomic rows with `instrument`, `contract`, `event_time`, `available_at`, `bid`, `ask`; sizes are optional. CGB and US10 prices must already be decimal price points. A Treasury fractional quote requires an explicit upstream conversion. `contract` must identify the actual future or fixed proxy series. Supplied sessions define the research session; no exchange calendar is inferred.

For an instrument at decision time $t$, choose the maximum event time among rows with availability at or before $t$, then its newest available revision. A late correction of an older event does not rewind the current observation. A correction that invalidates the newest event remains invalid. A crossed, missing, stale or otherwise invalid latest quote never causes fallback to an older apparently good quote.

Freshness is receiver decision time minus the selected source event time. This tests quote age, not full feed integrity. The canonical adapter does not claim to recover packet loss, venue sequence gaps, hidden liquidity, trade cancellations or vendor corrections automatically.

The minute grid preserves invalid rows. CGB returns need valid adjacent rows and an unchanged contract. Rolling windows are confined to a session and a consecutive fixed-contract run. Full-window validity prevents missing minutes from being silently skipped. No return bridges a roll, overnight boundary or invalid quote gap. New-session observations require a source event inside that session.

`grid_minutes` must divide the fixed 5, 15, 30 and 60-minute feature windows, volatility/beta windows and forecast horizons. The practical supported default is one minute. Session grids are anchored at their supplied open. If a session close does not land on the grid, the final point precedes close; the model must still demand a full requested horizon.

### CGB movement, scale and path

Let $m_t$ be the valid CGB midpoint and $\tau$ the price tick. A completed grid return, in CGB ticks, is

$$
r_t=\frac{m_t-m_{t-1}}{\tau}.
$$

The past scale excludes the current completed return:

$$
\sigma_t=\max\left(0.25,\operatorname{sd}(r_{t-v},\ldots,r_{t-1})\right).
$$

Here $v$ is the number of grid intervals in the configured volatility window. It requires all $v$ valid observations. The 0.25-tick floor is an explicit numerical research convention, not an estimated market parameter. It does not state that a midpoint must be an integer exchange tick.

For each window containing $n$ intervals,

$$
M_{t,n}=\sum_{j=0}^{n-1}r_{t-j},\qquad
Z_{t,n}=\frac{M_{t,n}}{\sigma_t\sqrt n},\qquad
E_{t,n}=\frac{|M_{t,n}|}{\sum_{j=0}^{n-1}|r_{t-j}|}.
$$

$Z$ is a normalized displacement. It is not a calibrated Gaussian significance statistic; serial correlation and changing volatility invalidate that interpretation. $E$ distinguishes a direct path from offsetting movement. For a fully observed, completely unchanged path, efficiency is zero. Missing paths remain missing.

The core also includes midpoint position in its observed 30-minute range, 15/60-minute realized volatility ratio, 60-minute return skewness, the fraction of squared return movement on the negative side, and current bid/ask spread in ticks. A zero-width observed range has position one half. Zero total squared movement has negative-side fraction one half. Those values mean observed inactivity, not an imputation for unavailable data.

The current core feature block deliberately uses both earlier scale and current completed movement. It is usable only after those observations have arrived. A same-timestamp end-of-interval measurement cannot justify sizing the already completed return.

### Common duration and Canadian deviation

For a US10 decimal price midpoint $u_t$, the observation is a log-price change in basis-point units:

$$
x_t=10^4\log(u_t/u_{t-1}).
$$

These are **log-price basis points, not yield basis points**. No assumed US futures tick size appears.

Using complete paired returns from the preceding beta window,

$$
\widehat\beta_{t^-}
=\frac{\widehat{\operatorname{Cov}}(r,x)_{t^-}}
       {\widehat{\operatorname{Var}}(x)_{t^-}},\qquad
c_t=\widehat\beta_{t^-}x_t,\qquad
e_t=r_t-c_t.
$$

Beta has units of CGB ticks per US log-price basis point; $c_t$ and $e_t$ are both in CGB ticks. The reference has zero intercept as used in this decomposition; covariance/variance estimates a slope, and any average component not explained by that slope remains in the residual. This is an accounting/reference coordinate, not a causal identification result. Its current common component uses current observed US movement, not future US movement. A zero or unresolved US variance leaves beta undefined. Warmup is 120 complete prior paired minute returns by default. Local momentum additionally requires its own past residual volatility window.

Preserve all three quantities. A pure common-duration trend remains a possible outright CGB opportunity. A large residual is not automatically evidence of Canadian informed flow. Asynchronous price updates and a changing reference relation can also produce one.

### CAD curve, OIS and forwards

The optional `rates` table supplies `rate_bp`, already converted to yield/rate basis points by the data adapter. Negative rates are allowed. Source values must identify the actual measurement: executable rates, marks and fitted curve points are not automatically equivalent.

For a window's changes $\Delta y_2,\Delta y_5,\Delta y_{10}$,

$$
L_5=\Delta y_5,\qquad
S_{25}=\Delta y_5-\Delta y_2,\qquad
S_{510}=\Delta y_{10}-\Delta y_5.
$$

These coordinates retain the full three-point curve movement:

$$
\Delta y_2=L_5-S_{25},\quad
\Delta y_5=L_5,\quad
\Delta y_{10}=L_5+S_{510}.
$$

Five- and 30-minute changes are computed only if the entire corresponding grid window contains fresh observations. A rate may be carried while it remains inside its explicit freshness limit. That does not prove it was unchanged between source updates.

`ois` activates OIS1Y through OIS5Y changes; `swaps` activates SWAP1Y through SWAP5Y changes; `forwards` activates FWD1Y1Y and FWD2Y1Y changes. Derived forwards remain dependent on their parent curves. This code does not add up supposed independent confirmations or manufacture forward rates from incomplete discount-curve conventions.

Optional CGZ and CGF futures use atomic quote rows with their actual contract identifiers and decimal prices. The `cad_futures` module exposes their five- and 30-minute log-price changes in basis-point units. These changes retain direction and scale in each observed price series; they do not claim equal DV01, matched maturity or cash-curve equivalence. A risk-normalized comparison requires the actual contract/delivery-risk mapping.

### Book snapshots

With current valid best-level displayed sizes $B_t,A_t$,

$$
I_t=\frac{B_t-A_t}{B_t+A_t},\qquad
\widetilde m_t=\frac{a_t B_t+b_t A_t}{B_t+A_t}.
$$

The features are imbalance, $(\widetilde m_t-m_t)/\tau$, and a complete five-minute average imbalance. Both quantities require nonnegative sizes and strictly positive total displayed size. They measure displayed best-level conditions. The microprice expression is an algebraic size-weighted quote, not a proven expectation of the next traded price. Snapshot imbalance is not event-level order-flow imbalance and cannot identify cancellations, queue priority or replenishment on its own. Full L2 events need a separate declared schema before those features can be implemented honestly.

### Actual-trade VWAP

Optional `trades` rows require unique trade IDs, CGB contract, event/availability timestamps, positive price and size. Duplicate trade IDs are rejected until an upstream event adapter handles corrections and cancellations explicitly. At each decision, only received trades enter the weighted accumulators.

For the supplied observed trades in the displayed fixed-contract anchor interval,

$$
V_t=\frac{\sum_{i\in\mathcal T_t}q_i p_i}{\sum_{i\in\mathcal T_t}q_i},\qquad
s_{V,t}^2=\frac{\sum_{i\in\mathcal T_t}q_i(p_i-V_t)^2}{\sum_{i\in\mathcal T_t}q_i}.
$$

Features are $(m_t-V_t)/\tau$, $s_{V,t}/\tau$ and $(m_t-V_t)/s_{V,t}$. The final feature is undefined for zero dispersion. The band is weighted price dispersion, **not standard error and not a probability band**. No trade tape means no VWAP feature. VWAP is not reconstructed from quote midpoint samples.

`vwap_anchor` is the beginning of the supplied CGB fixed-contract panel run. If the first identifiable quote arrives late, this is an anchored observed-trade VWAP from that later point, not a certified full-session VWAP. `vwap_status` distinguishes `no_trades`, `stale` and `observed_tape`; the last means only that supplied trades exist and their latest timestamp is fresh. Feed completeness still requires an external audit. The default latest-trade age limit is 300 seconds and can be changed explicitly for the actual feed.

This block locates price relative to a volume-weighted reference. A repeated-rejection detector would require a declared approach, crossing, recovery and confirmation event definition; it has not been smuggled into a signed VWAP distance.

### Surrounding context

The preferred optional `context` input uses scalar rows with `instrument=SPX` or `VIX`, `event_time`, `available_at` and `value`, expressed in index points. It uses the same newest-event/newest-version point-in-time logic as other measurements. Quote rows are also supported when the actual input is a quoted proxy, but supplying both forms for the same instrument raises an error. Scalar marks leave bid and ask missing and carry `measurement_kind=scalar_mark`; they never fabricate an executable spread. For shared transformation code the scalar level occupies the corresponding `_mid` column, with the measurement kind retained explicitly. SPX changes are log-price basis points; VIX changes are index points. Their five- and 30-minute windows are separate observations. Neither has a hardcoded bullish or bearish CGB sign. `context_stale_seconds` controls freshness independently of US duration.

### Descriptive seven phases

Let $z=Z_{t,30}$, $E=E_{t,30}$, and $d=\operatorname{sign}(z)$. A phase is unavailable until the complete core feature block is finite. Otherwise the default rules are:

- Balance: $|z|<0.75$.
- Up/down forming: active normalized displacement in that direction.
- Up/down persistent: active displacement and $E\ge0.35$.
- Up/down weakening: active displacement but recent five-minute average movement in its direction is below half the 30-minute average; this takes precedence over the persistence condition.

The weakening comparison is

$$
d\frac{M_{t,5}}{n_5}<\frac12 d\frac{M_{t,30}}{n_{30}}.
$$

These names describe measured current paths. A weakening up phase does not predict a down move. A balance label means this rule's displacement threshold is unmet, not that all market evidence is balanced. There is no causal smoothing, future repainting or imposed sequential phase grammar. One-hot phase columns are missing during warmup. The training component can study transition counts diagnostically; future class targets remain future CGB outcomes.

### Missingness, modules and software checks

Default `feature_modules=('cgb',)` defines the baseline variant. Multimarket research requires explicitly selecting modules and reporting their training coverage. No optional unavailable channel becomes numerical neutrality. Optional activation cannot make four swap days provide evidence for earlier sessions. The selected model's output needs a separate live availability/coverage status.

Focused implementation checks used disposable deterministic fixtures outside the deliverable's data cells: prefix invariance; old late updates; invalid latest revisions; complete optional-module construction; direct trade-weighted VWAP agreement; and common-plus-local reconstruction. These check causal software behavior and formulas only. They establish no market predictability, calibration or trading performance.


## Appendix C — Predictor API and fitting details

### Implemented predictor: mathematical and API notes

`model_impl.py` is a new CAD application. It imports the feature component's `ResearchConfig` and `FEATURE_MODULES` from the same notebook namespace. It does not modify or claim to reproduce the original Fractal X daily model. All model fitting requires actual supplied observations; definitions execute with no market data. The private integration fixture used to check interfaces is not an empirical result and must not appear as a market backtest in the notebook.

### 1. Outcome and horizon

At a decision time $t$, let $m_t$ be the contemporaneously known CGB midpoint, $\tau$ the tick size, and $n=h/\Delta t$ the integer number of grid intervals in the horizon. `make_targets` returns a dictionary keyed by the horizon in minutes.

$$
Y_{t,h}=\frac{m_{t+h}-m_t}{\tau}.
$$

$$
A^+_{t,h}=\max_{0\le j\le n}\left[\frac{m_t-m_{t+j\Delta t}}{\tau}\right]_+,
\qquad
A^-_{t,h}=\max_{0\le j\le n}\left[\frac{m_{t+j\Delta t}-m_t}{\tau}\right]_+.
$$

The endpoint and both path outcomes require every grid midpoint through the endpoint, all within one session and contract segment. Missing quotes or crossing a contract boundary invalidate the outcome; they never become zero returns. The observed grid path cannot reveal adverse excursions between snapshots, so these are sampled-path adverse excursions.

The direction target is actual subsequent CGB price movement, not a future hand-designed state label. Its neutral width is frozen using a trailing volatility available at the decision.

$$
b_{t,h}=c\,\widehat\sigma_t\sqrt n,
\qquad
C_{t,h}=\begin{cases}0&Y_{t,h}<-b_{t,h},\\1&|Y_{t,h}|\le b_{t,h},\\2&Y_{t,h}>b_{t,h}.\end{cases}
$$

The default $c=0.35$ is an editable research convention, not a discovered trading threshold or a transaction-cost hurdle. A cost hurdle belongs in a separate policy evaluation. Other conventions change the question and must be specified before evaluating TEST.

### 2. Chronology and fitting population

`split_sessions` allocates the first sessions to TRAIN, the next three by default to CAL, and the last three to TEST. TRAIN requires at least ten sessions by default. The boundary embargo removes earlier-partition decisions at or after the next partition's first decision minus 240 minutes. For each horizon, `_label_indices` additionally requires the target endpoint to belong to the same retained partition. Entire future paths also remain within their original session by construction.

These counts are engineering gates, not evidence that 16 sessions establish a useful edge. Overlapping intraday horizons are highly dependent. Both pointwise and whole-session losses are retained; no IID confidence interval or misleading effective sample count is manufactured.

Every included session receives equal aggregate fitting and reporting weight. With $N_d$ eligible observations in session $d$, the unnormalized weight is $w_t=1/N_d$. All weights are rescaled to mean one before fitting. No class rebalancing changes the interpretation of class probabilities. This defines a population with equal session importance, rather than one in which the longest or most complete session dominates.

An activated optional feature module must have complete measurements in at least ten training sessions and 100 eligible rows, both overall and within each horizon's eligible training outcomes. Missing optional observations elsewhere remain NaN for trees. Four swap sessions cannot silently qualify a month-long model as a swap-aware model. These are explicit coverage gates, not statistical sufficiency claims.

### 3. The local drift expert

The fitted latent quantity is a statistical drift in ticks per grid interval. It is not identified institutional inventory, physical force, or latent pressure with independently measured units.

$$
r_k=d_k+\epsilon_k,\qquad \epsilon_k\sim N(0,R),
$$

$$
d_k=\phi d_{k-1}+\eta_k,\qquad \eta_k\sim N(0,Q),\qquad 0\le\phi\le0.999.
$$

This is a specific hypothesis: a locally persistent component plus observation noise. The chosen positive, stable persistence excludes sustained explosive dynamics and negative alternating drift. Those excluded behaviors remain objections to inspect through forecast losses and innovations; the model does not claim to represent every possible market law.

`fit_local_drift` estimates $\phi,Q,R$ using training-only Gaussian innovation likelihood and equal-session weights. It uses bounded numerical optimization, records convergence and boundary estimates, and refuses a failed optimization. Innovation errors $e_k$ and variances $S_k$ yield

$$
\mathcal L(\phi,Q,R)=\sum_k w_k\frac12\left[\log(2\pi S_k)+\frac{e_k^2}{S_k}\right].
$$

The filter initializes zero mean and stationary variance $Q/(1-\phi^2)$ on each segment. Missing returns reset to the same prior; they do not carry an unobserved deterministic drift across the gap. There is no backward smoother. All state updates use returns already observed at the decision. Replaying TEST returns through frozen parameters is normal causal filtering; refitting parameters using TEST would be a different and forbidden operation in this held-out report.

The familiar scalar filter updates are

$$
\widehat d^-_k=\phi\widehat d_{k-1},\quad P^-_k=\phi^2P_{k-1}+Q,
\quad K_k=\frac{P^-_k}{P^-_k+R},
$$

$$
\widehat d_k=\widehat d^-_k+K_k(r_k-\widehat d^-_k),\qquad
P_k=(1-K_k)P^-_k.
$$

For the future sum $S_{t,n}=\sum_{j=1}^{n}r_{t+j}$, define

$$
A_n=\sum_{j=1}^{n}\phi^j,
\qquad B_j=\sum_{i=0}^{j-1}\phi^i.
$$

Then `drift_terminal_moments` computes

$$
\mu_{t,n}=A_n\widehat d_t,
\qquad
V_{t,n}=A_n^2P_t+Q\sum_{j=1}^{n}B_j^2+nR.
$$

The first future state is $d_{t+1}$, not the already observed $d_t$. The last formula includes posterior uncertainty, every future state innovation, and future observation noise. It assumes the fitted Gaussian transition remains in force throughout the horizon; event jumps and regime changes can violate that assumption.

`_gaussian_classes` integrates this conditional normal law below $-b$, inside $[-b,b]$, and above $b$. A Gaussian zero-drift baseline uses mean zero and trailing standard deviation $\widehat\sigma_t\sqrt n$. This isolates the claim that directional persistence adds information beyond the scale convention.

`simulate_current_path` optionally simulates conditional paths from the current posterior and frozen parameters. This is a numerical view of this fitted stochastic model, not a second independent source of evidence. Gaussian simulated tails do not establish empirical tail probabilities or market liquidity.

### 4. Where machine learning enters

Only after observable features, time boundaries, and future price outcomes exist does `fit_research` fit XGBoost. Each of 60, 120, and 240 minutes has independent supervised heads:

1. `XGBClassifier`, three future direction classes, objective `multi:softprob`.
2. `XGBRegressor`, conditional mean endpoint movement in ticks, objective `reg:squarederror`.
3. Two `XGBRegressor` heads, 0.8 quantile of sampled-path adverse excursion for long and short directions, objective `reg:quantileerror`.

The fixed settings are 100 trees, depth 2, learning rate 0.03, minimum child weight 10, L2 regularization 10, full rows and columns, histogram trees, and an explicit random seed. There is no search over these settings using TEST. CPU is the default for the new research application; the user can choose the XGBoost device. This is a declared departure from the original repository's maintenance contract, not a modification of its GPU pipeline.

These heads learn nonlinear interactions among known measurements. They do not learn an unspecified metaphysical state or prove the source framework. The three-class target needs all three observed classes in TRAIN; otherwise that horizon is explicitly unavailable. Optional features only enter when named in the configuration and covered by training observations.

The path quantile loss is

$$
\rho_q(u)=u\bigl(q-\mathbf 1_{u<0}\bigr),\qquad u=A-\widehat A_q,\quad q=0.8.
$$

A predicted 0.8 quantile is not a guaranteed stop distance. TEST reports both pinball loss and observed coverage. The mean endpoint head and path quantiles are separate outputs; they are not moments of the pooled class distribution and are not forced to form one fully coherent joint path distribution.

### 5. Combining dependent experts

The dynamics and ML forecasts both use the same market history. They are dependent conditional forecasts. We do not multiply them as if they were independent likelihoods, reinterpret a classifier probability as a generative likelihood, or call a positive probability pool a demonstration of quantum interference.

For class $c$, the implemented pool is

$$
p_c^{\mathrm{pool}}=
\frac{\exp\{[w\log p_c^{\mathrm{ML}}+(1-w)\log p_c^{\mathrm{dyn}}]/T\}}
{\sum_j\exp\{[w\log p_j^{\mathrm{ML}}+(1-w)\log p_j^{\mathrm{dyn}}]/T\}},
\qquad 0\le w\le1,\quad0.5\le T\le5.
$$

`fit_opinion_pool` fits just $w,T$ on CAL log loss, with equal-session weights. That may select one expert completely. The pool can also lose to either expert on TEST. A temperature fit is not permission to label probabilities empirically reliable without examining held-out results. Three CAL sessions are especially weak evidence of stability.

The display score and two distinct uncertainty summaries are

$$
I_t=p_{\mathrm{up}}-p_{\mathrm{down}},\qquad
H_t=-\frac{\sum_c p_c\log p_c}{\log 3},
$$

$$
D_{\mathrm{JS}}=\frac12\operatorname{KL}(p^{\mathrm{ML}}\Vert M)+
\frac12\operatorname{KL}(p^{\mathrm{dyn}}\Vert M),\qquad
M=\frac12(p^{\mathrm{ML}}+p^{\mathrm{dyn}}).
$$

$I_t\approx0$ alone cannot distinguish a concentrated neutral forecast from equal bullish and bearish probabilities. The full distribution remains visible. Entropy is predictive dispersion, disagreement is disagreement between these two models, and neither is a complete epistemic uncertainty estimate. `data_status` is separately reported; missing information does not become a neutral market reading.

### 6. Competing hypotheses and held-out outputs

Every horizon reports TEST log loss, multiclass Brier score, endpoint mean absolute error, eligible rows, and distinct eligible sessions for six named forecasts: zero drift, train class frequency, past direction, fitted dynamics, ML, and the pool. The past-direction baseline estimates three-class frequencies conditional on the sign of `mom_z_30` using TRAIN only. It adds 0.5 pseudo-count per class. Its endpoint mean is the training conditional mean in the same direction bucket. This is a direct competing hypothesis: recent direction may already explain whatever the elaborate model seems to recognize.

The pool's reported endpoint error is the accompanying ML mean head's error, because a three-class probability pool does not specify a within-class return distribution. It is intentionally identical to the ML mean-head metric; only the class probability metrics compare the pool itself.

`metrics[expert]['pointwise_losses']` retains observation timestamps, session IDs, log loss, Brier loss, and endpoint absolute error. `per_session` averages within each session. A coarse confidence/reliability table is also retained, but correlated tiny samples do not justify certification. No Sharpe ratio, fill simulation, transaction cost, leverage, or position sizing appears in the predictor.

`phase_transition_diagnostic` counts adjacent TRAIN pairs in the seven descriptive feature states, requires the same segment, and adds 0.5 smoothing to every destination. It is explicitly descriptive. It neither supplies future price labels nor constrains the forecast to follow a hand-authored transition grammar. State persistence caused by rolling windows and hysteresis must not be mistaken for economic predictability.

### 7. Live use and statuses

`fit_research` returns `status`, `horizons`, `report`, `splits`, training coverage, dynamics parameters, filtered state, and phase transition diagnostics when available. Each ready horizon contains the fitted heads, calibration weights, retained indices, reports, and a full-index predictions table. Training rows are marked in-sample and calibration rows marked as such; those retrospectively evaluated rows are not live evidence.

`latest_readings(research)` returns the actual latest row, even if it is unavailable. It never quietly substitutes yesterday's or an earlier session's eligible forecast. Forecast numerical outputs are blank when the requested horizon extends beyond the explicit session close.

`predict_frozen(research, panel, features, cfg)` replays full prepared history, including newly appended observations, through fixed fitted parameters and returns the latest forecasts without using future labels. It requires the same configuration and original history starting point. It refuses timestamps at or before the calibration cutoff because the fitted model was not yet available then. A production incremental filter can replace full replay once feed and persistence engineering are supplied.

Possible statuses distinguish no data, insufficient history, missing dependencies, failed dynamics fitting, absent target-class coverage, failed calibration, partially available horizons, and ready research forecasts. A “ready” status means the defined fitting procedure completed. It is not an endorsement of a trade, a statistically significant edge, or a completed production feed integration.

### Remaining model objections made explicit

- The source research motivates the organization; the CAD forecasting components and parameters are a new design.
- Local Gaussian drift excludes jumps, negative persistence, and explosive drift; an observed boundary estimate may reveal poor identification.
- A month of futures data and a few swap sessions cannot settle nonlinear generalization, tails, or cross-regime stability.
- A 240-minute forecast can have very few eligible observations after feature warm-up; the code exposes unavailable horizons rather than shortening them.
- Snapshot path adverse excursion misses between-snapshot movements. Spread, fill size, and price impact belong to the separate execution adapter.
- The model requires a supplied session calendar. It does not infer holidays, early closes, exchange breaks, or the account's flat-by policy.
- A held-out TEST becomes development data if its results drive revisions. Subsequent honest evaluation then needs genuinely new data or a separately reserved outer period.
- Prediction is not mechanism identification. Useful forecasts do not establish a causal account of institutional order flow.
