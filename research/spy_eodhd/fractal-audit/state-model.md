# Fractal X state and structural-posterior source audit

This is a read-only source audit, not a rerun of Fractal X or a performance claim. Notebook cell numbers are one-based and include Markdown cells. Line numbers are local to the named cell. No source notebooks or fitted models were changed.

## Sources, logic, decision, uncertainties

- Files consulted: `0.1 AGENTS.md`, `0 README_MODEL.md`, `agents/sub_a.md`, `agents/sub_a1.md`, `4 matrices.ipynb`, the relevant mathematical and call-site cells of `5 algo fractal x.ipynb`, `research/spy_eodhd/run_study.py`, and `src/momentum/scenarios.py`.
- Passages used: notebook 4 cells 3–4; notebook 5 cells 10–11, 18–19, 32, 47, 51, 54–57, 59–60, 63, 86, 89–93, 104–110, 117, 121–124, 127, 146–147.
- Extracted logic: Fractal first constructs a persistent leg state using market, distribution, and spread evidence, then predicts its next states, simulates phase-constrained paths, and weights those paths with structural and learned evidence. It separately measures agreement with market-return labels.
- Decision: transfer the separation of observation, transition, and economic outcomes; test the usefulness of each layer before porting the full apparatus.
- Uncertainties: no verified Fractal performance artifacts were evaluated by this audit; comments describing numerical improvements are not reproduced results; several comments and the README describe older or broader behavior than the active implementation.

## The most important distinction from the SPY study

The SPY run is not an execution of Fractal X. It reuses our momentum research model's empirical path-distribution machinery and fits it on SPY.

The SPY state definition is particularly simple. In `run_study.py:124–128`, direction is zero when the absolute 30-minute momentum z-score is below 0.75; otherwise it is the sign of that momentum. A directional state is called weakening when its latest five-minute velocity is less than half its average 30-minute velocity. These rules produce balanced, up, up-weakening, down, and down-weakening states. Efficiency is a feature, not part of the state-label rule.

Fractal's 11 tags are range, upward premice, upward start, upward trend, upward pre-end, upward end, and the corresponding five downward tags. Two regime blocks produce 22 states. `5 algo fractal x.ipynb`, cell 11 lines 9–18, establishes their exact order.

This is a change of target as well as a change of model. Fractal's heads predict the future deterministic graph tag. Its separate market audit predicts a single future daily return's tag, not the cumulative return over the next h days. The SPY study predicts cumulative 60-, 120-, and 240-minute price movement relative to a volatility-scaled neutral band. Comparing headline accuracy across these targets would be misleading.

## How Fractal constructs a persistent leg

Cell 51 lines 2–37 constructs a motion context. When a spread is available, it removes the locally estimated response to spread increments:

$$
v_t=r_t-\widehat\beta_t\Delta S_t.
$$

It aggregates rolling drift and dispersion over 10, 20, and 40 daily observations and defines a drift-to-dispersion ratio. Other ingredients include changes in cointegration p-values, mean, volatility, kurtosis, Hurst, Lyapunov, gas probability, entropy, tail asymmetry, beta instability, and spread alpha. Scores are signed sums or averages of normalized components; they are implemented modeling choices, not automatically estimated coefficients.

Cell 57 combines these measurements with price location, breakouts beyond past 20-close bounds, compression, exhaustion, 5/20/40/120-day momentum, and fakeout/rebound logic. Past bounds are shifted. Cell 56 implements the persistent automaton. A phase usually advances or retreats through its adjacent leg states; it does not independently relabel the entire cycle every bar. The code explicitly allows a pre-end to return to trend when continuation is reconfirmed.

Cell 60 lines 64–83 further changes a trend to pre-end at a high frontier state, and freezes the block within a leg; the block is refreshed while the tag is range. The actual graph edges in lines 131–144 connect consecutive dates and carry feature differences. This is a temporal evidence graph, not a graph neural network learning cross-asset connections.

The useful question for SPY is not immediately 'should we use 22 states?' It is: does the current five-state observer confuse an ordinary pullback, a failed continuation, and a completed leg? A richer phase representation is worthwhile only if those distinctions predict different future economic paths out of sample.

## What the seven matrices actually are

Notebook 4 cell 3 contains seven numerical matrix literals. This notebook does not include the procedure that derived or fitted their entries. Cell 4 persists the matrices and writes a database-loading bridge.

Read-only evaluation of the matrix-literal assignment found seven finite, positive 22-by-22 arrays. All 484 entries of each matrix are nonzero. Row sums are within approximately 7e-8 of one. Across the matrices, diagonal probabilities range from 0.97158944 to 0.98669403. Thus these are very strongly persistent structural arrays. Their provenance and their suitability for an intraday time unit need separate justification.

Notebook 5 cells 89–93 make their composition concrete. Training-only transition counts are augmented by frontier-weighted and spread-weighted counts. For source state i and candidate law k:

$$
S_{ik}=\sum_j\left(C_{ij}+\tfrac12 F_{ij}+\tfrac12 B_{ij}\right)\log V_{k,ij},
\qquad
w_{ik}=\frac{\exp(S_{ik}/T)}{\sum_\ell\exp(S_{i\ell}/T)},
\qquad
P_{ij}=\sum_k w_{ik}V_{k,ij}.
$$

The code writes the normalized exponential weights as squared exponential amplitudes, which yields exactly this formula. The matrices are not added as seven ordinary features. The composed law is used in path transition confirmation and posterior weighting.

The strong self-weight can stabilize a persistent teacher label and also resist genuine transitions. Its incremental contribution needs a persistence baseline and a transition-specific score. More structural detail alone does not resolve weak future-return information.

## Gorge/frontier and Monte Carlo: the active calculation

Cells 106–107 construct a per-tag exit propensity. Range uses distribution/spread changes, premice uses contraction measures, starts use confirmation, and trends/pre-ends use position relative to a past mean. For an upward trend, one implemented coordinate is

$$
f_t^{\uparrow}=\tfrac12\left(1-\tanh\frac{P_t-\bar P_{t-1}}{s_{t-1}}\right).
$$

The downward coordinate reverses the sign. This makes departure from an upward trend more likely as price moves below its reference mean. The numerical coordinate is meaningful as a testable hypothesis about phase transition timing.

Cell 110 generates 256 price paths per observation, with a fixed seed. Each simulated path follows the phase automaton. The path's current phase may transition when a uniform draw is below its per-tag frontier propensity, and price or current-state evidence satisfies the transition rule. Premice-to-start confirmation is additionally sampled using a ratio from the composed structural law. The current spread and distribution 'bricks' remain fixed over the simulated horizon; only the simulated price and phase evolve.

The path-weighting rule is especially important. The h=1 head weights each path according to the path's first future tag. Those weights are carried to later simulated phases:

$$
\omega_m\propto L_1(z_{m,1}\mid X_t),
\qquad
q_{t,h}(k)=\sum_m\omega_m\mathbf 1\{z_{m,h}=k\}.
$$

This means Monte Carlo is conditional model propagation, not independent confirming evidence. If simulated paths never visit an alternative at h=1, likelihood reweighting cannot create those missing paths. The phase topology itself limits reachability.

No paths here imply that all future distribution and spread features have been simulated jointly. A direct transfer to a stock basket would need to specify whether the spread, volatility, and frontier are frozen or dynamically propagated and why.

## The official posterior as implemented

Notebook 5 cell 146, called from cell 147 lines 266–278, is the active posterior. Ignoring numerical floors, a useful algebraic representation before the separate calibration temperature is:

$$
\widetilde p_{t,h}(s)
=\left[q_{t,h}(s)P_{z_t,s}F_t(s)\right]^{1/D_{t,h}}
c_{t,h}(s)^2\ell_{t,h}(s)^2,
\qquad
p_{t,h}(s)=\frac{\widetilde p_{t,h}(s)}{\sum_u\widetilde p_{t,h}(u)}.
$$

Here q is the simulated tag histogram placed in the current block; P is the composed structural-law row; F is a frontier tilt; c is a bounded construction multiplier applied only to transition phases; and the direct likelihood multiplier ell applies only to transition phases. At h=1, ell is one because the Monte Carlo paths already carry the first head's likelihood. At later horizons ell is a power of the corresponding direct head.

The disagreement temperature is

$$
D_{t,h}=\operatorname{clip}\left[D_t\left(1+\tfrac12\left(1-\sum_k\sqrt{a_t(k)L_h(k)}\right)\right),1,6\right],
\qquad
D_t=1+\log\left(1+\frac{|r_t|}{b_t}\right).
$$

The construction vector a is the normalized geometric mean of the current OHLC evidence and the distribution/spread evidence. Disagreement broadens the posterior; it is not directional information by itself. The same observations feed several factors, so calibration and component ablations are necessary to assess whether the combination improves useful predictions.

Cell 147 lines 279–306 then chooses a flattening temperature on an internal TRAIN calibration segment. It does not sharpen below temperature one. This can repair overconfidence but cannot change the argmax ordering of an individual probability vector or invent directional discrimination.

Important active-versus-dormant distinctions:

- `env_amp22` is passed as `None` in the official call. GAS/FLUIDE still influences tags, bricks, and execution elsewhere; it is not a global posterior amplitude here.
- The allowed topology mask is a diagnostic, not a final hard probability mask.
- The supplied memory/reliability prior and explicit anticipation calculation are overwritten by the Monte Carlo histogram on the normal branch. They matter to fallback behavior; graph memory still affects the Monte Carlo fork direction and head features.
- The older `zureck_born_pnext` in cell 86 is retained for legacy audit, not the official output.
- Several comments still describe matrix powers, a single head, or different likelihood decay even though the active path differs.

## Concrete source concerns before using Fractal as the reference implementation

1. **Export meaning:** cell 147 lines 1056–1069 exports current graph-leg labels as `tag_post_t1`. It explicitly replaces posterior argmax to avoid flicker. This contradicts the README definition of that field as the posterior's t+1 prediction. A continuation policy can legitimately act on an observed state, but the field must not be interpreted as a distinct future forecast.
2. **Monte Carlo warm-up:** cell 110 line 21 fills unavailable historical volatility with `r.std()` over the full supplied history. That fallback is future-sensitive for early observations. This is not evidence that every late test row is affected; its actual impact needs an isolated prefix test.
3. **Drift convention:** cell 110 line 20 estimates mean log return, then line 34 subtracts half the variance again in the simulated log increment. If mu denotes mean log return, the subtraction changes the intended mean; if it denotes price drift, the estimator is inconsistent with that name. Choose one convention explicitly.
4. **Replay randomness:** the random generator draws arrays of shape `(number_of_dates, number_of_paths)` at each horizon. Extending the history changes later-horizon shocks allocated to earlier dates. Use per-origin deterministic streams when testing online/batch equivalence; the issue is reproducible coupling, not clairvoyance from random numbers.
5. **Block identity:** cell 47 uses sorted factorization of string regime values over the supplied history. The appearance of a previously unseen category can change earlier integer labels. Use an explicit fixed regime map.
6. **Teacher versus economic target:** the heads and temperature calibration learn future persistent graph tags. The separate market-reference label uses individual future daily returns. State classification, future return prediction, and executable profit are different measurements and must remain separate.

## Why the current SPY structural expert may add little

`scenarios.py:43–47` estimates a five-state transition distribution from training counts with shrinkage. A future-state classifier is blended with this transition prior. `scenarios.py:83–103` redistributes local empirical path weights so their future-state marginals match that state forecast; a separate expert redistributes the same paths to match directly predicted endpoint classes. Calibration learns a convex mixture of those experts.

There is a semantic mismatch worth investigating: SPY's future state at t+h describes momentum over the last 30 minutes before t+h, while its return label covers the entire h-minute interval. A four-hour path can finish in a downward state after a large earlier rally and still have a positive four-hour return. Predicting that terminal state better need not predict cumulative return better.

There is also an information-compression question. The five-state identity is a deterministic transform of recent price inputs already available to the direct head. It may help organize history without adding much predictive information. A zero fitted structural-mixture weight is evidence about this particular state-based redistribution on this calibration period, not a proof that all structure is useless.

## Bounded experiments derived from this audit

1. Preserve the present SPY study and its consumed test interval as a fixed reference. Use chronological development folds for changes, followed by a new untouched period.
2. Compare the current five-state observer with a small phase observer separating initiation, continuation, and failed continuation. Keep price outcomes and economic metrics identical; do not award a win merely for accurately predicting a sticky teacher label.
3. Test soft construction measurements and phase age directly in the price head before introducing an additional state head. Ask whether continuous evidence carries information lost by hard thresholds.
4. Compare state-conditional paths, direct-return paths, and path-event targets on the same folds. For a momentum use case, a continuation-before-reversal event or a first-passage target may align more closely with the intended phenomenon than the terminal 30-minute state.
5. Quantify neighborhood effective sample size and sensitivity to feature-group weighting. `neighbor_count` currently determines a kernel bandwidth rather than selecting only that number of paths. Test a bounded bandwidth family and measure calibration, tail coverage, and turnover; do not assume sharper distributions are better.
6. If structural simulation is retained, isolate price simulation, phase rules, law weighting, and likelihood weighting. Run seed stability, zero-drift/null-price, reversed-direction, and frozen-versus-propagated-context checks. More simulation paths reduce Monte Carlo noise, not model misspecification.
7. Add basket context only with synchronized observed data and lagged exposure weights. Test whether market/common-factor movement and stock-specific movement improve the fixed SPY outcome; do not combine this result with a separate basket-trading strategy's performance.
8. Evaluate the indicator's forecast distribution and a separately frozen trading rule. Any profitability statement needs an explicit fill clock, direction, holding/exit policy, spread/slippage assumptions, and net results. The present classification study alone does not establish trading edge.

The strongest transferable idea is to identify what mechanism can change the next path and give that mechanism a measured representation. The full 22-state machinery should earn its place through incremental predictive and economic evidence.
