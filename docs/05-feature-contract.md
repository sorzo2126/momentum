# Measurement and transformation implementation

This component implements `ResearchConfig`, `prepare_panel`, `build_features`, and `FEATURE_MODULES`. Its canonical code is in [features.py](../src/momentum/features.py). The current notebook imports that package. It does not fit an estimator or invent a market tape.

## Provenance

Files inspected : `0.1 AGENTS.md`; `5 algo fractal x.ipynb`, zero-based cells 50, 55, 56; the shared CAD interface contract.

Passages used : `_regime_motion_context`, `_regime_refine`, `_regime_price_context`, `build_tags_from_features_strict`.

Extracted logic : the source constructs several time scales of normalized displacement, preserves a reference-relative velocity, separates direction from persistence/exhaustion, and uses explicit causal state rules. These are useful organizational ideas. Its state grammar is an implemented convention, and its normalized motion scores are engineered quantities.

Derived decision : retain interpretable measurements, dimensional consistency, explicit time availability and descriptive phases. Replace source daily/basket assumptions with CGB ticks, observed US duration movement, CAD curve coordinates and optional liquidity/context measurements. Keep future CGB outcomes as the learning target. No original repository file is changed.

Uncertainties or contradictions : the CAD phases are a new seven-phase research convention, not the source's 22-state GAS/FLUID graph. These baseline phases are excluded from the current five-state model described in [the derivation](10-structural-model-derivation.md). No claim is made that either partition uniquely identifies physical states or proven predictors. Source Hurst, Lyapunov, entropy and EVT proxy machinery is not silently relabeled or copied into this small intraday data set.

## Input and time semantics

All event, availability and session timestamps must carry timezones. The adapter converts them to UTC and rejects naive timestamps and records with event time after availability time. The latter requires repairing the upstream clock definition, not guessing a correction.

`prepare_panel(..., as_of=...)` requires an explicit timezone-aware receiver cutoff. For a historical full sample, supply the last intended session close. For a live sample, supply the actual decision/receiver clock. Sessions whose opens are after that cutoff are excluded, and the current session grid ends at the cutoff rather than adding future invalid rows. The original scheduled `session_close` remains unchanged for full-horizon eligibility. The cutoff is never inferred from the last quote: a feed can be stale while wall-clock time continues. Omitting it raises an actionable error. `neutral_band_sigma` must also be finite and nonnegative.

Quotes are atomic rows with `instrument`, `contract`, `event_time`, `available_at`, `bid`, `ask`; sizes are optional. CGB and US10 prices must already be decimal price points. A Treasury fractional quote requires an explicit upstream conversion. `contract` must identify the actual future or fixed proxy series. Supplied sessions define the research session; no exchange calendar is inferred.

For an instrument at decision time $t$, choose the maximum event time among rows with availability at or before $t$, then its newest available revision. A late correction of an older event does not rewind the current observation. A correction that invalidates the newest event remains invalid. A crossed, missing, stale or otherwise invalid latest quote never causes fallback to an older apparently good quote.

Freshness is receiver decision time minus the selected source event time. This tests quote age, not full feed integrity. The canonical adapter does not claim to recover packet loss, venue sequence gaps, hidden liquidity, trade cancellations or vendor corrections automatically.

The minute grid preserves invalid rows. CGB returns need valid adjacent rows and an unchanged contract. Rolling windows are confined to a session and a consecutive fixed-contract run. Full-window validity prevents missing minutes from being silently skipped. No return bridges a roll, overnight boundary or invalid quote gap. New-session observations require a source event inside that session.

`grid_minutes` must divide the fixed 5, 15, 30 and 60-minute feature windows, volatility/beta windows and forecast horizons. The practical supported default is one minute. Session grids are anchored at their supplied open. If a session close does not land on the grid, the final point precedes close; the model must still demand a full requested horizon.

## CGB movement, scale and path

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

## Common duration and Canadian deviation

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

## CAD curve, OIS and forwards

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

## Book snapshots

With current valid best-level displayed sizes $B_t,A_t$,

$$
I_t=\frac{B_t-A_t}{B_t+A_t},\qquad
\widetilde m_t=\frac{a_t B_t+b_t A_t}{B_t+A_t}.
$$

The features are imbalance, $(\widetilde m_t-m_t)/\tau$, and a complete five-minute average imbalance. Both quantities require nonnegative sizes and strictly positive total displayed size. They measure displayed best-level conditions. The microprice expression is an algebraic size-weighted quote, not a proven expectation of the next traded price. Snapshot imbalance is not event-level order-flow imbalance and cannot identify cancellations, queue priority or replenishment on its own. Full L2 events need a separate declared schema before those features can be implemented honestly.

## Actual-trade VWAP

Optional `trades` rows require unique trade IDs, CGB contract, event/availability timestamps, positive price and size. Duplicate trade IDs are rejected until an upstream event adapter handles corrections and cancellations explicitly. At each decision, only received trades enter the weighted accumulators.

For the supplied observed trades in the displayed fixed-contract anchor interval,

$$
V_t=\frac{\sum_{i\in\mathcal T_t}q_i p_i}{\sum_{i\in\mathcal T_t}q_i},\qquad
s_{V,t}^2=\frac{\sum_{i\in\mathcal T_t}q_i(p_i-V_t)^2}{\sum_{i\in\mathcal T_t}q_i}.
$$

Features are $(m_t-V_t)/\tau$, $s_{V,t}/\tau$ and $(m_t-V_t)/s_{V,t}$. The final feature is undefined for zero dispersion. The band is weighted price dispersion, **not standard error and not a probability band**. No trade tape means no VWAP feature. VWAP is not reconstructed from quote midpoint samples.

`vwap_anchor` is the beginning of the supplied CGB fixed-contract panel run. If the first identifiable quote arrives late, this is an anchored observed-trade VWAP from that later point, not a certified full-session VWAP. `vwap_status` distinguishes `no_trades`, `stale` and `observed_tape`; the last means only that supplied trades exist and their latest timestamp is fresh. Feed completeness still requires an external audit. The default latest-trade age limit is 300 seconds and can be changed explicitly for the actual feed.

This block locates price relative to a volume-weighted reference. A repeated-rejection detector would require a declared approach, crossing, recovery and confirmation event definition; it has not been smuggled into a signed VWAP distance.

## Surrounding context

The preferred optional `context` input uses scalar rows with `instrument=SPX` or `VIX`, `event_time`, `available_at` and `value`, expressed in index points. It uses the same newest-event/newest-version point-in-time logic as other measurements. Quote rows are also supported when the actual input is a quoted proxy, but supplying both forms for the same instrument raises an error. Scalar marks leave bid and ask missing and carry `measurement_kind=scalar_mark`; they never fabricate an executable spread. For shared transformation code the scalar level occupies the corresponding `_mid` column, with the measurement kind retained explicitly. SPX changes are log-price basis points; VIX changes are index points. Their five- and 30-minute windows are separate observations. Neither has a hardcoded bullish or bearish CGB sign. `context_stale_seconds` controls freshness independently of US duration.

## Descriptive seven phases

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

## Missingness, modules and software checks

Default `feature_modules=('cgb',)` defines the baseline variant. Multimarket research requires explicitly selecting modules and reporting their training coverage. No optional unavailable channel becomes numerical neutrality. Optional activation cannot make four swap days provide evidence for earlier sessions. The selected model's output needs a separate live availability/coverage status.

Focused implementation checks used disposable deterministic fixtures outside the deliverable's data cells: prefix invariance; old late updates; invalid latest revisions; complete optional-module construction; direct trade-weighted VWAP agreement; and common-plus-local reconstruction. These check causal software behavior and formulas only. They establish no market predictability, calibration or trading performance.
