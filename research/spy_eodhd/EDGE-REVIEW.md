# Does the real-SPY model demonstrate a trading edge?

**No demonstrated directional trading edge yet.** The frozen model weakly improves some probability scores against a constant forecast, but it does not reliably beat a simpler price-only learner. Its expected price-change forecasts also fail to improve on a zero-change forecast in this sample. There is a more encouraging, narrower finding: modest incremental quality in its uncertainty intervals. That deserves a separate research question rather than being presented as profitable momentum trading.

This review excludes the UI. It examines the original frozen results and adds descriptive diagnostics to the same already inspected TEST sample. No model was refitted, no trading threshold was searched, and no original prediction or fitted artifact was changed. The new risk comparisons are **post-hoc exploration**, not a new out-of-sample confirmation.

## What model did we actually test?

We tested this repository's SPY adaptation of the conditional-path momentum architecture, using Fractal's EODHD connection. We did not execute the complete original Fractal strategy.

The original local `0 README_MODEL.md` describes a six-stage pipeline: select a leader universe, measure daily distributional and regime features, construct the beta/spread pack, build 22-state transition matrices, fit the graph/multi-horizon prediction and deployment logic, and read the resulting signals. The SPY study instead uses one instrument, five-minute bars, five rule-defined observed states, shallow XGBoost heads and a conditional historical-path mixture.

Consequently these results assess our selected transformation of those ideas. They establish neither the performance nor the failure of the original six-stage model. Adding its omitted components is a hypothesis to test, not an explanation that automatically rescues the current score.

## Directional probability evidence

There are 241 retained sessions, divided chronologically into 144 TRAIN, 48 CAL and 49 TEST sessions. TEST runs from 15 July through 25 September 2026. The following log losses give each session equal weight; smaller values are better.

| Model | 60 minutes | 120 minutes | 240 minutes |
|---|---:|---:|---:|
| TRAIN frequency | 1.098091 | 1.099169 | 1.089483 |
| Momentum-only | 1.099661 | 1.094716 | 1.092582 |
| Clock-only | 1.097815 | 1.100631 | 1.089180 |
| Price-only | **1.095584** | **1.089862** | 1.088407 |
| Full-feature direct head | 1.097375 | 1.096544 | 1.089310 |
| Conditional-path mixture | 1.096452 | 1.093547 | **1.085388** |

The mixture improves log loss by about 0.15%, 0.51% and 0.38% relative to TRAIN frequency. Those percentages describe a probability loss, not returns. Price-only wins the one- and two-hour comparisons; the mixture wins the four-hour point estimate. The Brier scores give the same mixture-versus-price-only ordering. [All original scores](metrics.csv).

Against price-only, mixture-minus-baseline log-loss differences and their original 95% five-session block-bootstrap intervals are:

| Horizon | Difference | Interval |
|---|---:|---:|
| 60 minutes | +0.000868 | [-0.004714, +0.006729] |
| 120 minutes | +0.003685 | [-0.003146, +0.011135] |
| 240 minutes | -0.003019 | [-0.015124, +0.008494] |

Every interval crosses zero. The same is true for all 15 original mixture comparisons, including constant frequency. We have not resolved a stable improvement at this sample size. This is not a proof that the true advantage is exactly zero. [Original comparisons](comparisons.csv).

The mixture's three-class accuracy is 34.1%, 37.1% and 42.7%. At four hours, a constant class-frequency forecast already achieves 40.7%, because the observed class mix differs from the shorter horizons. The comparison is not 42.7% versus an assumed universal 33.3% hurdle. None of these accuracies is a trade win rate: neutral is a volatility-dependent endpoint band, and no entry policy was evaluated.

Log loss and Brier score evaluate probability quality. They are suitable for that question; economic utility requires an additional decision and payoff definition. See [Gneiting and Raftery on proper scoring rules](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

## What the added structure contributed

CAL assigned the local-path expert weights of 32.4%, 41.2% and 29.8%, and the direct-class-conditioned expert 67.6%, 58.8% and 70.2%. The separate future-state-conditioned expert received effectively zero weight at all horizons. [Fitted weights](fit-metadata.json).

That is evidence against claiming this particular extra expert improved the calibrated ensemble. It is not evidence that all state information is useless: state and age remain input features to the other components. The standalone structural expert has competitive TEST scores, but replacing the frozen mixture after seeing those scores would be another model-selection decision on an already inspected sample.

Also, `direct_full` and `supervised` are the same endpoint-class forecast up to floating-point arithmetic. Redistribution over historical paths preserves the direct head's class masses. They are not two independent confirmations of predictive skill.

Our five observed states are defined by recent movement and deceleration thresholds. Naming these states does not independently establish that the resulting partition is sufficient for predicting subsequent momentum. The right test is whether conditioning on it improves forecasts beyond its underlying continuous price features, and whether that improvement persists elsewhere.

## How strong were individual forecasts?

| Diagnostic | 60 minutes | 120 minutes | 240 minutes |
|---|---:|---:|---:|
| Median largest class probability | 36.5% | 35.7% | 37.5% |
| Origins with any class probability over 50% | 0 / 2,646 | 3 / 2,058 | 0 / 882 |
| Median up-minus-down probability | +3.17 pp | +4.46 pp | +2.95 pp |
| Fraction with up probability above down | 84.0% | 95.8% | 81.1% |
| Median predicted price change | -2.05 cents | -3.48 cents | +3.83 cents |

The model mostly makes modest probability tilts. More than 50% probability is not a mathematical prerequisite for profitable trading; payoff asymmetry matters. These figures explain the strength and character of the issued forecasts, not a newly chosen trade filter.

The almost persistent positive probability balance at two hours deserves investigation. We must determine whether it adds conditional information beyond class frequencies and market drift; repeated positive readings do not establish that it is discriminating between opportunities.

## Probability direction and expected profit are different quantities

In 53.6%, 74.9% and 15.8% of origins respectively, the sign of up-minus-down probability disagrees with the sign of expected price change. That can occur in a coherent distribution: fewer negative outcomes can carry larger losses, and neutral outcomes need not have mean zero.

Writing class-conditional expected price changes as signed quantities gives:

$$
\mathbb{E}[\Delta P\mid X]
=p_+\mu_+ + p_0\mu_0 + p_-\mu_-.
$$

The probability balance is merely:

$$
I(X)=p_+-p_-.
$$

Their signs need not agree. Therefore the probability balance cannot be interpreted directly as expected P&L. A decision rule must specify which forecast quantity it uses and what risks and costs accompany the action. The disagreement is not an implementation contradiction, but it is a consequential semantic distinction in using the model.

## Expected price changes did not show useful incremental accuracy

| Mean absolute endpoint error | 60 minutes | 120 minutes | 240 minutes |
|---|---:|---:|---:|
| Mixture expected change | 93.94 cents | 128.57 cents | 192.85 cents |
| Predict zero change | **93.73 cents** | **128.46 cents** | **191.82 cents** |

The mixture also has higher squared error at all three horizons; squared error is the appropriate loss for assessing a conditional mean forecast. Paired intervals on the differences cross zero. We cannot conclude that the mixture is reliably worse, but neither error measure supplies evidence of improvement.

Pooled raw correlations between predicted and realised changes are -0.031, -0.024 and -0.094. After scaling both by the known origin volatility, they are -0.021, +0.015 and -0.038. These overlapping-origin correlations are descriptive, not independent-sample significance tests or instructions to reverse the signal.

## There is a narrower positive finding in uncertainty forecasts

The original 80% endpoint intervals cover 79.4%, 80.7% and 78.3% of outcomes. Coverage alone cannot show incremental skill: sufficiently wide intervals can cover many observations.

For this review, the simple comparator uses the session-weighted TRAIN distribution of normalized future changes and rescales it by the same known current volatility. It has no local-neighborhood, state or tree conditioning. The interval score rewards narrow ranges while penalising outcomes outside them:

$$
\operatorname{IS}_{\alpha}(l,u;y)
=(u-l)+\frac{2}{\alpha}(l-y)\mathbf{1}_{\{y<l\}}
+\frac{2}{\alpha}(y-u)\mathbf{1}_{\{y>u\}},
\qquad \alpha=0.2.
$$

This jointly assesses width and misses; lower is better. It follows the proper interval-score construction discussed by [Gneiting and Raftery](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf).

| Horizon | Mixture interval score | Simple baseline | Relative improvement | Paired 95% interval for difference |
|---|---:|---:|---:|---:|
| 60 minutes | 466.52 | 471.24 | 1.00% | [-7.92, -1.46] |
| 120 minutes | 631.60 | 643.56 | 1.86% | [-19.99, -4.53] |
| 240 minutes | 1,002.32 | 1,023.90 | 2.11% | [-43.29, -2.04] |

Scores have price-change units of cents, but are statistical losses, not profits. The intervals are narrower on average than the simple comparator. At one hour, for example, average width is $2.98 versus $3.12, with coverage 79.4% versus 80.6%.

These unadjusted intervals all favour the mixture in this sample. This is the most encouraging incremental finding in the review. However, these comparisons were added after inspecting TEST; 21 supplementary error/risk comparisons were calculated and no multiple-comparison adjustment was applied. Treat this as a candidate advantage in uncertainty modelling that needs a frozen repeat on unused observations.

Adverse-excursion quantile losses also improve in their point estimates at all horizons and both sides, with mixed uncertainty. Short-side 80th-percentile coverage remains low at four hours: 75.2%, so about 24.8% of observed short adverse excursions exceed the claimed 80th percentile. These are excursion forecasts, not stop-fill probabilities. [Risk diagnostics](risk-baseline-diagnostics.csv), [all supplementary comparisons](risk-baseline-comparisons.csv).

## Does it specifically identify momentum continuation?

After an observed upward state, realised continuation occurs in 37.3%, 41.3% and 33.8% of origins at the three horizons. After a downward state, continuation occurs in 28.9%, 31.5% and 22.7%. The one-hour downward-state group instead finishes in the upward endpoint class 39.3% of the time. [Original directional breakdown](observed-direction-breakdown.csv).

The distinction is important: an observed falling market is not itself evidence that continuing to short has positive expectation. These descriptive subsets are not an approved reversal strategy either. They overlap in time, use a volatility-dependent neutral band and do not determine average payoffs or executable returns.

The endpoint label also does not fully encode the original idea of useful momentum. A move that continues smoothly and a violent reversal that happens to finish on the same side can share a class. The bank retains path and adverse-excursion information, but CAL optimises endpoint class log loss, not continuation persistence, first-passage risk or realised trading utility. The current objective only partly matches the intended use.

## The evidence has boundaries

- There are 49 TEST sessions, not thousands of independent trades. Consecutive one-hour forecasts overlap heavily. The block bootstrap respects some clustering, but does not turn this into evidence across many independent market regimes.
- The first usable forecast is 10:35 ET because of the same-session volatility warm-up. This study has no model forecasts for the opening hour, despite opening behaviour being part of the motivating use case.
- Four-hour origins are only 10:35–12:00, two-hour origins end at 14:00, and one-hour origins end at 15:00. Comparing horizons also changes the time-of-day sample.
- All horizons use one chronological split. The 49 TEST days do not certify stability across bear markets, volatility shocks or different breadth conditions. The configured Fractal basket has not been backtested here.
- Ten incomplete sessions were removed retrospectively. Both early closes are excluded, so the results do not empirically validate shortened-session or live missing-feed behaviour.
- The source is historical OHLCV with an assumed completed-bar clock, not a historical quote/receipt-time tape. Volume is unsigned and VWAP is a bar proxy.
- No position ledger, trade entry rule, capital allocation, repeated-signal policy, borrow cost, slippage model, net P&L, Sharpe ratio or drawdown was measured. We can add an explicitly assumed cost scenario using bars, but should not describe its fills as observed executions.

## What the thesis suggests asking next

The local Beta and Stationary Time Series lessons start from the exposure and its surrounding economic system. They distinguish the underlying basket/spread from the features used to describe it, and require the claimed stability to be checked on the relevant object.

Applied to this study, my interpretation is: **does SPY's recent path contain enough information about the environment producing the next move, or did we ask an elaborate conditional model to infer a missing system from one price series?** This is a research question, not a claim to know the author's private judgement.

A basket experiment could expose breadth, sector leadership and common versus idiosyncratic movement. That is a reasoned hypothesis because the original framework starts with an exposure system; it is not proof that adding stocks will improve predictions. Likewise, increasing the number of states or adding geometric features is justified only by a discriminating measurement and a comparison showing its contribution.

## The next experiment should answer three concrete questions

1. **What must the indicator predict?** Define either unconditional future direction, continuation of an already observed direction, or useful path continuation subject to an adverse-excursion condition. Keep these distinct outcomes and state the intended trading decision before selecting a loss.
2. **What information is missing?** Compare the current price-only benchmark against one declared addition: the designed basket's breadth/relative movement, a justified alternative state partition, or an opening-session initialization. Do not add all three at once and then attribute an improvement to a preferred story.
3. **Does that information improve a decision?** Freeze a selective position policy using TRAIN/CAL only, specify overlapping-signal handling, delayed entry and same-session exit, and report gross outcomes plus a range of round-trip costs. Evaluate on unused data with risk-matched simple policies and clustered uncertainty. Separately repeat the promising uncertainty-interval comparison.

Repeatedly changing a strategy after inspecting the same historical evaluation can produce a selected result that fails elsewhere; see [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf). The current TEST period can now be used for diagnosis, but cannot remain an untouched confirmation sample for a redesign informed by this review.

My judgement is to retain the measurement and validation infrastructure, treat the uncertainty result as promising, and redesign the directional experiment around a clearer exposure and decision. **There is currently no measured basis for calling this a profitable SPY momentum strategy.**

## Reproduce this review

Run `python research/spy_eodhd/analyze_results.py` from the repository root using the existing local study artifacts. The script writes [edge-diagnostics.json](edge-diagnostics.json), [day-level-diagnostics.csv](day-level-diagnostics.csv) and the two risk comparison tables. It records hashes of all five frozen inputs and verifies that they remain unchanged. It does not fetch data or train a model.
