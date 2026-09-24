# Source-to-model audit for an intraday CAD duration research notebook

Audit date: 2026-09-24. Source root: `C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main`. This is a read-only source inspection; the original models were not executed, packages were not installed, and original files were not changed. Notebook cell numbers below are **zero-based JSON cell indices**, including Markdown cells. The accompanying `source_inventory.json` records source SHA-256 hashes, cells, saved outputs, and 400 function/class definitions with within-cell line numbers.

This document distinguishes source behavior, mathematical interpretation, and proposed CAD extensions. Physical terminology in a comment is not evidence that the corresponding physical quantity has been identified in financial data. A deployable pipeline is not, by itself, demonstrated predictive alpha.

## 1. Source architecture and what the CAD notebook should inherit

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

## 2. Notebook 1: reference universe and leader

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

## 3. Notebook 2: measured returns, fitted tails, engineered memory

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

## 4. Notebook 3: beta, residual, level spread, and fragility

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

## 5. Notebook 4 and persistence bridge

`4 matrices.ipynb`, cell 2, contains seven manually specified 22-by-22 transition matrices and validates row-stochastic structure. Cell 3 persists them and regenerates the loader bridge. `matrices.py`, `load_cell04_matrices`, loads matrices in a prescribed order and rejects missing artifacts.

`fractal_db.py` stores raw market observations using a `DATE` field and stores pipeline run metadata, states, posteriors, splits, and lineage. Relevant functions are `persist_cell04` around line 803 and the cell-05 artifact persistence path around line 1126. The lineage pattern is useful; the daily date schema is not a ready-made intraday market-data model. Choosing the latest successful run independently for different stages can combine incompatible versions unless run identifiers are explicitly reconciled.

## 6. Notebook 5: recognition, learning, and fusion

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

## 7. Notebook 6 and saved evidence

`6 signaux.ipynb`, cell 1, is a display/consumption layer. `read_signal_tags` reads forecasts; `read_graph_tags_t` reads current recognition; `current_signal` selects the latest saved signal. `linreg_stats_on_returns` actually fits a price trend and residual z-score. `build_signal_table` combines forecast tags with price-deviation filters. Date-only formatting loses intraday resolution. It does not fit the model afresh.

No working DuckDB/data/model-output directories were present in the audited checkout. Saved notebook outputs do contain historical results; therefore “there are no results” would be inaccurate. For example, notebook 5 cell 158 includes varied test accuracy/Sharpe logs across equities, IEF, and FX, including negative Sharpe examples. These are saved logs, not independently reproduced results or verified CGB evidence. The source timing issue above further prevents treating those logs as clean proof of predictive alpha.

## 8. Transfer contract for a self-contained 1–4-hour CAD notebook

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
