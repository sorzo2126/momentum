"""Reproduce this review's numerical findings from saved artifacts; never refit.

Run from any directory with Python's standard library. --write saves the audit
beside this script; without it, the results are printed only.
"""
from pathlib import Path
import argparse
import ast
import csv
import hashlib
import json
import math

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[1]


def rows(relative):
    with (STUDY / relative).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def clean_number(value):
    if value in ("", None):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    weights = rows("fitted-weights.csv")
    metrics = rows("metrics.csv")
    execution = rows("execution-summary.csv")
    source_files = {"fitted-weights.csv", "metrics.csv", "execution-summary.csv"}
    bases = []
    for seed in (1729, 2718, 3141):
        run = f"base-{seed}"
        w = next(r for r in weights if r["run"] == run and r["horizon_minutes"] == "60")
        m = next(r for r in metrics if r["run"] == run and r["horizon_minutes"] == "60")
        e = next(r for r in execution if r["run"] == run and r["horizon_minutes"] == "60" and r["strategy"] == "model")
        pair = {}
        for expert in ("mixture", "supervised"):
            name = f"results/{run}/frozen-model/pointwise_losses-60-{expert}.csv"
            source_files.add(name)
            pair[expert] = rows(name)
        a, b = pair["mixture"], pair["supervised"]
        assert len(a) == len(b) == int(m["scored"])
        assert [r["decision_time"] for r in a] == [r["decision_time"] for r in b]
        gaps = {column: max(abs(float(x[column]) - float(y[column])) for x, y in zip(a, b))
                for column in ("log_loss", "brier", "endpoint_abs_error_ticks")}
        assert abs(float(w["supervised_weight"]) - 1) < 1e-12
        assert gaps["log_loss"] < 1e-12 and gaps["brier"] < 1e-12
        bases.append({"run": run, "supervised_weight": float(w["supervised_weight"]),
                      "structural_weight": float(w["structural_weight"]),
                      "pointwise_mixture_supervised_max_abs_difference": gaps,
                      "log_loss_improvement": -float(m["loss_difference"]),
                      "saved_loss_difference_ci": [float(m["difference_ci_low"]), float(m["difference_ci_high"])],
                      "net_cad": float(e["net_cad"]), "higher_slippage_net_cad": float(e["stress_net_cad"]),
                      "trades": int(e["trades"]), "scored_forecasts": len(a)})
    selected = []
    for r in execution:
        if ((r["run"] == "fast_decay-1729" and r["horizon_minutes"] == "60" and r["strategy"] == "model")
            or (r["run"] == "base-2718" and r["horizon_minutes"] == "120" and r["strategy"] in ("model", "simple_momentum"))
            or (r["run"] == "cgb_only-1729" and r["horizon_minutes"] == "60" and r["strategy"] == "model")
            or (r["run"] == "feed_gaps-1729" and r["horizon_minutes"] == "60" and r["strategy"] == "model")):
            selected.append({**{k: r[k] for k in ("run", "horizon_minutes", "strategy", "accounting_status")},
                             **{k: clean_number(r[k]) for k in ("net_cad", "stress_net_cad", "trades", "unpriced_trades")}})
    assert len(selected) == 5, "Review selections no longer match the saved protocol."
    coverage = next(r for r in metrics if r["run"] == "base-2718" and r["horizon_minutes"] == "240")
    for p in ("model_snapshot/momentum/scenarios.py", "model_snapshot/momentum/states.py",
              "simulation/structured_simulation.py", "simulation/bond_ecosystem.py"):
        source_files.add(p)
    hashes = {p: hashlib.sha256((STUDY / p).read_bytes()).hexdigest() for p in sorted(source_files)}
    tree = ast.parse((STUDY / "simulation/structured_simulation.py").read_text(encoding="utf-8"))
    phi_assignments = [n.value for n in ast.walk(tree) if isinstance(n, ast.Assign)
                       and any(isinstance(t, ast.Name) and t.id == "phi" for t in n.targets)]
    assert len(phi_assignments) == 1 and isinstance(phi_assignments[0], ast.IfExp)
    values = {"fast_decay": ast.literal_eval(phi_assignments[0].body),
              "base": ast.literal_eval(phi_assignments[0].orelse)}
    driver = {name: {"phi_per_minute": phi, "half_life_minutes": math.log(.5)/math.log(phi),
                     "retained_initial_pressure_60_minutes": phi**60,
                     "cumulative_60_minute_fixed_loading_multiplier": phi*(1-phi**60)/(1-phi)}
              for name, phi in values.items()}
    result = {"status": "PASS", "scope": "Saved-artifact comparisons; no fitting, no new simulation, no source modification",
              "base_60_minutes": bases, "selected_execution_rows": selected,
              "pressure_driver_decay": driver,
              "pressure_driver_assumption": "Isolated initial pressure, no new nonzero-mean forcing; cumulative result assumes a fixed linear loading, not full ecosystem repricing.",
              "base_2718_240_minute_nominal_80_interval_coverage": float(coverage["interval_80_coverage"]),
              "directional_identity": "With all three endpoint classes present, sum of supervised path mass in class c equals the price head probability for c.",
              "nuance": "Local within-class paths still determine magnitude and excursions. State-derived features can still enter the price head.",
              "input_sha256": hashes}
    if args.write:
        (HERE / "saved-results-audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
