# Implemented predictor: mathematical and API notes

`model_impl.py` is a new CAD application. It imports the feature component's `ResearchConfig` and `FEATURE_MODULES` from the same notebook namespace. It does not modify or claim to reproduce the original Fractal X daily model. All model fitting requires actual supplied observations; definitions execute with no market data. The private integration fixture used to check interfaces is not an empirical result and must not appear as a market backtest in the notebook.

## 1. Outcome and horizon

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

## 2. Chronology and fitting population

`split_sessions` allocates the first sessions to TRAIN, the next three by default to CAL, and the last three to TEST. TRAIN requires at least ten sessions by default. The boundary embargo removes earlier-partition decisions at or after the next partition's first decision minus 240 minutes. For each horizon, `_label_indices` additionally requires the target endpoint to belong to the same retained partition. Entire future paths also remain within their original session by construction.

These counts are engineering gates, not evidence that 16 sessions establish a useful edge. Overlapping intraday horizons are highly dependent. Both pointwise and whole-session losses are retained; no IID confidence interval or misleading effective sample count is manufactured.

Every included session receives equal aggregate fitting and reporting weight. With $N_d$ eligible observations in session $d$, the unnormalized weight is $w_t=1/N_d$. All weights are rescaled to mean one before fitting. No class rebalancing changes the interpretation of class probabilities. This defines a population with equal session importance, rather than one in which the longest or most complete session dominates.

An activated optional feature module must have complete measurements in at least ten training sessions and 100 eligible rows, both overall and within each horizon's eligible training outcomes. Missing optional observations elsewhere remain NaN for trees. Four swap sessions cannot silently qualify a month-long model as a swap-aware model. These are explicit coverage gates, not statistical sufficiency claims.

## 3. The local drift expert

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

## 4. Where machine learning enters

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

## 5. Combining dependent experts

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

## 6. Competing hypotheses and held-out outputs

Every horizon reports TEST log loss, multiclass Brier score, endpoint mean absolute error, eligible rows, and distinct eligible sessions for six named forecasts: zero drift, train class frequency, past direction, fitted dynamics, ML, and the pool. The past-direction baseline estimates three-class frequencies conditional on the sign of `mom_z_30` using TRAIN only. It adds 0.5 pseudo-count per class. Its endpoint mean is the training conditional mean in the same direction bucket. This is a direct competing hypothesis: recent direction may already explain whatever the elaborate model seems to recognize.

The pool's reported endpoint error is the accompanying ML mean head's error, because a three-class probability pool does not specify a within-class return distribution. It is intentionally identical to the ML mean-head metric; only the class probability metrics compare the pool itself.

`metrics[expert]['pointwise_losses']` retains observation timestamps, session IDs, log loss, Brier loss, and endpoint absolute error. `per_session` averages within each session. A coarse confidence/reliability table is also retained, but correlated tiny samples do not justify certification. No Sharpe ratio, fill simulation, transaction cost, leverage, or position sizing appears in the predictor.

`phase_transition_diagnostic` counts adjacent TRAIN pairs in the seven descriptive feature states, requires the same segment, and adds 0.5 smoothing to every destination. It is explicitly descriptive. It neither supplies future price labels nor constrains the forecast to follow a hand-authored transition grammar. State persistence caused by rolling windows and hysteresis must not be mistaken for economic predictability.

## 7. Live use and statuses

`fit_research` returns `status`, `horizons`, `report`, `splits`, training coverage, dynamics parameters, filtered state, and phase transition diagnostics when available. Each ready horizon contains the fitted heads, calibration weights, retained indices, reports, and a full-index predictions table. Training rows are marked in-sample and calibration rows marked as such; those retrospectively evaluated rows are not live evidence.

`latest_readings(research)` returns the actual latest row, even if it is unavailable. It never quietly substitutes yesterday's or an earlier session's eligible forecast. Forecast numerical outputs are blank when the requested horizon extends beyond the explicit session close.

`predict_frozen(research, panel, features, cfg)` replays full prepared history, including newly appended observations, through fixed fitted parameters and returns the latest forecasts without using future labels. It requires the same configuration and original history starting point. It refuses timestamps at or before the calibration cutoff because the fitted model was not yet available then. A production incremental filter can replace full replay once feed and persistence engineering are supplied.

Possible statuses distinguish no data, insufficient history, missing dependencies, failed dynamics fitting, absent target-class coverage, failed calibration, partially available horizons, and ready research forecasts. A “ready” status means the defined fitting procedure completed. It is not an endorsement of a trade, a statistically significant edge, or a completed production feed integration.

## Remaining model objections made explicit

- The source research motivates the organization; the CAD forecasting components and parameters are a new design.
- Local Gaussian drift excludes jumps, negative persistence, and explosive drift; an observed boundary estimate may reveal poor identification.
- A month of futures data and a few swap sessions cannot settle nonlinear generalization, tails, or cross-regime stability.
- A 240-minute forecast can have very few eligible observations after feature warm-up; the code exposes unavailable horizons rather than shortening them.
- Snapshot path adverse excursion misses between-snapshot movements. Spread, fill size, and price impact belong to the separate execution adapter.
- The model requires a supplied session calendar. It does not infer holidays, early closes, exchange breaks, or the account's flat-by policy.
- A held-out TEST becomes development data if its results drive revisions. Subsequent honest evaluation then needs genuinely new data or a separately reserved outer period.
- Prediction is not mechanism identification. Useful forecasts do not establish a causal account of institutional order flow.
