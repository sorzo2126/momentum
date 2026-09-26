# What the saved results say

The simulation provides its clearest support for a **60-minute research horizon inside the assumed synthetic ecosystem**. It does not establish a real-market trading edge.

| Base history | 60-minute net, C$ | With higher slippage, C$ | Trades |
|---|---:|---:|---:|
| 1729 | 3,656 | 2,426 | 41 |
| 2718 | 2,140 | 940 | 40 |
| 3141 | 2,206 | 976 | 41 |

Each row is a separate eight-session TEST book with one contract per trade. These are not portfolio returns or capital-normalized performance. Fees, spread crossing and assumed extra slippage are included. Do not sum overlapping horizon books into a capital-free strategy.

The 60-minute probability loss improves on TRAIN class frequencies across all three base seeds. At 120 minutes the probability improvement is less consistent in uncertainty terms, and one model book loses C$876 before the higher slippage stress. A simpler momentum policy earns more at that horizon in two base histories. A richer predictive model is therefore not automatically a better trading rule.

At 240 minutes, one base history loses C$1,494, another places no model trades, and probability improvements are mixed. One nominal 80% endpoint interval has only approximately 61.8% realized coverage. There is no basis here to declare four-hour forecasting solved.

Fast-decay stress makes the 60-minute book lose C$538, or C$1,198 with higher slippage. That is a direct warning that the model's favorable outcomes depend on persistence in the constructed world. Liquidity and decoupling stresses are mixed across horizons and represent one intervention path each.

Feed gaps expose two different missing-data issues. All 200 four-hour forecasts lose observable path outcomes. Separately, an unpriced exit prevents a complete 60-minute execution-book P&L. An unavailable result is not zero and is not safely replaceable by the subtotal of priced trades.

The pressure-removal controls retain other structured curve effects. They are not no-predictability controls. Likewise, bond-math identities, hash checks and historical replay certify implementation properties rather than economic alpha.

The modest conclusion is to take the one-hour mechanism seriously enough to investigate on real chronological data, while retaining the simpler alternatives, testing calibration and monitoring when persistence breaks. Re-tuning until every synthetic scenario profits would destroy the value of these challenges.

Exact results are in [metrics.csv](../metrics.csv), [execution-summary.csv](../execution-summary.csv), [proper-path-scores.csv](../proper-path-scores.csv) and the [full report](../REPORT.md). Every individual forecast and trade is preserved under [results](../results/).
