# Independent audit of the SPY bar study

This review inspected the runner, protocol, raw bar file, saved features, split and locally generated frozen models. It made no API requests, accessed no credentials and trained no models. It independently recomputed feature prefixes, poisoned future observations, checked targets and inspected the fitted TRAIN transformations. The basket files remain a separate design-only extension.

## Result

No feature or target look-ahead was found in the checked construction. The five-state equations, lagged scale, chronological fitting and future-bar adverse-excursion labels are implemented consistently with the declared bar-clock protocol. This supports using the first output as a real-data research result. It does not make weak forecasting scores stronger or establish executable trading performance.

The first one-hour mixture log loss is approximately **1.09645**, versus **1.09809** for TRAIN frequency and **1.09558** for the price-only head. The reported paired uncertainty includes zero for those differences. The separate structural expert receives effectively zero mixture weight at every horizon. The measured conclusion is that this first SPY test does **not demonstrate an incremental forecasting advantage** for the larger construction over these controls. Keep the full result, including the unfavorable comparisons.

## Independent checks performed

| Check | Evidence and result |
|---|---|
| Feature prefix invariance | Exact DataFrame equality between truncated-input features and the corresponding full-history prefix at five cutoffs: 2025-09-30, 2026-05-01, 2026-07-14, 2026-07-15 and 2026-09-25, each at 16:50 UTC. PASS. |
| Future feature poisoning | Multiplying every later OHLC by seven and later volume by thirteen leaves every earlier feature unchanged at all five cutoffs. PASS. |
| Target construction | At first, middle and last eligible origins for each 60/120/240-minute horizon, recomputed endpoint movement and future-bar low/high adverse extrema match the target. Future windows contain exactly the next 12/24/48 bars. PASS. |
| Session and split boundaries | Every target ends inside its originating exchange session. TRAIN target maturity precedes CAL origins, and CAL target maturity precedes TEST origins. Saved session lists are disjoint and chronological. PASS. |
| Fitted transform provenance | Recomputed medians, IQR scales and standardized matrices from saved TRAIN features match each frozen bank. Every stored bank origin belongs to TRAIN. PASS. |
| Input feature contract | Head feature names match the frozen contract. Return labels, future state, endpoint classes and adverse-excursion labels are absent from the feature matrix. PASS. |
| State and mixture fitting | Code inspection confirms TRAIN-only transition counts and heads, followed by CAL-only state blending and expert weights. Batched TEST predictions do not enter the CAL objective. |
| Event observer isolation | The local SPY event observer produces exactly the original presentation function's output on a controlled break/hold/re-entry/opposite-break fixture. The original function was isolated from its AST; its full module was not imported during this check. PASS. |

The independent feature/target test process loaded runner snapshot SHA-256 `19cf5a2626046e214df429715504ea84c0dc7f7266c1f9ccdb50d8c203451666`. Engineering edits occurred on disk after that module was loaded. These test results therefore apply directly to the captured first-run implementation, rather than pretending that the file remained unchanged during the audit. The separately saved first-run source and final-run provenance preserve that distinction.

## Actual data coverage

The exchange calendar schedules **251 sessions** in the requested interval. The declared completeness rule retains **241 sessions**, with **18,798 regular-session bars**. The fixed split contains:

| Partition | Sessions | First | Last |
|---|---:|---|---|
| TRAIN | 144 | 2025-09-26 | 2026-05-01 |
| CAL | 48 | 2026-05-04 | 2026-07-14 |
| TEST | 49 | 2026-07-15 | 2026-09-25 |

Eligible TRAIN/CAL/TEST origin counts are **7,776 / 2,592 / 2,646** at one hour, **6,048 / 2,016 / 2,058** at two hours and **2,592 / 864 / 882** at four hours. Different horizon samples must not be treated as the same opportunities.

[data-quality-reasons.csv](data-quality-reasons.csv) independently decomposes the ten excluded sessions. Across them, **65 bars are invalid** because price or volume fields are nonfinite. Their timestamp rows exist; these are not absent timestamps. Reason counts can overlap when a bar has both invalid prices and invalid volume, so summing reason columns would double-count some bars.

The calendar correctly includes shortened sessions. However, both 2025-11-28 and 2025-12-24 fail completeness because each has two invalid bars. The retained sample consequently contains **no early-close sessions**. Do not claim that this result empirically validates early-close behavior merely because the calendar code supports it.

## Engineering findings and repairs

The first chart writer imported an event observer from the CGB research directory. This was a presentation-code dependency, not reuse of CGB observations or fitted weights. The user requested an independent study, so [localevents.py](localevents.py) provides the equivalent local observer and removes the need for that dependency.

The first session-quality table recorded valid/expected counts without reason categories, although the protocol promised reasons. The independent reason table fills that gap; the final runner now emits its own reason counts. This changes diagnostics, not eligibility or the fitted sample.

The first empirical bank retained endpoint and long/short adverse summaries from each historical future, rather than its complete sampled trajectory. These correlated summaries were sufficient for all first-run forecasts and scores. The engineering revision additionally stores normalized five-minute close paths. This must preserve their endpoint identity and must not change fitted probabilities or scores. OHLC adverse extrema remain separate from close-path extrema because they retain intrabar highs and lows. Neither representation provides intrabar event ordering.

**Final engineering verification: PASS.** Every numeric and metadata value in the final metrics and comparison tables is exactly identical to the saved first-run tables; their CSV file hashes also match. The added path arrays have shapes 7,776 × 13, 6,048 × 25 and 2,592 × 49 for the three horizons. Every path is finite, starts at exactly zero and ends at its corresponding stored endpoint. The OHLC adverse-extrema summaries cover the close-path extrema, as required. The final runner hash matches its recorded execution provenance, and the protocol hash matches the previously recorded split. [reproduction-check.json](reproduction-check.json) preserves all checks and first/final source hashes. This was an engineering reproducibility check, not a second parameter search.

## Interpretations that remain constrained by the data contract

The provider timestamps are treated as bar starts and decision times as bar ends. The audit confirms this implemented five-minute shift. It does not independently certify an actual historical receipt timestamp: the historical dataset does not contain one. The known bar-clock assumption must stay visible.

The first within-session return is first-bar close minus first-bar open; subsequent returns are close-to-close. This is causal and avoids importing the overnight gap, but it is a declared session initialization rather than an identical observation type at every row.

The full-session completeness screen uses the eventual contents of that session. The protocol explicitly identifies it as a retrospective quality restriction. A live indicator cannot know at the open that the remainder of a session will contain an invalid bar. The present scores describe the retained historical sample; an additional replay with incremental missingness is needed for live availability behavior.

Volume and the cumulative typical-price VWAP proxy are computed only from completed bars. They are not signed flow, actual tape VWAP, depth, spreads or identified participant activity. No such unavailable observations were fabricated. All feature scales and classifier parameters were estimated from SPY; the reused source functions supply algorithms, not CGB-trained coefficients.

Future adverse excursions use bars strictly after the forecast origin. They exclude the already completed origin bar, so an earlier high/low inside that bar cannot be counted as subsequent risk. They still do not establish first-passage order, stop fills, quote execution, transaction costs or net P&L.

The next experiment should answer a declared failure question using a new evaluation identity and genuinely unused observations. The current TEST interval has now been inspected. Improving its score through repeated architecture choices would turn it into development data, regardless of whether the code still calls it TEST.
