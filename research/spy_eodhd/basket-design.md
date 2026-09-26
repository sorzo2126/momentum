# Basket research after the independent SPY pilot

**Status: design and source inventory only. No basket data was fetched and no basket experiment was run.** This work belongs to the separate real-data study. It does not change the CGB simulator, fitted models or results.

## What the source actually configures

The first notebook, `1 leader univers.ipynb`, contains four static Python list assignments. They were extracted from notebook JSON with `ast.parse` and `ast.literal_eval`; no notebook code was imported or executed. [basket-universe.json](basket-universe.json) contains every symbol in its original order, exact source variable names, cell indices and hashes.

| Source name | Members | Composition by provider suffix |
|---|---:|---|
| `Q1_BUY_slim` | 20 | 18 US-listed securities, silver `XAGUSD.FOREX`, Dow index `DJI.INDX` |
| `Q1_SELL_slim` | 7 | `IEF.US` plus six FX pairs |
| `Q2_BUY_slim` | 56 | 51 US-listed securities, BTC, ETH, gold, Nasdaq 100 index and S&P 500 index |
| `Q2_SELL_slim` | 17 | 17 US-listed securities |

There are **100 unique configured symbols**: 87 `.US`, eight `.FOREX`, three `.INDX` and two `.CC`. These are distinct identifiers, not 100 independent economic exposures. The lists contain US-listed foreign issuers as well as domestic names; `.US` denotes the provider listing namespace.

`slim` is part of the literal variable names. There is no dynamic slimming step creating these four lists. `Q1` and `Q2` are the keys of `REGIME_MAP` in zero-based cell 16. The comments motivate them as macro quadrants, but the implemented leader selector ranks spread momentum. It does not compute observed growth and inflation acceleration or establish their quadrant signs. Retain the source labels without inventing a macro classification.

The exact Q1 buy list is ADM, BA, BABA, DAL, DLTR, EC, FTI, GM, KGC, KMI, LUV, NEM, RCL, RGLD, SPG, TRMB, UAL and VALE, plus the silver and Dow identifiers above. Its short list is IEF, USDMXN, EURUSD, GBPUSD, USDJPY, AUDUSD and NZDUSD, with exact suffixes preserved in the JSON.

Q2's US-listed buy names are **ACN, ADI, ADP, ADSK, AMGN, AMZN, BMY, BSX, BUD, CHTR, CL, CLX, COR, COST, CSCO, DG, DIS, EA, ECL, GFS, GOOG, HLT, IBM, INTC, JNJ, LHX, LMT, LOW, LULU, MA, MCHP, MCK, MCO, MNST, MO, NFLX, NOC, ORCL, PAYX, PLTR, PM, PYPL, REGN, RL, RSG, SE, SPGI, TXN, ULTA, WM and ZBRA**. Its short names are **AMCX, AMWL, AUPH, BAX, BB, BLDP, FOSL, GEVO, KODK, LUMN, NBR, PTON, RIG, SNOW, UA, VFS and VTRS**. The exact Q2 mixed-asset buy list additionally includes `BTC-USD.CC`, `ETH-USD.CC`, `XAUUSD.FOREX`, `NDX.INDX` and `GSPC.INDX`.

## Which transformations transfer

The notebook loads daily adjusted closes and converts them into log returns. Each leg receives inverse-volatility weights based on an exponentially weighted mean of squared returns, half-life 63 observations and minimum 20 observations. The volatility estimate is shifted by one observation before weights are used. A proportional capped normalization enforces a 35% per-name cap; initialization uses equal weights and later unavailable weight rows carry their previous values.

The legs are combined using a rolling 63-observation covariance/variance hedge ratio, clipped to 0.05–3.0 and shifted one observation. The initial hedge fallback is 0.05. The leader uses each spread's 126-observation rolling sum divided by rolling standard deviation, then selects the maximum. The source backtest applies the leader with a one-observation lag. Source cells 35, 38–42, 52, 59 and 62 contain these stages.

The source's missing-return substitution of zero is not an acceptable default for a new synchronized intraday portfolio. Missing marks must remain visible. Nor should 63 daily observations silently become 63 five-minute bars: that changes the economic memory from months to hours. The initial intraday pilot should calculate risk weights from prior completed daily history and hold them fixed during the session. Intraday adaptation is a later, separately named experiment.

## Three different questions

**Fixed exposure:** can the observer forecast a declared, stable basket contract through different environments? Freeze membership. The first control uses equal leg weights and a fixed gross-normalized hedge. A second variant uses prior-close inverse-volatility weights and a prior-close hedge, held unchanged intraday. These differ in risk weighting, not symbol selection.

**Dynamic selection:** does choosing between eligible baskets add value over observing every basket independently? A selector chooses only from completed information and takes effect on the next declared decision interval. Its signal, turnover and performance are separate from the forecast model. Both branches remain in the evaluation log; publishing only the selected branch would hide selection effects.

**Regime-conditioned evaluation:** does a fixed model behave differently in predeclared environments? This is a reporting stratification, not an automatic allocation policy. For a first small design, classify each session using the sign of SPY's prior 20-session return and prior 20-session realized volatility above/below a TRAIN-only threshold. These four observed market environments are not GDP/inflation quadrants. Keep rare cells visible and do not choose a favorable cell after observing TEST performance.

## The first achievable basket

After the single-instrument SPY adapter is verified, request synchronized five-minute closes for **Q2_US_fixed_membership: the 51 US-listed Q2 buy names and 17 Q2 sell names** listed above. This is a declared adaptation of Q2, not an exact reproduction of its mixed-asset universe. Keep `SPY.US` as an external benchmark and context channel; it is not a new constituent secretly inserted into the source basket.

A US-listed-only Q1 is unsuitable as an unchanged first replica: its short leg reduces to **IEF alone**, making a 35% per-name cap with leg weights summing to one impossible. The full Q1 requires FX synchronization, currency/notional conventions and executable instrument mappings. The index and spot-metal identifiers in both exact baskets also require an explicit choice between a mathematical reference series and a tradable instrument. Do not silently replace them with ETFs or futures.

Before a basket fit, publish a coverage table for every requested symbol: usable dates, IPO/listing history, missing bars, symbol changes, corporate-action treatment and currency. Freeze the inclusion rule before returns are evaluated. A missing security must not be silently dropped because its history is inconvenient. These current configured lists do not provide historical point-in-time membership; a replay of today's list must be named accordingly. No coverage or borrow availability has yet been verified.

## A close-based portfolio with explicit accounting

Weighted log-return sums are useful synthetic coordinates. Exponentiating them creates a geometric index; it does not automatically reconstruct the NAV of an ordinary share portfolio.

For a separately identified portfolio account, choose signed dollar exposures before the interval. With leg weights each summing to one and hedge coefficient beta, gross-normalize the long weights by one plus the absolute hedge coefficient and the short weights by minus beta over that same denominator. At a known initial mark, convert each signed dollar allocation into a share quantity. Hold those quantities constant during the declared session or rebalancing interval. Subsequent close-based NAV is initial capital plus the sum of each share quantity multiplied by its observed price change, with cash and any explicitly modelled financing recorded separately.

This permits a reproducible **hypothetical close-marked synthetic exposure** from aligned bar closes. It does not assume simultaneous executable fills at those closes. Do not label it net traded performance without spread, fees, slippage, borrow and financing assumptions. For the first indicator study, score its conditional movement and path uncertainty directly.

Every constituent used at a decision must have a valid, causally available mark under the declared synchronization rule. Do not fill an absent return with zero or carry yesterday's price through a missing session. Keep tradeable raw-price marks distinct from adjusted daily histories used to estimate risk; reconcile corporate actions instead of mixing their units.

**A basket high is not the weighted sum of constituent highs.** Constituents can reach their extremes at different times. Short positions reverse which constituent extreme contributes to an upper or lower bound. OHLC bars therefore permit bounds under fixed quantities, not the actual simultaneous basket high/low or the order of intrabar events. Start with the synchronized close path and label excursions close-sampled. Finer synchronized observations are required for tighter path claims.

## A bounded experiment sequence

1. **Complete the SPY control first.** Verify completed-bar availability, exchange sessions, gaps, targets, chronological split and frozen forecasting without borrowing any CGB-trained weights.
2. **Freeze the basket contract and data audit.** Begin with Q2_US fixed membership and preserve every requested name's coverage outcome. Choose the eligible date span and TRAIN/CAL/TEST sessions before viewing results.
3. **Build two fixed-contract references.** Compare equal-weight legs against the daily risk-weighted construction. Keep membership and gross exposure convention identical. Publish the long leg, short leg, spread and SPY separately so short-leg or broad-market effects remain interpretable.
4. **Fit the same limited observer family.** Compare TRAIN class frequency, price-momentum-only, clock-only and the state/head/path-expert model. Train all transforms, state heads and empirical paths on TRAIN; fit fusion only on CAL; preserve a final untouched period. Use 60 minutes as the primary horizon, then report matched-origin 120/240-minute results where session length allows them.
5. **Report predefined environment slices.** Use the prior-session trend/volatility classifications above, with paired session-level scores, calibration, close-sampled excursion scores and continuation/opposing/balanced-origin counts. A single profitable environment does not become a new trading filter automatically.
6. **Only then study dynamic selection.** Add a second economically defined, coverage-valid basket before reproducing a leader selector. Freeze its selection rule and delay. Compare it with each permanently held candidate and with a selector-free observer. Record turnover and all rejected candidates' shadow forecasts.

The first objective is to learn whether a stable equity basket gives the indicator a more persistent and interpretable forecasting object than SPY alone. Changing constituents, risk weights, regimes, forecasting architecture and selection rules simultaneously would prevent that question from being answered.
