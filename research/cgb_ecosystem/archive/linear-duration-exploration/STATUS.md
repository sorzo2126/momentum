# Superseded exploratory run

This incomplete first pass used linear duration mappings. During the experiment,
the user requested cash-flow bond pricing and a full CAD/US curve ecosystem. The
replacement experiment is [CGB ecosystem simulation](../../REPORT.md).

The first pass also exposed an evaluation edge case: with a recurring intraday
quote outage, every four-hour target can become unobservable. The scorer originally
attempted to average an empty table. The replacement records zero scored outcomes
and missing metrics instead of treating missing returns as zero or fabricating a
score. Forecasts remain in the journal. No predictive model parameters were tuned
in response to these results. Files here preserve the incomplete run's evidence.
