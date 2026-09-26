# Component audit protocol — fixed before this run

This bounded Phase-A audit reuses the published S0 synthetic worlds 1729, 2718 and 3141. Their TEST results have already been inspected. These are retrospective diagnostic comparisons, not a fresh validation sample. No S0 inputs, fitted models, forecast thresholds or results will be changed. No order execution or new trading rule is included.

## E01: endpoint and path attribution

At 60 minutes reconstruct each saved local, future-state-conditioned and price-class-conditioned path expert, plus the original mixture. Verify reconstruction against saved TEST probabilities. Add one strong comparator with the same frozen price-class probabilities and uniform probability within each TRAIN endpoint class. This isolates local within-class weighting from directional classification.

Evaluate endpoint log loss/Brier, continuous endpoint CRPS, long and short maximum-adverse-excursion CRPS, 80% adverse-excursion pinball loss and endpoint 80% interval score. Scores use the same eligible origins. Quantities in tick units are reported in ticks. CRPS computations use exact finite-distribution sums, not Monte Carlo samples.

Fit one additional four-expert mixture on CAL only, minimizing the equally weighted mean of endpoint, long-adverse-excursion and short-adverse-excursion CRPS after dividing each origin by its observed volatility scale. Expert parameters and TRAIN paths remain frozen. This is a sum of proper marginal scores; it does not identify the full joint path law or first-passage timing. The original endpoint-loss mixture is preserved as its own comparator. No new hyperparameter or candidate selection will use TEST.

Primary descriptive comparison: price-class-conditioned local paths minus uniform-within-class paths in the three-marginal CRPS score. Secondary: CAL path-score mixture minus original mixture. Compute paired session-average differences and 95% session bootstrap intervals separately by seed. Eight TEST sessions per seed mean substantial uncertainty; overlapping forecast rows are not treated as independent trials. No architecture will be promoted automatically on this exploratory audit.

## E02: clock and restricted-information baselines

Fit the same fixed 100-tree, depth-two price classifier on the saved TRAIN origins using (a) minutes from open and minutes remaining, and (b) CGB midpoint-derived price features, volatility, price state and state age, excluding spread, book, flow, VWAP, cross-market information and explicit clock. Evaluate at the same saved TEST origins as the full frozen model. No tuning or refitting from TEST; model settings are copied from the frozen fit. CAL is not needed for these fixed classifiers and is left unused for them.

Report log loss and Brier against TRAIN class frequency for every 60/120/240-minute horizon. Also intersect TEST origin timestamps across horizons and recompute losses there. This separates sample eligibility from horizon differences; it cannot identify fixed-event-clock causality. Event-schedule jitter, new generator families, first-passage scoring and decision-policy experiments are explicitly deferred.

## Integrity and outputs

Save reproducible code, new fitted baseline heads, per-origin and per-session scores, paired intervals, plots, CAL weights and source hashes. Check finite probabilities, sum-to-one, exact saved-probability reconstruction within numerical tolerance, and CRPS against a direct small-matrix calculation. Hash all consumed source files before and after execution. Reports state both supportive and adverse findings.
