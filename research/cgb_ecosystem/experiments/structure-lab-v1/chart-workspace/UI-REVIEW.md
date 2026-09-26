# Chart workspace: source review, design choices and acceptance tests

Reviewed on 2026-09-26. This is a review of public official documentation and a proposed CGB interaction contract. It is not a hands-on evaluation of the paid BigShort application, a reconstruction of its proprietary indicators, or evidence that the proposed interface already improves trading decisions. The manual tasks below must be run against the implementation and their outcomes recorded separately.

## Documented reference behaviour

The summaries in this section concern the referenced product. The CGB design decisions that follow are our own adaptation.

| Official source | What the documentation establishes | Evidence boundary |
|---|---|---|
| [Charts & Navigation](https://help.bigshort.com/docs/getting-started/charts-navigation), updated July 24, 2026 | Version 2 uses a consolidated chart with a prominent price pane, configurable indicators, saved layouts, session and timeframe controls, and a movable values panel. Historical sessions can be selected by date. Event dots have inspectable details. | Descriptions of controls establish intended behaviour; they do not establish discoverability, speed, accessibility or absence of interaction bugs. |
| [The Main Chart](https://help.bigshort.com/docs/tabs/chart), updated July 21, 2026 | A symbol's price is above stacked indicator panes, with side panels and settings organised by indicator family. Dated URLs identify historical sessions. | The page is a layout/feature guide, not a published usability study. Its stock-specific indicator inventory is not a required CGB inventory. |
| [FastFlow and MomoFlow](https://help.bigshort.com/docs/indicators/core-flow/fastflow-momoflow) | The guide explains signed bars, exact-value inspection, cumulative lines, and a colour convention that also encodes agreement between two proprietary measures. It explicitly warns that automatic rescaling can exaggerate a bar's visual importance. | The participant classifications and trading interpretations are the vendor's claims. We have neither replicated their classifier nor validated transfer to CAD rates. Navigation and indicator pages differ in how they describe combined versus separate panes; a precise clone would require observing the app. |
| [M2: RC1 + RC2](https://help.bigshort.com/docs/indicators/elite/m2), updated July 20, 2026 | The pair is described as fragility under institutional versus crowd pressure. The page distinguishes its formal definition from community descriptions of rendering and use, including forming bars and session effects. | The guide itself says rendering details need on-chart verification. Community interpretations are not validated estimates of confidence or a CGB measurement contract. |

The useful reference is the visual grammar: price provides the spatial anchor, time links observations, and additional measurements can be inspected without leaving the market context. “This looks like a trading chart” is a design hypothesis; “traders can identify a contradiction faster” is a testable claim.

## The proposed CGB workspace

The first view should answer: what moved, what arrived with it, which level or event matters, and what does the saved model forecast from the selected time? A page of equally weighted cards forces the trader to reconstruct these relationships mentally. The chart should contain them in one coordinate system.

1. **Price receives most of the vertical area.** Display received midpoint candles, identified as such rather than actual exchange-trade OHLC. Overlay VWAP and a small set of causal reference levels. Candle interval and forecast horizon are distinct controls: a five-minute candle does not imply a five-minute forecast.
2. **One aligned flow pane is visible by default.** Use the received classified signed quantity and its actual unit. Positive and negative bars report aggressor imbalance, not identified institutional buying or predicted price direction. A cumulative line, if added, needs a separate unit/axis and an explicit session reset; it must not hide the signed bars.
3. **A narrow MODEL strip presents one chosen forecast horizon.** Label the selected 1h, 2h or 4h horizon, origin, expiry, class boundaries and model availability. Show absolute up/down/neutral probabilities and, for an established directional state, the same masses relabelled as endpoint continuation/opposite/neutral. Endpoint continuation is not uninterrupted trending or state survival. The current independent horizon fits must not be drawn as one coherent probability process.
4. **One cursor controls the historical readout.** Price, flow, event details, observed state and forecast refer to the same selected information cutoff. The forecast is the latest saved record available at or before that time, with its original origin timestamp visible. No nearest-future match, interpolation of probabilities, or substitution of the session's final state is allowed.
5. **Details appear on selection.** A selected dot or line opens its definition, timestamp, value, unit and source. Model diagnostics and provenance live in a collapsible panel. Useful detail should be available without permanently reducing the price chart to a thin strip.

Use green consistently for upward price movement or positive signed quantities and magenta for downward or negative quantities, matching the requested visual language. Retain signed numbers and text so colour is not the sole channel. Neutral forecasts should have a labelled neutral fill; unavailable observations should appear as gaps or gray/hatching with “unavailable.” Gray must not silently mean zero, balanced, unclassified and stale at once.

## Information-time rules

There are three separate clocks: the data's event time, its arrival/availability time, and the selected replay cutoff. The UI may show both event and receipt times in details. Only observations available by the cutoff may alter a candle, histogram, event marker or forecast readout.

An opening-range high/low becomes a completed level only when its configured interval has finished and its required observations have arrived. Before completion, show “forming” or omit the final lines. Do not paint the eventual completed range backwards across the opening minutes. The selected range interval and session timezone must be visible in its details.

For events confirmed by a rule after several observations, anchor the signal marker at its confirmation/availability time. The earlier pattern start may be referenced in the detail panel as an earlier observation, without implying that the confirmed event was known then. A delayed trade marker must likewise disclose when it was received. A scheduled future event may be shown as known schedule context, but its outcome or realised impact cannot be shown before release.

Historical bars and forecast records should remain as known at their saved cutoffs. If the dataset contains corrections, late arrivals or partial bars, the displayed mode must say whether this is an as-received replay or a revised historical view. The current prototype should use the former where its inputs support that reconstruction.

## Scaling, crowding and responsive layout

The scale control must disclose whether an axis is fitted to the visible window or the entire **observed** session. “Entire session” must not incorporate future extrema beyond the replay cutoff. A visible-window zoom may change pixels per unit, but values, signs, zero line and units remain unchanged. Flow should use a zero-centred axis, with both bounds visible; a tiny imbalance should not resemble a large event solely because all other observations were removed.

At approximately 1440×900, price should remain dominant with aligned flow/model strips below it. At approximately 390×844, keep price first; place controls in a compact wrapping row and move details below the chart or into a sheet. Do not compress all desktop sidebars onto the screen. Preserve adequate touch targets and allow inspection without hover. These are proposed acceptance viewports, not claims of device coverage already achieved.

At high event density, use small dots and selected-event labels rather than printing every description over candles. Clustering must expose count and individual timestamps. Overlapping events remain keyboard-accessible through a chronological list. Any filtering must show its active state; a clean chart should not falsely suggest that hidden events did not occur.

## Manual acceptance tasks

Record implementation version, viewport, input mode, exact action, observed result and screenshot for each task. The expected outcomes below are requirements, not reported passes.

| ID | Task and fixture | Expected result |
|---|---|---|
| U01 | Open the default view at 1440×900 and identify instrument, contract, date, replay cutoff and candle interval. | All are discoverable without opening settings; price is the dominant plot; no clipped controls or horizontal page overflow. |
| U02 | Repeat at 390×844 and 768×1024; open and close details. | Price, legend, horizon control and cutoff remain readable. Details do not permanently cover the chart. Controls wrap or move rather than shrinking text to illegibility. |
| U03 | Move the cursor from 10:30 to 09:45. Compare candle, flow, observed state and model origins. | Every readout identifies the historical selection. The model is from a saved origin no later than 09:45. Current/latest state is not silently displayed beside historical values. |
| U04 | Select a time between two five-minute forecast origins. | Use only the preceding eligible forecast, show its origin and age, and retain the chosen historical cutoff. A future forecast is never selected by nearest-neighbour rounding. |
| U05 | Use a cutoff before the first eligible forecast and after the final eligible forecast for a horizon. | Explicit unavailable/expired status with reason. No invented zero forecast and no silent carry-forward across eligibility boundaries. |
| U06 | Toggle 1h → 2h → 4h while keeping candle interval and cursor fixed. | Only the selected forecast quantities, neutral band and expiry change. Received candles and flow do not move. No aggregate confidence score or interpolated multi-horizon fan appears. |
| U07 | Inspect upward, downward and balanced observed states. | Continuation probability maps to up for upward and down for downward; the relative label is omitted in balance. Absolute probabilities remain unchanged. The UI explains endpoint continuation rather than uninterrupted trend. |
| U08 | Replay just before, at and after opening-range completion. | Final range lines appear only after their information is available. Earlier bars are not decorated with the final high/low. The range interval and timezone are stated. |
| U09 | Replay an event that needs later confirmation, plus a deliberately late-arriving record. | Nothing confirms early. Details expose event versus availability time. Advancing the cutoff reveals the event at the correct information time. |
| U10 | Inject missing flow, a stale quote, absent swaps, neutral forecast and genuine zero net flow as separate cases. | Gaps/status messages differ from economic neutrality and zero. Disabled/excluded inputs cannot be cited in explanations. A stale forecast retains its actual age and origin. |
| U11 | Zoom to a quiet ten-minute window, then back to the observed session; toggle scale mode. | Axis labels make the scaling change explicit. Same bar has the same numeric quantity and sign. Session scaling uses no future extrema. Reset restores a documented view. |
| U12 | Pack multiple events into one candle and zoom out to a full session. | Candles remain visible, labels do not collide continuously, and every event remains selectable via a list or cluster. No event silently disappears without an active filter indication. |
| U13 | Navigate using Tab, arrow keys, Enter and Escape without a mouse. | Visible focus; chronological cursor stepping; horizon and event selection available; details can close; no keyboard trap. The same data values are available as in pointer use. |
| U14 | Use touch to inspect a candle and event, then pan/zoom. | Tap pins a readout without requiring hover. Inspection and navigation gestures do not accidentally conflict. A clear action releases the selection. |
| U15 | Turn optional layers on/off and restore defaults. | Price/flow/model identities and clocks remain fixed; settings change visibility, not forecasts. Active filters are visible. A reproducible default layout can be restored. |
| U16 | Move the replay cutoff backwards after viewing a later interval. | Future candles, confirmed events, labels, annotations derived from future data and axis extrema disappear. Only explicitly future scheduled events known at the cutoff may remain. |
| U17 | Compare green/magenta readings in light and dark modes and with colour removed. | Signs, legend text and selected values still communicate direction; unknown and neutral remain distinguishable. Contrast and focus markers remain usable. |
| U18 | Ask a trader to explain one contradiction: rising received price with a forecast favouring the opposite endpoint. | They can identify observation versus forecast, the selected horizon and adverse path uncertainty. Record misunderstandings rather than marking success from visual attractiveness. |

## What to iterate first

First test information integrity: U03–U10 and U16. A visually convincing chart with a future-informed level or misaligned readout teaches the wrong pattern. Then test navigation and layout: U01–U02 and U11–U15/U17. Finally run the trader interpretation task U18 with several examples, including mixed evidence and unavailable data.

Compare the chart workspace with the earlier card/report snapshot on fixed tasks: identify the selected horizon, find the largest observed sell-flow episode, distinguish a failed recovery from a confirmed forecast reversal, recognise an unavailable source, and explain why endpoint continuation differs from uninterrupted trending. Measure correct answers, time taken, wrong selections and explanation errors. Counterbalance interface order and use different but comparable sessions to reduce memorisation. A small internal pilot can reveal defects; it cannot establish that the interface improves live trading performance.

Do not solve every failure by adding a new coloured indicator. If a user mistakes the model for an observation, strengthen the boundary and timestamp. If a user cannot locate the event, improve selection and temporal alignment. If the numbers are correct but the visual impression changes under zoom, repair scaling. If a term is misunderstood, state the quantity and unit before inventing another score.
