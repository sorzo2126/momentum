# Research decisions and unresolved questions

Historical baseline: this document records an earlier experiment. Use [the current model derivation](../../docs/10-structural-model-derivation.md) and [iteration protocol](../../docs/12-iteration-and-improvement.md) for active research.

This is a record of the explicit research rationale developed in the conversation. It collects the choices, alternatives, objections and evidence requirements so the project can be understood without the chat. It is not a claim that every possible market mechanism has been enumerated.

## The question we are actually answering

Can information available now improve our estimate of subsequent **outright CGB duration movement over one to four hours**, including its adverse path? We are not trying to identify a named firm's strategy from one reported trade. We are not automatically constructing a Canadian–US hedge or a curve trade.

The original horizon reply, “1 and 4,” was interpreted as a one-to-four-hour holding window and adopted in the subsequent specification. The implementation makes 60, 120 and 240 minutes explicit. The intermediate two-hour horizon is a design grid, not a discovered optimum.

## The principal choices

| Decision | Alternative considered | Why this version chooses it | What could change the decision |
|---|---|---|---|
| Forecast CGB outright | Forecast a CAD–US spread | A US-led duration trend can satisfy the account's objective | A later mandate explicitly targets relative value |
| Predict future movement and path | Predict a whole-day trend label | The live question must remain meaningful at many times of day | A separate session-level allocation task |
| Keep price targets before costs | Define momentum as a net-profitable trade | Market behavior and trading implementation are different research objects | A declared policy-optimization objective with execution data |
| Preserve common and residual movement | Residualize away all US duration | Removing the common component can remove the intended trade | Demonstrated superiority for a specifically hedged objective |
| Use causal state filtering | Smooth states with the complete path | A live state cannot use later observations to repaint the past | Smoothing may be used only for a clearly labeled retrospective study |
| Use actual future price labels | Copy Fractal X's future state grammar as the primary target | A state-accuracy improvement must connect to the economic objective | Future phase forecasts may become a secondary diagnostic |
| Small filtered drift plus shallow XGBoost | A large hidden-state or graph neural model | The stated history is short and the measurement map is still unsettled | More independent history and a clear incremental-loss case |
| Keep a transparent opinion pool | Treat correlated conditional scores as independent likelihoods | The experts share information; agreement cannot automatically create new evidence | An identified joint generative observation model |
| Fixed initial model settings | Repeatedly optimize whichever test period looks best | Selection itself can manufacture apparent evidence | A prespecified nested chronological selection study with additional untouched data |
| Optional modules need declared coverage | Impute four days of swaps across a month | Missing historical measurements are not observations of a quiet market | A longer preserved swap history |
| Display data status and forecast uncertainty separately | One red/green confidence gauge | A neutral market, disagreement and stale data are different situations | No reason to erase this distinction |

## Competing mechanisms can coexist

Continuing orders, delayed cross-market transmission, changed liquidity and endogenous hedging can all contribute to the same move. Completed repricing, replenishing liquidity and countervailing information can reduce continuation. A model should not have to choose exactly one of these stories to express a directional forecast.

This implementation forecasts observable outcomes. It does not estimate a posterior over those causal mechanisms. Distinguishing them would require additional measurements or identification assumptions. For example, price and an unobserved pressure product alone cannot identify both impact and remaining pressure:

$$
\kappa p=(\kappa/c)(cp),\qquad c\ne0.
$$

The same observed movement is compatible with many combinations. This is why the hidden state is called drift, not inventory or force.

## Common duration and local movement: all sign cases

Write an observed interval as $r^C=c+e$, where $c$ is the US-reference component and $e$ the residual. Zero here is an exact algebraic case; a practical near-zero band would need a declared scale.

| Common component $c$ | Local residual $e$ | Interpretation of actual CGB movement |
|---:|---:|---|
| Positive | Positive | Both components support a rally |
| Positive | Zero | Rally described entirely by the reference component |
| Positive | Negative | Opposition; outright sign depends on magnitudes |
| Zero | Positive | Rally in the residual coordinate |
| Zero | Zero | No movement in either coordinate |
| Zero | Negative | Selloff in the residual coordinate |
| Negative | Positive | Opposition; outright sign depends on magnitudes |
| Negative | Zero | Selloff described entirely by the reference component |
| Negative | Negative | Both components support a selloff |

Cancellation is not the same as inactivity. A nearly unchanged CGB price could reflect two substantial opposing components. Conversely, a large residual could reflect stale US observations or a changed beta. The table is a measurement decomposition, not a causal verdict or nine independently learned trading rules.

## The 2s5s flattening example

Define the spread as $s_{25}=y_5-y_2$. Flattening means $\Delta s_{25}<0$. It does not determine $\Delta y_{10}$.

| Example | $\Delta y_2$ | $\Delta y_5$ | Spread change | What it tells us |
|---|---:|---:|---:|---|
| Front end sells off faster | +4 bp | +2 bp | −2 bp | Both yields rose |
| Belly rallies faster | −1 bp | −3 bp | −2 bp | Both yields fell |
| Front end rises, belly falls | +1 bp | −1 bp | −2 bp | Opposing tenor movements |
| Front end rises, belly unchanged | +2 bp | 0 bp | −2 bp | Rotation without a five-year move |

The flattening observation becomes more useful when its component changes, timing, ten-year behavior, US context and swap/government relationships remain visible. “Flattening takes the foot off the pedal” is a hypothesis about a particular configuration, not the definition of flattening.

## The VWAP rejection example

A lower open followed by repeated failed recoveries can motivate continuation research. It does not prove that a trader knew future flow.

The causal event sequence would need to distinguish approach, touch, attempted recovery, confirmation of failure and subsequent outcome. At the first touch, failure is not yet known. A rejection detector must timestamp its confirmation and freeze any reference level used to judge it. Otherwise the reference and event boundaries can move after the fact.

The first implementation measures the observed-trade VWAP reference and distance. It leaves a full rejection detector for an explicit event specification. Useful questions are:

- Was the recovery actually accompanied by executed buying, or only quote movement?
- Did the common duration environment help the recovery?
- Did renewed selling generate more movement than earlier selling of comparable observed size?
- Did displayed depth disappear, replenish, or simply shift price levels?
- Does the proposed pattern add information beyond recent CGB movement on matched observations?
- Would we still identify continuation on a day that never revisited VWAP?

## Price, flow and response need not agree

| Observed signed aggressive flow | Price response | Candidate interpretation, not identified cause |
|---|---|---|
| Selling | Falls | Selling coincides with downward movement |
| Selling | Holds or rises | Possible absorption, countervailing information or incomplete flow coverage |
| Buying | Rises | Buying coincides with upward movement |
| Buying | Holds or falls | Possible absorption, countervailing selling or incomplete measurement |

The current generic L2 adapter does not assert that signed aggressive flow is available. Best-quote sizes support an imbalance measurement; they do not populate this table's executed-flow column. Reconstructing that column requires the actual trade/event schema.

## What the original code audit changed

The source inspection supports a much more specific account than “physics feeds AI.” It separates rolling statistical estimation, current state construction, future state learning, Monte Carlo paths, structural transition scores and final score fusion.

Some source metrics use familiar scientific names for custom proxies. The audit records their actual formulas so they can be evaluated on their own terms. It also identifies a same-interval position-sizing issue in the historical backtest. Saved performance outputs exist, but they cannot be treated as clean proof for the proposed Canadian model.

These findings change what we copy. We retain the research ordering and reference-frame discipline. We do not silently transfer daily windows, all 22 source states, or the source posterior's interpretation into a market with a month of futures observations and a few days of swaps.

## What is decided, provisional, and awaiting information

**Decided:** the exposure, separation of current phase and future target, available-at timing, direct endpoint/path outcomes, preservation of common/local coordinates, separate execution accounting, and explicit missing-data status.

**Provisional research settings:** the one-minute grid, 5/15/30/60-minute feature windows, 60-minute volatility window, 120-minute beta window, phase thresholds, class deadband, shallow trees, session counts and calibration bounds. They are readable defaults. They are not empirical discoveries.

**Awaiting actual feeds:** quote and rate units, receipt clocks, source update cadence, contract mapping, trade corrections, event sequence integrity, L2 granularity, session/flat-by rule, and available history per instrument. No notebook can truthfully infer these facts from a list of available symbols.

**Awaiting empirical evidence:** whether any predictor improves on simple persistence, whether US/curve/book context helps, whether the pool helps, whether path quantiles have adequate coverage, and whether a specified trading policy survives execution costs.

## What counts as progress next

The next substantive observation is not another hand-picked chart. It is a correctly timestamped sample of the actual feed, allowing us to verify what each measurement means and how often it is usable. Then the already implemented pipeline can produce a frozen comparison on explicitly separated sessions.

If the simple predictor wins, the complex layers have not earned their place. If the complex predictor wins only during a single event, the result may be event-specific. If optional feeds improve outcomes only when their timestamps are aligned with hindsight, the result is invalid. If probability forecasts improve but net price-touch results do not, the issue may be the size of the opportunity relative to implementation costs. Those are different conclusions and require different changes.
