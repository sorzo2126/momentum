# A CGB momentum decision aid for a trader

The intended product helps a trader decide whether an existing duration adjustment is likely to continue, over which horizon, and through what adverse path. Its first deployment should publish forecasts and record decisions in shadow mode. A trader remains responsible for the position and execution. Automated trading is a separate extension with its own contract.

There are three distinct questions on the screen: what the market has already done; what the model forecasts next; and whether the observations and model supporting that forecast remain usable. A fourth, optional execution view translates the forecast into an instrument, size and cost assumption. Keeping these separate is what makes the display intelligible.

## An actual saved example

![Historical synthetic CGB snapshot](../experiments/structure-lab-v1/trader-view/trader-snapshot.png)

This is the first saved TEST session at 10:30 New York, selected by a fixed clock rule. All forecast numbers come from `base-1729`. The display reads an explicit allowlist of forecast columns; it does not read future returns, realised adverse excursion, future class labels or latent simulator state. The history stops at the decision time. The records were generated from synthetic data and are labelled accordingly.

At this origin, CGB has risen 21.5 ticks over 30 minutes and stands 26.9 ticks above session VWAP. The one-hour forecast nevertheless assigns approximately 50.4% down, 17.7% neutral and 31.9% up. Its mean endpoint change is −3.4 ticks, with a model 10th–90th percentile interval of −20.6 to +13.8 ticks. The 80th percentile adverse excursion is 17.0 ticks for a long and 12.4 ticks for a short.

That is a useful conversation for a trader: recent upward movement and the conditional future view disagree, the mean is small relative to the path uncertainty, and a three-tick current spread is material. It is not a high-conviction sell message. A discretionary trader could use this to question chasing the rally, monitor whether buying remains effective, or compare an existing position with the forecast's horizon. The display itself does not choose that action.

The compact relative label therefore reads **“Observed upward leg | 1h endpoint continuation 32% / opposite 50% / neutral 18%.”** This is a relabelling of the saved up/down/neutral probabilities relative to the observed directional state, with rounding for display. It creates no new score. Endpoint continuation means finishing beyond the neutral band in the current leg's direction. It does not mean uninterrupted trending, survival of the current state, or avoidance of an adverse retracement. For a downward observed leg, down-probability becomes continuation and up-probability becomes opposite. For a balanced or unidentified observed state, the relative label is omitted because there is no established directional leg to continue. The original absolute-direction probabilities remain visible.

This distinction is central to the product: a general directional forecast can favour a reversal or a move out of balance. Calling every directional forecast “momentum continuation” would misstate its purpose. The display allows the trader to distinguish those uses immediately.

The one-hour neutral band at this origin is approximately ±3.05 ticks. “Down” means an endpoint below the lower band, “up” an endpoint above the upper band, and “neutral” an endpoint inside it. It does not mean that the path stayed quiet, that a down move began immediately, or that a short would make money after costs. The two-hour and four-hour bands have different widths. All exact values and target timestamps are in [horizon-forecasts.csv](../experiments/structure-lab-v1/trader-view/horizon-forecasts.csv).

## What should be visible at a glance

| Item | Meaning and intended use |
|---|---|
| Instrument, contract, bid/ask, time and mode | Establish which price and information cutoff the display describes. Replay, shadow and live must be unmistakable. |
| Observed phase and age | A summary of received price behaviour. The current “responsive” state is assigned by price rules; it is not proof of response to an identified trader or order. |
| Separate 1h, 2h and 4h probabilities | Directional endpoint beliefs with the neutral band and expiry shown. A selected horizon should remain prominent; no summing independent horizons into a strength score. |
| Endpoint continuation relative to the observed leg | Existing direction probabilities relabelled as same direction / opposite / neutral. Omit for a balanced or unidentified state. This is not a trend survival or first-passage probability. |
| Mean and 10th–90th percentile endpoint change | Expected movement and dispersion in CGB ticks; absolute price bounds are available on inspection. These are model predictive quantiles, not a confidence interval for an estimated mean. |
| Long and short adverse-excursion quantiles | The size of adverse movement along the path under each directional interpretation. A q80 value can be exceeded; it is neither a worst case nor an automatically suitable stop. |
| Received price, VWAP and dated events | The observation record from which the trader can form a competing explanation. Future outcomes appear only in a clearly separated review mode. |
| Data status | Per-source age, unavailable inputs, active feature coverage, session eligibility and reference validity. Missing information stays distinct from an economically balanced forecast. |
| Model identity | Run ID, contract version, fit cutoff and artifact hashes for replay and audit. A cached old forecast retains its original timestamp. |

Use ticks as the primary short-horizon price unit. The bundle uses 0.01 price points per CGB tick and C$10 per tick per contract. Display dollar exposure only after the trader supplies a position size. DV01 and yield-equivalent movement can be added as a separate risk view using the same current contract, cheapest-to-deliver assumptions and valuation timestamp. The synthetic valuation ledger contains these quantities, but the prototype does not imply that this ledger is an observed live risk feed.

The endpoint forecast begins at the decision midpoint. Executable P&L begins at a specified fill. A cost panel should show the observed spread and separate commissions, delay and slippage assumptions. It must not subtract one convenient constant and relabel a midpoint probability as the probability of a profitable trade.

## Explanation without a made-up story

An explanation should state measurable observations first: “CAD rose while the fitted US component was negative over the last minute”; “selling produced less price displacement than earlier episodes”; or “three recovery attempts failed under the declared event rule.” Then it should name alternative interpretations and the observation that would distinguish them.

The current common/local decomposition is a fitted statistical reference, not verified causal attribution. A local residual may reflect local pressure, a changing relationship or a measurement problem. The current failed-recovery tracker is a specific below-VWAP event rule with a timeout and retracement threshold; zero recorded failures does not establish that no discretionary chart pattern failed. Its definition belongs one click away.

The explanatory text must distinguish channels present in the observation record from channels actually used by the fitted model. In this example, swaps, OIS and forwards are absent and excluded from the fitted feature list. They cannot be cited as confirming the forecast. SPX and VIX exist in the synthetic record but are also outside this fit's selected modules. The extra contextual series should be marked “context only” if displayed.

We should not claim remaining institutional inventory, a continuation half-life, a state-transition cause, or named-account intent until a corresponding estimand and validated observer exist. The proposed inventory experiments are intended to create precisely that next layer of observable reasoning.

## The quant trader's drilldown

The compact screen needs a deeper audit pane, rather than more numbers squeezed into the headline.

| Drilldown | What it should reveal |
|---|---|
| Horizon definition | Decision time, target time, session cutoff, neutral-band rule, midpoint/fill origin and all units. |
| Empirical reliability | Out-of-sample calibration and interval coverage, sample dates, independent session count, uncertainty and relevant regime/freshness subgroup. Nominal q10–q90 is not automatically 80% realised coverage. |
| Scenario support | Weight concentration, effective scenario count, distance to training observations, missing-feature pattern, and unsupported future-state mass. Effective scenarios are weighted paths, not independent market episodes. |
| Component contributions | Endpoint probabilities and path-risk estimates for each expert and the actual fitted mixture weights. At one hour the saved base fits largely select the supervised price-class expert; empirical within-class paths still affect the path forecast. |
| Source lineage | Raw event time, received time, age limits, transforms, model fit cutoff, saved prediction version, and which inputs were excluded. |
| Replay | The exact forecast that was visible then, with outcomes revealed only after maturity. Preserve forecasts made during abstention so the review is not selected on trades alone. |
| Trader annotations | Existing position, thesis, intended horizon, decision, reason for overriding or following, and later outcome. These enable analysis of whether the aid actually improves decisions. |

Predictive entropy, expert disagreement, support distance and data age answer different questions. They should remain separate diagnostics. Do not blend them into an arbitrary “87% confidence” badge. A narrow distribution can be wrong because the model is stale; a broad distribution can be the appropriate forecast with excellent data.

## What the display takes from Fractal X

Files consulted: the source repository's `0 README_MODEL.md`, Cellule 6 contract, and the actual code in `6 signaux.ipynb`. Relevant source logic is `read_signal_tags`, `read_graph_tags_t`, `current_signal`, `build_signal_table`, and the plotting functions.

Fractal X has a useful boundary: its display consumes saved model artifacts and separately identifies the observed graph state at time T and the predicted tag at T+1. Its notebook reads the database in read-only mode, uses file fallbacks and represents unavailable tags. Those are good operational ideas for this decision aid: a view should expose a forecast, preserve its identity and show what was unavailable.

There is also a deliberate adaptation. The original display adds a visual entry flag from predicted tags, universe leg and one-year/ten-year price-extension rules. Those long-horizon rules are not derived for intraday CGB. Our prototype therefore retains the saved probabilities and the trader's observed context without generating a new entry rule in the renderer. An execution policy, if later added, must be versioned and evaluated as its own component.

The original displays realised Sharpe and drawdown alongside the signal. Our compact view instead prioritises the current forecast's horizon and path uncertainty. Historical strategy statistics belong in the drilldown with their dates, costs and sample size; placing a backtest Sharpe next to a current signal can be mistaken for current confidence.

## Output contract for a future live service

One immutable record per decision and horizon should contain: instrument and contract; event cutoff and decision timestamp; generated-at time; fit cutoff; model/run/data version; horizon and target timestamp; endpoint class definitions and probabilities; predictive endpoint quantiles; both directional adverse-excursion quantiles; observed state and its rule/version; support diagnostics; per-source freshness and availability; and explicit forecast status with reasons.

Suggested statuses are `available`, `degraded`, `unavailable`, and `expired`. Their thresholds must be written and validated with the deployment policy. The present prototype reports measured age and missingness; it does not pretend a learned acceptance policy already exists. A service failure should preserve the last record visibly marked stale, rather than presenting an old record as a new forecast.

A separate execution record may add chosen side, size, fill assumptions and controls. A separate outcome record is appended after the target matures. No renderer should recompute the model, alter thresholds, revise past forecasts or silently fill in a missing source.

## Acceptance questions for trader use

- Can the trader explain the selected horizon and what each probability means?
- Can they distinguish an observed upward phase from a forecast of further upward movement?
- Can they see adverse-path risk and two-sided uncertainty before interpreting the mean?
- Can they identify stale or absent sources, including an excluded swaps module?
- Can the same historical forecast be reproduced from its saved artifacts?
- Do blind replay exercises improve the trader's specified decisions compared with the same information without the aid?
- Are improvement and failure measured by horizon, market condition and trader action, including decisions not to trade?
- Does shadow use preserve latency, outages, missing data and overrides instead of reviewing only clean successful examples?

These questions define readiness for an assistive product more precisely than whether the synthetic strategy made money. Real-feed replay and shadow observation remain necessary to establish usefulness on the intended desk. The synthetic research can make the structure and failure behaviour ready to evaluate there.

## Reproduction

Run [build_snapshot.py](../experiments/structure-lab-v1/trader-view/build_snapshot.py) with the project's Python dependencies. It reads the saved study and creates the PNG, SVG, JSON snapshot, forecast table and source-hash verification file in the same display folder. It does not train a model, simulate a market, access live feeds, or change baseline results.
