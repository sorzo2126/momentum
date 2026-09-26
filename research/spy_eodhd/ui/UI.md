# SPY historical chart workspace

This is the presentation layer for the separate SPY study. It reads the study's local historical OHLCV and saved holdout forecasts. It performs no model fitting and makes no network request for market data.

The price pane shows real five-minute OHLC candles in USD. Bars are labelled at their interval ends, derived from the source's documented interval starts plus five minutes. The second pane shows unsigned share volume in a neutral colour. It never infers buying or selling volume from candle colour. Aggressor flow and bid/ask spreads are explicitly unavailable because they are absent from OHLCV.

The dashed reference is labelled **Bar VWAP proxy**. It is cumulative typical price (HLC3) multiplied by bar volume, divided by cumulative bar volume. It is not an exact transaction-level VWAP. It is recalculated causally within each session by the study's data preparation, not estimated by the renderer.

The separate MODEL strip shows endpoint probability balance: probability up minus probability down, in percentage points. It is not itself a probability, observed flow or execution recommendation. The selected one-hour horizon is primary; two and four hours are labelled research horizons. Exact class probabilities, the origin-specific neutral band, endpoint quantiles and adverse-excursion estimates appear in the readout/details. Price changes and risk estimates use cents per share, while price levels use USD.

The shared cursor selects only the most recently completed bar at or before the cursor. Its forecast and observed context use the same historical origin; future bar or forecast values cannot be chosen by nearest-point rounding. Replay cutoff, pinned historical selection and hover are separately labelled. Opening-range levels and events appear only when their supplied known-at/confirmation times have passed. Axis bounds use only the observed prefix and eligible references. Advancing and rewinding the cutoff does not revise past forecasts.

The initial session and cutoff come from the dataset's metadata. There are no fixed synthetic dates, bond instruments or session-open times. Widget state uses `spy-replay-v1`, independently of other workspaces. The interface is a historical replay with frozen holdout forecasts, not a live feed.

## Data and privacy boundary

`workspace.js`, `workspace.css`, this document and `verify_ui.cjs` contain presentation logic and tests. They can be versioned without bundling market observations. The input is `../private/chart-data.json`. Screenshots, verification records containing source-data hashes, and any market-bearing preview remain under `../private/` or the task-owned visualization directory. The renderer does not expose credentials or embed data in the committed source.

The inline fragment is response content and stays in the task visualization directory. Rebuilding it requires the local private data. Do not commit the fragment or screenshots with displayed prices as part of the reusable UI source.

## Verification

Run `node verify_ui.cjs` with Playwright available; optionally supply the absolute inline-fragment path to test the actual delivered preview. `BROWSER_EXECUTABLE` can select an installed Chromium/Edge executable. All output is written below `../private/`.

The checks exercise six desktop/mobile widths in light and dark themes, exact saved probabilities, replay prefix and causal opening-range visibility, event timing, no future-aware price scaling, unsigned volume colours, explicit missing aggressor flow and spread, between-bar cursor selection, shared crosshair, historical versus current status, horizon selection, missing forecasts, zero versus missing volume, neutral distributions, keyboard stepping, touch pinning and persistent state.

These are software and presentation checks. They do not establish predictive performance; that belongs to the study's frozen holdout evaluation. Current run status and screenshots are private outputs, so this source document does not claim a test pass before the input and browser checks complete.

The delivered preview was checked on 2026-09-26: all 17 browser cases passed, comprising six widths in each of light/dark themes, one touch-input case, and four deliberate data-display fixtures. There were no browser runtime errors. Desktop, mobile and touch screenshots were inspected visually. Two test-harness issues were repaired during the run: the standalone fixture needed a body mount before the script, and touch geometry needed to settle before measuring the hit target. The private test history preserves these attempts.
