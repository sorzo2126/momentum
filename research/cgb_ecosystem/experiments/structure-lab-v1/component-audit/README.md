# Phase-A component audit

Start with [the report](report.md). The [protocol](protocol.md) was written before the new comparisons ran. [run_audit.py](run_audit.py) performs the bounded experiment, reads the frozen S0 data and deployment artifacts, and writes only into this directory.

Run from the study folder:

```powershell
python experiments/structure-lab-v1/component-audit/run_audit.py
python experiments/structure-lab-v1/component-audit/alignment_audit.py
```

The experiment uses the dependencies already recorded in the study. It preserves the original generator, fits, observations, forecasts and trading results. New baseline classifiers are in `fitted-baselines/`; the new calibration mixture weights are in `cal-path-mixture-weights.csv`.

`path-scores-per-origin.csv.gz` and `baseline-scores-per-origin.csv.gz` retain the scored observations. Session summaries and paired differences support the report and plots. `feature-columns.json` lists exactly what each baseline may observe. `verification.json` records reconstruction tolerances, source hashes and the execution timestamp.

The S0 TEST sample was consulted before this experiment was designed. These results diagnose the existing construction; they are not a new untouched validation claim. First-passage timing, changed event clocks, unseen generator families, real-data replay and trader-use validation remain separate work.

The separate [alignment protocol](alignment-protocol.md) and [alignment script](alignment_audit.py) partition existing one-hour forecasts and saved trades into continuation, opposing and balanced-origin cases. They do not add an alignment filter or simulate a new policy.
