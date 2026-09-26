# Independent audit of the observability laboratory

This bounded review inspected [run.py](run.py), [protocol.json](protocol.json), the saved verification, and the martingale/twin data. It did not rerun the experiment or alter its protocol, code, results or hashes. Small independent numerical checks were evaluated in memory. This audit adds two interpretation corrections after completion; it does not retroactively amend the predeclared protocol.

The numerical checks are reproducible with [audit_independent.py](audit_independent.py). Running it writes [independent-audit.json](independent-audit.json), including source/input hashes, individual Gaussian-conditioning and horizon-moment comparisons, and ledger reconciliation results. The script verifies the experiment's referenced files are unchanged before and after the checks.

## Conclusion

No logical or numerical defect was found in the inspected linear-Gaussian observation clocks, augmented Kalman calculation, future-return moments, TRAIN/CAL separation or strict-martingale touch accounting. The twin experiment has two interpretation limits that must accompany its results: its observer is misspecified throughout, and its first unequal paired forecast is not a reliable detection time.

## Reviewed invariants and numerical checks

| Object | Independent check | Result |
|---|---|---|
| Return clock | Return received at minute t measures pressure at t−1; the origin return is a placeholder and is excluded from filtering | Correct indexing |
| Proxy clock | The proxy received at t measures pressure at t minus the declared delay, with independent measurement noise | Correct indexing for 0, 5 and 30 minutes |
| Augmented state | State components are current pressure and its required lags; transition shifts each lag, injects process noise only into the current component, and observes the correct entries | Correct |
| Initial covariance | Stationary AR covariance is used for the pressure lag vector; only the available proxy is observed at time zero | Correct for the main Gaussian experiment |
| Kalman posterior | Compared filter means and variances against direct multivariate-Gaussian conditioning on all received observations for eight worlds, delays 0/5/30 and times 0/1/8/20 | Maximum mean error 8.05 × 10⁻¹⁶; maximum variance error 2.78 × 10⁻¹⁷ |
| Horizon moments | Independently expanded the coefficient of current pressure and every future pressure innovation for horizons 1, 2, 60, 120 and 240 | Agreed with `loadings` within 10⁻¹⁰ for the mean coefficient and 10⁻⁹ for variance |
| Oracle information | Oracle accesses current hidden pressure and known parameters; it never accesses future innovations | Correct for the stated oracle |
| Causal poisoning | Saved checks change messages strictly after a cutoff and compare the entire earlier state prefix | All five configurations report zero prefix difference |
| Ridge fit | Scaling and coefficients are fit only on TRAIN worlds; Gaussian residual variance is fitted only on independent CAL worlds | Correct separation |
| Score uncertainty | Forecast origins overlap within a world, but reported intervals use means over independent worlds, with paired world differences for model comparisons | Consistent with the declared design |
| Martingale positions | Independently reconstructed all 61,440 ledger directions using only the current price and prior 30-minute change, or the declared constant side | Exact match |
| Martingale accounting | Recomputed midpoint gross gain and net price-touch gain for every ledger row | Maximum reconstruction errors both 0.0 ticks |
| Saved identity | Recomputed SHA-256 for `run.py` and `protocol.json` against saved verification | Exact matches |

For the future-return calculation, the next h returns begin with current pressure. Its coefficient is the sum of AR powers zero through h−1. A future pressure innovation first arriving after i minutes affects the remaining h−i returns. Return noise contributes h independent variances. The implementation uses exactly this ordering. The filter's additional uncertainty is current-pressure conditional variance multiplied by the squared current-pressure loading.

The quoted analytic information gap is appropriate to this known Gaussian world: it is half the logarithm of the conditional variance ratio, averaged over decision origins. It is an expected proper-score gap, so finite-sample paired score differences need not equal it exactly.

## Required correction: twins are misspecified throughout

The original protocol describes the fixed twin observer as “explicitly misspecified after the change.” That wording is too narrow. The observer is deliberately misspecified before and after the change:

- Twin pressure starts at a fixed −0.25 ticks/minute; the filter starts with a zero-mean stationary prior.
- Twin mean reversion is 0.97; the filter uses 0.98.
- Twin pressure innovation standard deviation is 0.025; the filter uses 0.045.
- Twin pressure reverts toward a nonzero target even before the branch; the filter assumes zero-mean AR dynamics.

Therefore the Kalman observer is exact for the main Gaussian comparison but is a fixed, misspecified causal observer in the twin construction. The twin result demonstrates response to newly arriving evidence under that common observer. It does not estimate the minimum achievable branch-classification error or optimal detection delay.

## Required correction: paired inequality is not reliable detection

Re-reading the saved twin trajectories independently gives these first paired differences:

| Quantity | First differing minute |
|---|---:|
| Hidden pressure | 181 |
| Received return | 182 |
| Received delayed proxy | 186 |
| Forecast mean | 182 |

Both worlds use the same noise draws, so a small deterministic branch effect becomes visible by directly subtracting paired observations. A real observer receives one branch and cannot subtract its unobserved counterfactual. Minute 182 is the first branch-sensitive received input in this paired construction, and the first unequal forecast. It is not evidence that a trader can reliably classify the branch at minute 182.

The original assertion of equal received histories and forecasts through minute 180 holds; in fact those received histories remain equal through minute 181. Hidden pressure separates at 181, affects the next return at 182, and reaches the five-minute-delayed proxy at 186. This is internally consistent.

## Martingale interpretation

The process has independent symmetric tick changes. Each position is bounded and determined before its subsequent 30-minute price change. Hence its expected midpoint gain is zero. A completed active round trip costs 2.4 ticks: one tick for crossing both half-spreads, one additional slippage tick and 0.4 fee ticks. Flat decisions pay zero. The saved gross intervals include zero for all four declared policies; net means are negative, as expected under this design.

The ledger deliberately treats adjacent holding blocks as separate liquidated and re-entered round trips, even when the direction stays unchanged. That is the declared touch benchmark. A policy that continuously retained the same position would pay fewer crossings and would require a separate accounting rule; it would still not acquire positive expected gross gains from this martingale.

No rerun is needed for these editorial interpretation corrections. The completed numerical artifact remains unchanged.
