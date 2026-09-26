# Source dossier for the compact CGB indicator

The passages below support display choices, not a claim that the author designed this CGB screen. Original wording is preserved. English translations are labelled; the first four essays are already in English in the supplied source. The interpretation after each quotation is ours. This dossier draws on the relevant thesis passages and inspects the actual notebook 6 reader and display code.

The source root inspected was `C:/Users/mn262/Downloads/fractal-x-main/fractal-x-main`. Physical text-file lines are one-based. Notebook cell indices are zero-based JSON indices and their source-line numbers are one-based. [quotes.json](quotes.json) records exact locations, source hashes, translations and quotation counts. Every excerpt was verified against its stated line; each source contributes at most 25 verbatim words here.

## Exact passages and their use

### Q01

**Source:** `theses/source/PHYSICS/01 beta.md`, line 12.

> What remains stable as long as no one breaks the system's invariances?

**Language:** English original; no translation.

**Our display decision:** Name the reference and show when it is weakening; a direction score alone cannot describe reference validity.

### Q02

**Source:** `theses/source/PHYSICS/02 smart beta.md`, line 20.

> I define (w) as a small vector of exposures, because that is where constraints actually bite

**Language:** English original; no translation.

**Our display decision:** Organise the compact evidence view by economic exposure: CGB duration, common US duration, Canadian curve and liquidity response; avoid a wall of unrelated indicators.

### Q03

**Source:** `theses/source/PHYSICS/03 zureck.md`, line 119.

> ρ is a hidden state.

**Language:** English original; no translation.

**Our display decision:** Label inferred pressure separately from directly observed price, flow and depth. Do not present an inferred unfinished seller as a measured inventory.

### Q04

**Source:** `theses/source/PHYSICS/04 zureck vs laplace.md`, line 50.

> The calculation is done at t... the action at t+1 (anti-circularity).

**Language:** English original; no translation.

**Our display decision:** Display forecast origin, horizon and data freshness. A present state label and its future forecast must never share an ambiguous time label.

### Q05

**Source:** `theses/source/PHYSICS/09 ummo.md`, line 726.

> (vrai, faux, vrai-et-faux, ni-vrai-ni-faux)

**English translation:** (true, false, both true and false, neither true nor false)

**Our display decision:** As our operational adaptation, distinguish support, opposition, conflicting fresh evidence and unavailable evidence. The source supplies a four-valued vocabulary; our feed/evidence mapping is a design choice.

### Q06

**Source:** `6 signaux.ipynb`, cell 1, source line 214.

> Tag du graph a T par barre

**English translation:** Graph tag at T for each bar

**Our display decision:** Keep the observed-state overlay tied to completed observations, distinct from the forecast line.

### Q07

**Source:** `6 signaux.ipynb`, cell 1, source line 241.

> Dernier tag predit t+1

**English translation:** Latest predicted tag for t+1

**Our display decision:** Keep the forecast visibly forward-looking and horizon-specific; do not repaint observed bars with future predictions.

### Q08

**Source:** `5 algo fractal x.ipynb`, cell 102, source line 14.

> JAMAIS vers thr/pos/bias

**English translation:** NEVER toward threshold/position/bias

**Our display decision:** In this specific source path, Ashby diagnostics are published rather than applied to trading parameters. A contradiction/health indicator can inform the trader without silently issuing a control action.

### Q09

**Source:** `0 README_MODEL.md`, line 599.

> La performance ne remplace jamais le contrat de donnees. Un artefact incoherent est invalide meme si ses metriques sont bonnes.

**English translation:** Performance never replaces the data contract. An inconsistent artifact is invalid even if its metrics are good.

**Our display decision:** An expired or mismatched live snapshot must be visibly unavailable, regardless of the displayed historical model score.

### Q10

**Source:** `6 signaux.ipynb`, cell 1, source line 22.

> tags/Sharpe "indispo" si rien

**English translation:** tags/Sharpe unavailable if nothing is present

**Our display decision:** Missing readings become an explicit unavailable state, never a neutral numeric forecast. Actual code uses ? for a missing tag and NaN for absent metrics.

## What notebook 6 actually displays

The observed tag and predicted tag are different records. `read_graph_tags_t` reads the current observed graph state; `plot_ticker_last_year` merges that tag onto the historical price chart (cell 1, lines 213–237 and 411–437). `read_signal_tags` reads the stored future tag; `current_signal` returns the latest valid predicted tag for the table (lines 187–209 and 240–246). A compact CGB product should retain these two meanings even if it uses one small panel.

The table's entry marker is a further rule: selected buy/sell leg, predicted tag and one-year/ten-year price extension (lines 301–322). It is not the exported executable position. Its columns are ticker, tag, entry marker, extension and historical Sharpe/MaxDD (line 341). Those long-horizon extension rules should not silently become intraday CGB entry logic.

Missing or invalid predicted tags return `None`, displayed as `?`; missing summary metrics become NaN (lines 240–246 and 312–314). Missing regression data also produce NaN (lines 274–298). If every tag is missing, the display prints an explicit diagnostic (lines 353–354). If only one is missing, its row shows `?`. If observed state history is missing, the price chart remains available and no replacement graph state is calculated (lines 418–424).

There are three concrete gaps to repair in our display contract:

- `current_signal` chooses the last stored tag without checking its age. An old value can therefore remain a valid-looking latest tag. Our snapshot must carry an expiry/freshness status.
- The rendered table omits forecast origin, run identity and model version. Our compact view should expose the origin and horizon immediately and make provenance inspectable.
- The DB loader independently selects the latest successful universe run and prediction run (lines 78–102), with no displayed linkage check between them. Our consumer should require the inputs and forecast to belong to the intended compatible snapshot.

The notebook follows the read-only presentation principle: it reads model artifacts rather than recalculating the forecasting model. Presentation calculations such as regression extension and the entry screen still happen in the display. We should therefore specify which derived labels belong to the published model and which are presentation-only, then preserve that distinction in the saved reading.

## What one number cannot carry

A directional score formed as up probability minus down probability is useful for orientation, but it is not a probability of success. For example, an 80% up / 20% down forecast and a 60% up / 40% neutral forecast both produce a +60-point imbalance. They express different possibilities.

Zero is also ambiguous: 50% up / 50% down is very different from 100% neutral. A missing forecast must have its own unavailable status rather than displaying zero. Fresh contradictory evidence and missing observations should remain distinguishable even when neither produces a strong directional view.

The score also omits expected move size, adverse path, costs, horizon and the reliability of the information. A predicted endpoint decline can include a substantial adverse rally first. A one-hour bearish forecast and a four-hour bullish forecast can describe a coherent reversal path; the opposite signs do not automatically indicate an implementation error. Separate horizon models should not be presented as one coherent joint path unless that joint consistency has been established.

For the smallest useful display, keep **direction and selected horizon**, **up/down/neutral probabilities**, **a price-move interval or adverse-excursion reading**, and **freshness/availability** visible. Put observed state, reference relationship, conflicting evidence and versioned calibration in a short drill-down. This is our product design, derived from the source's separation of observed state, future forecast and operational contract.

## Best excerpts for the final explanation

Use **Q06 and Q07** together to explain the observed-state versus forecast distinction. Use **Q09** to justify freshness and snapshot consistency as part of correctness. Use **Q02** for grouping evidence by economic exposure, and **Q03** for separating inferred pressure from measured flow. Use **Q08** to explain why a useful diagnostic can inform a trader without changing positions. **Q05** supports the distinction between conflicting evidence and absent evidence, explicitly as our operational adaptation.

Avoid presenting the translations as new original quotations, or the proposed CGB layout as a private statement of the source author. No model result or source notebook was modified.
