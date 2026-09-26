# Hypotheses, mechanisms and possible refutations

This document makes the reasoning behind the saved experiment explicit. It was assembled when packaging the completed results; it is **not a timestamped preregistration**. The implemented protocol is recorded in [protocol.json](../protocol.json) and [resolved-config.json](../resolved-config.json). No model or threshold was selected by searching these TEST results.

The target is outright Canadian duration movement through CGB over the next 60, 120 or 240 minutes. Other instruments describe the environment. They do not turn the target into a CAD–US relative-value trade. Favorable direction, the path taken and executable accounting are separate questions.

## H1: continued adjustment can create conditional continuation

The proposed mechanism is persistent common and domestic rate pressure, transmitted through related markets and temporary liquidity effects. The simulator deliberately includes persistent latent drivers and event shocks. The observable model receives quotes, yields and trade measurements; it does not receive those latent drivers.

If the observed state contains usable information about unfinished adjustment, forecast distributions should improve on TRAIN unconditional frequencies in later sessions. The saved comparison uses probability losses and uncertainty by session, not only profitable trades.

All three base histories improve the 60-minute probability loss. That shows the model can extract information in these assumed worlds. It cannot demonstrate that real CGB has the assumed mechanism, strength or persistence. A realistic market test could refute the hypothesis even if this simulation works perfectly.

## H2: the surrounding system can add information beyond CGB alone

US duration, Canadian curve shape and pressure/response measurements can distinguish similar CGB moves with different surrounding conditions. The full model is compared with a CGB-only fit on the same first history. The ablation also removes tape inputs, so it measures the combined information difference rather than the unique contribution of US rates.

The full model improves the first seed's 60-minute probability loss and earns more in the stated execution policy. Its trade count also rises from 16 to 41. This is one-seed evidence with unmatched exposure, not proof of independent cross-market value. Repeated ablations, one component at a time and across independent histories, remain necessary.

## H3: learning conditional paths can connect direction and adverse movement

TRAIN paths form a finite empirical scenario bank. Local similarity, state-conditioned paths and a supervised price-class head provide three path distributions. CAL chooses their mixture. Direction, expected endpoint, quantiles and adverse excursions are computed from the same distribution for a given horizon.

This produces internally consistent probabilities and path summaries. It does not guarantee coverage, sufficient tail support or consistency between separate horizons. The 240-minute interval covers only about 61.8% of endpoints in one base history despite a nominal 80% interval. That is an observed weakness, not something coherence alone fixes.

## H4: a useful signal should survive plausible execution costs

Entry is delayed to the next minute. Buys pay the ask and sells receive the bid. Price differences are converted to cash using the CGB contract value. Fees and additional slippage are deducted separately; spread crossing is charged once. Cash bonds are likewise valued and traded in price units, with their own bid/offer and duration exposure.

The base policy uses one contract, C$4 round-trip fees and one extra tick of total additional slippage; stress uses four extra ticks. These are explicit assumptions. They are not calibrated estimates of achievable fills or order-book impact.

All three base 60-minute model books remain positive under the specified higher slippage. Other horizons and fast-decay stress do not consistently do so. Queue position, fill probability, size-dependent impact and real market-maker quotes still require data. Forecast skill and trade-policy profitability are not interchangeable conclusions.

## H5: the mechanism should matter to the model's success

The fast-decay world shortens the persistence of the hidden pressure process in TEST while keeping the training/calibration prefix unchanged and using the frozen base model. If the model relies on persistent adjustment, this is an appropriate challenge to that assumption.

The 60-minute book loses C$538 at base costs and C$1,198 at stressed costs in this world. The result exposes dependence on persistence. It does not isolate a single learned feature or establish a causal law of real markets.

Other TEST-only interventions change liquidity, the CAD–US coupling or feed quality. They test specific failure modes. They are not an exhaustive robustness certificate, and positive outcomes on one stress realization should not be generalized.

## H6: removing pressure should remove that particular source of predictability

Three controls remove persistent duration-coordinate pressure. They retain mean-reverting curve-shape factors, nonlinear valuation, carry and quote rounding. Their traded prices can therefore retain predictable components.

These controls are informative mechanism ablations. They are **not strict martingale price controls**, and their results cannot estimate the strategy's false-positive rate under a no-alpha market. A separate executable-price martingale control would answer that different question.

## H7: missing information must remain visibly missing

Receiver timestamps determine availability. A stale quote is not a fresh unchanged price. Missing future observations can make a published forecast unscorable; missing exit prices can make the execution book incomplete.

The feed-gap experiment retains unscorable forecasts. All 200 four-hour forecasts in that run have unavailable path outcomes. One 60-minute execution book has an unpriced open trade, so aggregate P&L and drawdown are withheld. Priced subsets remain inspectable but are not relabeled as the complete book.

This is an accounting and measurement requirement, not a trading edge. Silent removal of missing outcomes would invalidate the comparison.

## H8: the market construction must be mechanically coherent

Positive discount curves generate cash-flow prices, clean/dirty relationships, yields, forward rates, DV01 and key-rate sensitivities. Repo carry and coupon adjustments generate delivery costs; the cheapest simulated candidate determines the futures reference price.

These identities are verified. Their correctness does not imply empirical realism of chosen curve dynamics, delivery baskets or conversion-factor conventions. The instruments and baskets are fictional, and the conversion-factor treatment is a teaching approximation. Real calibration, exchange-specific implementation and market constraints remain separate work.

## Decision checklist

- [x] State the instrument, horizons, observation clock and availability clock.
- [x] Separate observable measurements from hidden simulator truth.
- [x] Separate TRAIN, CAL and TEST by session.
- [x] Preserve the frozen model in TEST stresses.
- [x] Compare forecast distributions with unconditional and simpler alternatives.
- [x] Account for price bid/offer, fees, slippage and missing exits.
- [x] Preserve losses, unavailable metrics and no-trade outcomes.
- [x] Report control limitations and the incomplete earlier experiment.
- [ ] Calibrate curve dynamics, cross-market lags, liquidity and costs to real feeds.
- [ ] Establish repeated out-of-sample value beyond simpler real-market baselines.
- [ ] Validate adverse-excursion/tail coverage and horizon consistency.
- [ ] Test a strict executable-price martingale control and broader independent interventions.
- [ ] Establish practical execution capacity and live shadow performance.

The checked items describe completed work in this synthetic study. The unchecked items remain open; the report makes no claim that they have been resolved.
