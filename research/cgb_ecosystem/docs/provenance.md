# Provenance and scope

This package consolidates the completed `reports/cgb-ecosystem-simulation` study and its `experiments` source from the Momentum repository. The initial `reports/structured-simulation` attempt is preserved under [archive/linear-duration-exploration](../archive/linear-duration-exploration/STATUS.md). Its incomplete linear-duration outputs are not included in the headline results of the replacement bond-cash-flow experiment.

The parent model source is from repository commit `a7d07563ee79fa7d7b951e0f49e312c42c14a375`. The eight files under [model_snapshot/momentum](../model_snapshot/momentum/) are byte-for-byte copies of the source used by the frozen fits. Each fit records its own source hashes. Keeping the snapshot here makes the study independent of subsequent edits to the live research package.

Packaging changed import locations, report links and output-directory selection. It changed the example-notebook verification to read the included reference copy. It did not change the simulator equations, learned model, forecasts, trade rules, saved raw histories or metric tables. The structural/accounting/replay checks were rerun after relocation.

The supplied example notebook is preserved unchanged at [reference/provided-example.ipynb](../reference/provided-example.ipynb). Its original source path remains in historical audit metadata as provenance only; it is not an execution dependency. The rerun arrays and documented objections are in [example-audit](../example-audit/). The delivered results notebook is a separate, executed reading notebook for this study. No notebook-generation script is included.

The [hypothesis document](hypotheses.md) and [interpretation](results-and-limitations.md) were assembled with knowledge of the saved results. They distinguish the intended mechanisms from observations and unresolved objections. They do not retroactively constitute preregistration or independent confirmation.

The [source register](../source-register.json) records the external research used for the qualitative market construction, with the scope of verification. The report's source section contains the corresponding links. None of those sources establishes that this uncalibrated generator matches observed intraday Canadian markets.

[manifest.json](../manifest.json) inventories published files by relative path, byte count and SHA-256. [file-index.csv](../file-index.csv) provides a tabular view. The two inventory files exclude themselves to avoid circular hashing; caches and installed dependencies are also excluded. The archived model is checked against every frozen deployment. A bundle checksum confirms file identity, not predictive validity.
