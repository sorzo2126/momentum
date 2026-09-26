# Chart data and causal replay contract

The chart uses the existing `base-1729` synthetic session of **19 February 2025, 08:00–16:00 America/New_York**. It contains 96 completed five-minute midpoint bars, 168 saved forecasts across 60/120/240-minute horizons, and five confirmed opening-range events. This is the frozen model's first TEST session, not a new live or market-calibrated sample.

Run from the repository root:

```powershell
python research/cgb_ecosystem/experiments/structure-lab-v1/chart-workspace/prepare_data.py
```

This writes [chart-data.json](chart-data.json) and [data-verification.json](data-verification.json). It reads the existing received quotes, saved features, saved state observations and saved forecasts. Source hashes are retained; the original files are unchanged. The data file is approximately 216 KB. No new model, forecast, policy or order is created.

## Schema

| Collection | Meaning |
|---|---|
| `meta` | Session, timezone, units, synthetic status, measurement definitions and consumed-source hashes |
| `bars` | Completed five-minute midpoint OHLC, session VWAP, received flow ratio, recent price movement, price-state label and available opening-range levels |
| `forecasts` | Saved frozen-model probabilities, horizon, origin, known target time, neutral band, endpoint distribution summaries and long/short adverse-excursion quantiles |
| `events` | Causal opening-range transition events, each stamped at confirmation |
| `opening_range` | Fixed first-30-minute high/low and the time they first become known |

Every chart record carries `time` in Unix epoch **milliseconds** and `as_of` as an explicit UTC timestamp. Bar `local_time` is New York display time. The opening range includes `known_local_time`, `window_start_local` and `window_end_local`. Forecasts include both `target_time` in milliseconds and `target_at` in UTC, plus `origin_midpoint` for translating forecast ticks into price coordinates. The bar timeframe and model forecast horizon are distinct controls.

## Prices, VWAP and flow

The original receiver-time quote selector is reused. At each one-minute decision time it selects the newest event actually received; a delayed older event cannot rewind the quote. Bid/ask must be valid and no more than 30 seconds old. Midpoint is the average of the atomic bid and ask.

Five-minute OHLC is a reduction of these one-minute midpoint observations. It is **not traded-price OHLC or a complete tick high/low**. The first bar includes the session-open snapshot and therefore has six snapshots; later bars use observations strictly after the previous close and up to the current close, normally five snapshots. A bar timestamp is its completion time. `valid_snapshots`, `expected_snapshots` and `complete` expose coverage.

VWAP is the existing observed session-tape VWAP, reconstructed from the received midpoint and the saved `vwap_distance_ticks` feature. Its formula in words is midpoint minus distance-in-ticks multiplied by tick size. This preserves the original calculation instead of inventing a volume proxy from candles. VWAP can be available while the forecasting model is still warming up.

`flow_pressure` is buy-initiated classified volume minus sell-initiated classified volume, divided by their sum, across the preceding five receiver-minute bins. It lies between -1 and +1. Availability requires positive classified volume, at least 80% of total volume classified, and no contributing bin invalidated by a trade delayed more than 30 seconds. It is a **signed classified-volume ratio**. It does not identify institutions, their remaining inventory, absorption, hidden orders or a probability of a trend. Missing flow is null, never replaced with zero.

`mom_ticks_30` is the observed preceding-30-minute midpoint movement in ticks. `mom_z_30` is the existing standardized version, when sufficient history is available. Price-state labels are the frozen model's price-derived descriptions; they are not direct order-response measurements. Unready history is explicitly `warming_up`. The first saved model forecast is at **09:05 New York time**, while earlier price, flow and VWAP observations remain visible.

## Opening-range event observer

The fixed range is computed from valid received midpoint snapshots from 08:00 through 08:30, endpoints included, and becomes available only at the completed 08:30 bar. Its high is 112.325 and its low is 112.205 in this session. The UI must hide both levels before their `known_at_time`.

The observer waits for a later completed bar:

1. A strict close above or below the range emits `break_above` or `break_below`.
2. The second successive completed close on the same outside side emits `held_above` or `held_below`. The initial break counts as the first close. The marker is stamped on the second close, never moved backward onto the first.
3. Further closes on that same side emit no additional markers.
4. A completed close back inside the range emits `returned_inside` and resets the outside episode. This also records later re-entry after a previously held break.
5. A direct completed-close jump from one outside side to the other starts an opposite break episode. It does not fabricate an inside close.

The actual event times are 08:35 break above, 08:40 held above, 11:25 returned inside, 11:35 break below and 11:40 held below. These are observed price events. They are **not model confirmation, support/resistance proof, absorption, trade recommendations or retrospectively chosen turning points**.

## Forecast semantics and replay

The original probability values are copied exactly from the parsed saved forecasts. The endpoint classes are down, neutral and up relative to the forecast origin and its recorded neutral-band width. The displayed indicator is the saved up probability minus down probability. A 60-minute forecast is not a statement that all intervening bars will continue in the same direction.

`endpoint_q10_ticks` and `endpoint_q90_ticks` describe the endpoint distribution. They are not a calibrated simultaneous path envelope. `mae_long_q80_ticks` and `mae_short_q80_ticks` are separate adverse-excursion quantiles; they are not stops. The horizon models are fitted separately, so they must not be presented as a single coherent joint scenario tree.

No realized future return, future class, future adverse excursion or outcome-availability column enters the JSON forecasts. The target timestamp is known at the origin because it is origin plus the stated horizon. Near the session close, there is no newly originated forecast for a horizon that cannot finish within the session. The interface should show the displayed forecast's origin explicitly and should not silently relabel an older forecast as current.

For any replay cursor, display only bars, forecasts and events at or before that cursor; show the opening range only once its knowledge time has passed. Select an individual forecast by both its origin and horizon. Viewable future file contents are replay data, not information the historical observer possessed.

## Verification

The adapter's checks pass:

- Exact OHLC reductions and price ordering from causally selected one-minute snapshots.
- Every source quote used in a completed bar was received by that bar's completion.
- Prefix invariance at six cutoffs: 08:20, 08:30, 09:05, 10:30, 12:00 and 13:55.
- Poisoning future quote, feature, observation and forecast numeric values leaves all earlier outputs unchanged.
- A quote with an old event timestamp but receipt after the cursor remains unavailable.
- Saved forecast numeric fields remain identical, probabilities sum to one, and future outcomes are excluded.
- Warmup remains unavailable, missing flow stays null, and opening-range values are absent before 08:30.
- Opening-range markers occur only after the range is known; a controlled event sequence verifies break, two-close hold, reset and suppression of repeated markers.
- Consumed source hashes remain unchanged.

These checks establish the adapter's causal replay behavior for the supplied records. They do not independently recompute every upstream feature or validate the synthetic model against a live market. Browser interaction tests belong to the chart interface.
