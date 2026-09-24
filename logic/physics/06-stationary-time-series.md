---
author: Karim Khemiri
organization: Khem Kapital — société de R&D en finance
---

# Stationary Time Series

Being able to transform time series into stationary series is a Holy Grail, because the moment the object stops drifting, the entire strategic framework mechanically becomes simpler.

A stationary series, in the operational sense, is one whose behavior does not fundamentally change over time:

it does not "run away," it oscillates around a center, and this center remains interpretable.

Once you have that, reasoning becomes cleaner, because you are no longer trying to capture a trend that sweeps everything away: you are working on a deviation that reverts.

This is exactly why stationarity matters:

if it persists, then risk and structure metrics become truly exploitable over time, because they cease to be snapshots of a fleeting regime.

You regain consistency, so decisions become more mechanical, and the entire chain framework, management, hedging is simplified.

Now, a critical point: you must be clear about the object you are making stationary, otherwise, you are just telling yourself a story. Testing for stationarity on daily variations is a classic trap, because daily returns are often already close to noise centered around zero, even when the price itself drifts heavily. In this case, ADF and KPSS tests can "validate" something that has no strategic value for the capital. For a mean-reversion logic, what must be stationary is not the daily variation: it is the level of the spread, meaning the difference in value (or log-price) between two baskets.

The construction is therefore done in two stages. First, you can work with log returns to build clean and stable baskets in terms of contribution: for each asset, you set

$$r_t = \ln(P_t / P_{t-1})$$

You build a "plus" basket and a "minus" basket via weighted aggregations

$$R_t^+ = \sum_i w_i^+ r_{i,t}$$

$$R_t^- = \sum_j w_j^- r_{j,t}$$

The weights are not there to "optimize" performance: they serve to prevent a single asset from taking control of the basket.

The principle is simple

underweight what is too volatile, overweight what is more stable, and impose a weight cap to avoid disguised concentration.

At this stage, you obtain two composite returns.

Next, to test the stationarity that actually matters, you reconstruct synthetic levels.

You accumulate the composite returns to obtain log-synthetic levels

$$L_t^+ = \sum_{\tau \leq t} R_\tau^+$$

$$L_t^- = \sum_{\tau \leq t} R_\tau^-$$

The level spread is then written as

$$S_t = L_t^+ - k L_t^-$$

$$k \times L_t^-$$

The role of k is one of scale alignment

to prevent the spread from drifting simply because one basket structurally carries more amplitude than the other.

Once St is built, there is no more storytelling to do you have to test.

The two tests, ADF and KPSS, are complementary because they do not share the same starting hypothesis.

ADF starts from the idea that the series drifts (presence of a unit root) and seeks to reject this idea

KPSS starts from the opposite idea, that the series is stationary, and seeks to reject this stationarity if it is not sustainable.

Therefore, the operational rule is simple we want ADF to reject non-stationarity, and KPSS to not reject stationarity.

When both point in the right direction, you have a serious signal that the level spread is indeed a "ranging" object over time, not just an illusion based on daily variations.

That is exactly the core of the lesson: it is not about "predicting" a price, but about building a composite object whose level is stationary, and then mechanically validating it with ADF and KPSS.
