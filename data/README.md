# Market inputs remain empty

Populate the notebook's QUOTES, RATES, SESSIONS, TRADES, CONTEXT and AS_OF cells using your actual feed adapters. Only QUOTES, SESSIONS and AS_OF are mandatory for the CGB baseline. Optional modules require actual history; missing measurements are not neutral readings.

See [the measurement contract](../docs/05-feature-contract.md) for exact columns, units, logical instrument aliases, available-at timestamps, revisions, contract boundaries and freshness. Every session has an explicit allowed close. AS_OF is the actual decision cutoff, not the last received quote's timestamp.

Do not replace receipt times with exchange times without justification. Do not feed a continuous adjusted futures price as though it were one executable contract. Do not manufacture bid/ask values for scalar SPX or VIX observations. Use the scalar context adapter instead.
