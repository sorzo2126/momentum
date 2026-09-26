# Fractal X upstream exposure audit

Read-only audit, 26 September 2026. Notebook references below use **zero-based JSON cell indices** and **one-based local source lines**. No notebook was run, no data was fetched, no credentials were read, and no model was trained. Two isolated arithmetic/helper checks used artificial inputs solely to demonstrate implementation issues.

## Files consulted

- Fractal X `0 README_MODEL.md`, `0.1 AGENTS.md`, `0.2 README_THESES.md`, `agents/00-ARCHITECTURE.md`, `agents/header.md`, `agents/sub_a.md`, `agents/sub_a1.md`.
- Notebooks `1 leader univers.ipynb`, `2 metriques.ipynb`, `3 beta.ipynb`; selected consumer functions in `5 algo fractal x.ipynb`.
- Original thesis sources `PHYSICS/01 beta.md`, `02 smart beta.md`, `06 stationary time series.md`.
- Momentum `research/spy_eodhd/run_study.py`.

## Passages used and logic extracted

The Beta essay asks what remains stable under the system's invariances (line 12), constructs an exposure relative to its environment, and explicitly distinguishes convergence from imbalance carry (lines 77–83). Smart Beta selects a small vector of exposures rather than individual names (lines 20–24). Stationary Time Series explicitly rejects stationarity of daily returns as sufficient evidence for level-spread reversion (line 22), then constructs weighted return legs, synthetic cumulative levels, and a level spread (lines 24–58).

The inference for our weak SPY result is therefore to examine the **observed system and constructed object before increasing classifier complexity**. This is a source-grounded interpretation, not a quotation or claim to know the author's private thoughts.

## What the source actually constructs

Notebook 1 has two predefined buy/sell maps, Q1 and Q2: cells 12–16. It does not calculate GDP or inflation acceleration, although cell 16's comments invoke that macro interpretation.

Cell 38 computes lagged inverse-volatility weights with 63-day EWMA half-life and a intended 35% per-name cap. Cell 42 estimates a 63-day return hedge ratio, clips it to [0.05,3], then shifts it by one observation. Cell 52 constructs

$$
R_t^+=\sum_i w_{i,t}^+r_{i,t},\qquad
R_t^-=\sum_j w_{j,t}^-r_{j,t},\qquad
e_t=R_t^+-\beta_tR_t^-.
$$

Weights and beta are based on earlier observations. Cell 59 ranks quadrants by the rolling 126-observation sum of this return residual divided by its rolling standard deviation. This is a relative return-momentum selection rule; the comments call it “momentum de mean-reversion,” but the implementation is not a direct estimate of restoring force or macro acceleration. Cell 62 shifts the selected quadrant before attributing the next residual to the rotation.

Cell 64 lines 22–29 selects the **last** leader and exports its ticker/leg membership. Downstream notebooks process the history of this current selected universe. This is useful as a current-universe analysis; it is not a replay of historically selected constituents at each decision date.

Notebook 3 rebuilds the exposure using different estimators: expanding volatility with one-period lag and cap `min(1,2/n)` (cells 7–8), expanding lagged return and level hedge ratios (cell 9). These are not Notebook 1's 63-day EWMA weights and clipped rolling beta.

Cell 13 distinguishes the return residual from the level residual:

$$
\alpha_t=R_t^+-\beta_tR_t^-,\qquad
L_t^\pm=\sum_{u\le t}R_u^\pm,
$$

$$
S_t^{\rm raw}=L_t^+-k_tL_t^-,\qquad
S_t=S_t^{\rm raw}-\overline S_{t-1}^{\rm raw}.
$$

The center is a lagged 126-day average (cell 10). Cell 18 constructs a second lagged mean/scale normalization of this centered spread. Cell 17 measures hedge drift and instability; cell 21 measures ticker-to-spread covariance, correlation and cointegration statistics. These are potential environmental measurements absent from the SPY adapter.

The difference of a changing-hedge level spread is **not automatically a self-financing portfolio return**:

$$
\Delta S_t^{\rm raw}=R_t^+-k_tR_t^--(k_t-k_{t-1})L_{t-1}^-.
$$

Centering adds another term, $-\Delta\overline S_t^{\rm raw}$. Use this object as a state coordinate, and derive executable returns separately from holdings, prices and costs.

## What the metric layer really is

Notebook 2 cell 5 sets `ROLLING_WIN=252`; all observations are daily. Cell 59 shifts local mean, variance, skewness and kurtosis. Cell 61 assembles tails, hybrid empirical/EVT VaR and ES, entropy, early-transition scores and GAS/FLUIDE context.

`rolling_hurst` is explicitly a **custom bounded shock-memory proxy**, not a conventional Hurst estimator (cell 33 lines 2–7). It combines tails, excess kurtosis, volatility acceleration, sign-entropy deficit, curvature and recent standardized movement into a [0.5,1] score. `rolling_lyap_kernel` is explicitly a **custom propagation proxy**, not a Kantz/Rosenstein Lyapunov estimator (cell 34 lines 2–9). The GAS/FLUIDE classifier combines these with distribution, range and volume scores into normalized hand-specified energies (cell 35). Its `p_gas` is not demonstrated calibrated probability merely because it is normalized.

These measurements are not decoration downstream. Notebook 5 cell 40 joins the beta pack; cell 49 orients spread evidence to each ticker's structural leg; cell 50 combines residual motion, coupling/decoupling and distribution changes; cell 59 names them in graph nodes. Transferring their purpose requires independent observable measurements and validation, rather than renaming ordinary momentum as physics.

## Contrast with the tested SPY adapter

`run_study.py` lines 91–135 resets observations each session. Its main memory is 5–60 minutes of SPY returns, prior-hour volatility, efficiency, close-range position, skew/semivariance, unsigned volume and bar VWAP proxy. Five states derive from a 30-minute standardized move and five-minute weakening rule. Lines 298–309 fit state/price heads and calibrate the empirical path-expert mixture.

There is no contemporaneous basket, slow regime state, cross-asset coupling, spread deformation, long-memory tail state, or original 22-state structural model in that adapter. Weak adapter performance therefore does not evaluate the original complete Fractal X strategy. Conversely, resemblance in terminology cannot establish that its missing layers would improve SPY prediction.

Our dataset has 241 retained trading sessions, with 144 training sessions. Original Notebook 2 requires 252 daily observations even for the initial full rolling window; nested normalization uses further history. A faithful daily study needs multi-year history. Replacing 252 days by 252 five-minute bars materially changes the model. An intraday adaptation could combine a prior-completed-day environmental state with current intraday evidence, but must be named and tested as an adaptation.

## Uncertainties and contradictions: do not copy blindly

1. **Cap violation, verified.** Notebook 1 cell 40 restricts the bisection multiplier to `1/cap`, then normalizes after clipping. With normalized raw scores `[0.99,0.005,0.005]`, cap 0.35, its arithmetic returns `[0.9245283,0.0377358,0.0377358]`. The cap fails. Notebook 3's separate water-filling implementation does not use this same bound.
2. **Missing data turned into no return.** Notebook 1 cell 39 uses `nan_to_num` on asset returns and weights. Cell 59 zero-fills missing quadrant residuals before ranking. This can turn unavailable observations into apparent stability. Notebook 3 cell 13 sums available contributions with `min_count=1`, so missing held names are not explicitly rejected or normalized.
3. **Return stationarity vs level stationarity.** Notebook 1 cell 52 defines `S` as the return residual, and cell 64 passes it to stationarity tests. Its own stationarity comments and thesis warn against using daily-return stationarity to justify a level-reversion trade. Notebook 3 separately builds a level residual.
4. **Stationarity name is not a test.** Notebook 3 uses `STATIONARITY_ALPHA=0.35` (cell 1 line 44), rather than the familiar 5%. More importantly, Notebook 5 `_resolve_stationarity_flags` cell 39 lines 3–10 sets `stationarity_ok` from nonmissing spread and mean plus positive variance/volatility. It does not consume ADF/KPSS acceptance in that path, and defaults an absent flag to one (lines 18–24). This is feature validity, not empirical stationarity evidence.
5. **Prefix inconsistency, verified.** Notebook 3 cell 20 line 21 forces cointegration recalculation at the final sample in addition to the 126-step schedule. The same historical date can therefore have a fresh estimate in a live/prefix run and a stale scheduled estimate when a longer batch is recomputed. An isolated helper check with a deterministic history-length statistic confirms this: index 4 uses four past samples when terminal, but three when the history extends to index 5. No future price enters the regression; the issue is an unstable update schedule.
6. **OHLC adjustment needs correction.** Notebook 2 cell 61 lines 34–39 scales raw open/high/low by adjusted-close divided by the mean of open/high/low, rather than adjusted-close divided by raw close. It also includes backfill. This is not a standard corporate-action adjustment factor and distorts gap/true-range measurements. The log high/low ratio itself cancels a common scale; the gap and true range generally do not.
7. **Names and units need contracts.** Numerous fields named `w252` actually use 126 days (Notebook 3 cells 1,11,17,18). `sb_fragility_inertia` is variance divided by a regression slope against variance (cell 12); interpreting it as an empirically measured relaxation time requires a dimensional/dynamical derivation beyond that code.
8. **Artifacts absent.** This downloaded copy has no `fractal.duckdb`, `data`, `outputs`, `STAGE1_OUT`, `beta` or `STAGE3_OUT`. Notebook output cells exist, but no coherent synchronized artifact bundle was audited here. Source inspection cannot certify the claimed original deployable performance.

## Decisions deduced: bounded next experiments

First preserve the existing SPY study as a completed exploratory result; its inspected TEST period is no longer a fresh selection holdout.

**Environment experiment:** keep SPY as target, unchanged baseline/target/horizon, and add only a small fixed block of lagged basket breadth, dispersion, relative strength and coupling information. The hypothesis is that equal SPY moves have different continuation odds when broadly supported versus concentrated or opposed. Compare incremental out-of-sample information against price-only, not just the old full mixture.

**Exposure experiment:** separately build one predeclared basket with fixed membership. Derive gross/net normalization, lagged weights, hedge updates, tradable return accounting and missing-data policy. Compare fixed equal weights, lagged inverse-volatility weights and a later selector as separate hypotheses. This evaluates exposure engineering without pretending it is SPY outright alpha.

**Timescale experiment:** obtain enough daily history to make slow state estimates meaningful; consume each slow state only after the corresponding day's observations are complete. Compare the same fast model with/without this slow state before adding more complicated graph/posterior mechanisms.

**Mechanism experiment:** specify separate continuation and restoration claims, based on a measurable stable or breaking relationship. A large negative residual can mean accelerating decoupling or an attractive convergence deviation. Its sign alone does not decide the trade. Evaluate response to subsequent disturbances, incremental path-risk information and fixed cost assumptions.

Each experiment needs a predeclared observable, expected conditional effect, failure condition, simple comparator and untouched chronological evaluation. Adding all original layers simultaneously would prevent us from learning which premise was missing.

## Minimal reproduction of the two implementation checks

These fixtures require only NumPy/Pandas and read the local notebook as JSON. They do not execute the notebook, access market data, load credentials or fit models. The first reproduces the scalar arithmetic of Notebook 1 cell 40; the second executes only Notebook 3 cell 20's helper with a transparent deterministic replacement for the expensive cointegration statistic.

```python
import ast
import json
from pathlib import Path
import numpy as np
import pandas as pd

# Notebook 1, zero-based cell 40: capped-simplex arithmetic.
raw = np.array([0.99, 0.005, 0.005])
cap = 0.35
lo, hi = 0.0, 1.0 / cap
for _ in range(80):
    mid = (lo + hi) / 2.0
    total = np.minimum(raw * mid, cap).sum()
    if total < 1.0:
        lo = mid
    else:
        hi = mid
weights = np.minimum(raw * hi, cap)
weights /= weights.sum()
print(weights)
assert weights.max() > cap

# Notebook 3, zero-based cell 20: terminal update schedule.
root = Path("C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main")
notebook = json.loads((root / "3 beta.ipynb").read_text(encoding="utf-8"))
source = "".join(notebook["cells"][20]["source"])
namespace = {
    "pd": pd,
    "np": np,
    "COINT_MIN_OBS": 2,
    "COINT_RECALC_STEP": 3,
    "_safe_coint": lambda y, x: (float(len(y)), float(len(y)) / 100),
}
exec(compile(ast.parse(source), "NB3-cell0-20", "exec"), namespace)
helper = namespace["_expanding_coint_stats"]
y = pd.Series(np.arange(6.0))
x = pd.Series(np.arange(6.0) ** 2)
prefix = helper(y.iloc[:5], x.iloc[:5])
extended = helper(y, x)
print(prefix.loc[4].to_dict(), extended.loc[4].to_dict())
assert prefix.loc[4, "coint_stat"] != extended.loc[4, "coint_stat"]
```

Observed output: weights `[0.9245283018867925, 0.03773584905660378, 0.03773584905660378]`; terminal-prefix statistic/p-value at index 4 `(4.0, 0.04)` versus extended-batch `(3.0, 0.03)`. The deliberately simple statistic isolates scheduling behavior; it is not a claim about real cointegration estimates or forecasting performance.
