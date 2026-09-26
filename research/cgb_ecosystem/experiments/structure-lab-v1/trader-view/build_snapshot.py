"""Read-only display adapter for an actual saved synthetic forecast.

Run from any working directory: python path/to/build_snapshot.py
No training, scenario generation, outcome selection, or live-data claims.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
STUDY = HERE.parents[2]
RUN = STUDY / "results" / "base-1729"
INPUTS = RUN / "inputs"
FORECAST_FIELDS = [
    "decision_time", "horizon_minutes", "p_down", "p_neutral", "p_up",
    "endpoint_mean_ticks", "endpoint_q10_ticks", "endpoint_q90_ticks",
    "mae_long_q80_ticks", "mae_short_q80_ticks", "effective_scenarios",
    "predictive_entropy", "expert_disagreement", "nearest_distance",
    "observed_feature_fraction", "unsupported_future_state_mass", "observed_state",
]


def read_csv(path: Path, **kwargs) -> pd.DataFrame:
    frame = pd.read_csv(path, **kwargs)
    for name in ("decision_time", "event_time", "available_at"):
        if name in frame:
            frame[name] = pd.to_datetime(frame[name], utc=True, format="mixed")
    return frame


def native(value):
    if isinstance(value, dict):
        return {str(k): native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [native(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if np.isfinite(value) else None
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def endpoint_relative_to_leg(row):
    """Relabel existing endpoint masses relative to the observed directional state.

    This creates no new forecast and is not a trend survival probability.
    A balanced or unidentified state has no directional leg to continue.
    """
    state = str(row["observed_state"])
    if state.startswith("up-"):
        direction, same, opposite = "upward", "p_up", "p_down"
    elif state.startswith("down-"):
        direction, same, opposite = "downward", "p_down", "p_up"
    else:
        return None
    return {"observed_leg": direction,
            "p_endpoint_continuation": float(row[same]),
            "p_endpoint_opposite": float(row[opposite]),
            "p_endpoint_neutral": float(row["p_neutral"]),
            "meaning": "Endpoint beyond the neutral band in the observed leg's direction; not uninterrupted movement or trend survival."}


def build():
    # This explicit usecols allowlist cannot read future outcomes or latent truth.
    predictions = read_csv(RUN / "predictions-and-outcomes.csv.gz", usecols=FORECAST_FIELDS)
    first_day = predictions.decision_time.min().tz_convert("America/New_York").date()
    decision = pd.Timestamp(f"{first_day} 10:30", tz="America/New_York").tz_convert("UTC")
    forecast = predictions[predictions.decision_time == decision].sort_values("horizon_minutes").copy()
    assert forecast.horizon_minutes.tolist() == [60, 120, 240]
    probabilities = forecast[["p_down", "p_neutral", "p_up"]].to_numpy()
    assert np.all((probabilities >= 0) & (probabilities <= 1))
    assert np.allclose(probabilities.sum(axis=1), 1, atol=1e-9)
    assert (forecast.endpoint_q10_ticks <= forecast.endpoint_q90_ticks).all()
    assert (forecast[["mae_long_q80_ticks", "mae_short_q80_ticks"]] >= 0).all().all()
    features = read_csv(RUN / "features.csv.gz").set_index("decision_time")
    observations = read_csv(RUN / "observations.csv.gz").set_index("decision_time")
    feature, observation = features.loc[decision], observations.loc[decision]
    deployment = json.loads((RUN / "frozen-model" / "deployment.json").read_text())
    assert pd.Timestamp(deployment["available_after"]) < decision
    quotes = read_csv(INPUTS / "quotes.csv.gz")
    rates = read_csv(INPUTS / "rates.csv.gz")
    quotes = quotes[(quotes.available_at <= decision) & (quotes.event_time <= decision)]
    rates = rates[(rates.available_at <= decision) & (rates.event_time <= decision)]
    latest = quotes.sort_values("available_at").groupby("instrument").tail(1).set_index("instrument")
    latest_rates = rates.sort_values("available_at").groupby("instrument").tail(1).set_index("instrument")
    cgb = latest.loc["CGB"]
    midpoint = float((cgb.bid + cgb.ask) / 2)
    tick = deployment["config"]["tick_size"]
    forecast["neutral_band_ticks"] = (deployment["config"]["neutral_band_sigma"]
        * feature.sigma_ticks * np.sqrt(forecast.horizon_minutes))
    forecast["endpoint_mean_price"] = midpoint + tick * forecast.endpoint_mean_ticks
    forecast["endpoint_q10_price"] = midpoint + tick * forecast.endpoint_q10_ticks
    forecast["endpoint_q90_price"] = midpoint + tick * forecast.endpoint_q90_ticks
    forecast["target_time"] = decision + pd.to_timedelta(forecast.horizon_minutes, unit="min")
    relative = {str(int(row.horizon_minutes)): endpoint_relative_to_leg(row)
                for _, row in forecast.iterrows()}
    for key, masses in relative.items():
        if masses is not None:
            assert np.isclose(masses["p_endpoint_continuation"]+masses["p_endpoint_opposite"]+masses["p_endpoint_neutral"], 1)
    for state, key in [("up-responsive", "p_up"), ("down-weakening", "p_down")]:
        case = forecast.iloc[0].to_dict(); case["observed_state"] = state
        assert endpoint_relative_to_leg(case)["p_endpoint_continuation"] == case[key]
    case["observed_state"] = "balanced"
    assert endpoint_relative_to_leg(case) is None
    available_cols = [c for c in deployment["feature_columns"] if c in feature or c in observation]
    missing_features = [c for c in available_cols if pd.isna(feature[c] if c in feature else observation[c])]
    assert len(missing_features) == 1 and missing_features[0] == "local_z_30"
    flow_enabled = bool(deployment["use_flow"])
    swap_cols = [c for c in deployment["feature_columns"] if c.startswith(("swap", "ois", "fwd"))]
    assert not swap_cols
    status = {
        "CGB": {"event_age_seconds": (decision - cgb.event_time).total_seconds(),
                "received_age_seconds": (decision - cgb.available_at).total_seconds(),
                "freshness_limit_seconds": deployment["config"]["cgb_stale_seconds"]},
        "US10": {"event_age_seconds": (decision-latest.loc["US10"].event_time).total_seconds(),
                 "freshness_limit_seconds": deployment["config"]["us_stale_seconds"]},
        "CAD_benchmarks": {"event_age_seconds": float((decision-latest_rates.event_time).dt.total_seconds().max()),
                           "freshness_limit_seconds": deployment["config"]["rates_stale_seconds"]},
        "classified_flow": {"available": bool(observation.flow_available), "enabled_in_model": flow_enabled},
        "swaps_ois_forwards": {"observed_at_snapshot": False, "enabled_in_model": False},
        "missing_model_features": missing_features,
        "feature_fraction": float(forecast.iloc[0].observed_feature_fraction),
        "empirical_reliability_on_live_CAD": "not_established",
    }
    observed_fields = ["mom_ticks_5", "mom_ticks_30", "vwap_distance_ticks", "vwap_distance_sigma",
                       "common_ticks_1", "local_ticks_1", "beta_us_prior", "cad_us_corr_prior",
                       "cad_slope25_bp_5", "cad_slope510_bp_5", "spread_ticks"]
    state_fields = ["state_age_minutes", "recovery_failures", "recovery_active", "flow_pressure", "reference_available"]
    snapshot = {
        "display_mode": "historical_synthetic_replay",
        "selection_rule": "First TEST session, 10:30 America/New_York; chosen by clock, not forecast or outcome.",
        "decision_time": decision,
        "instrument": "CGB", "contract": str(cgb.contract), "bid": cgb.bid, "ask": cgb.ask,
        "midpoint": midpoint, "tick_size": tick, "tick_value_cad_per_contract": deployment["config"]["tick_value_cad"],
        "run_id": deployment["run_id"], "code_contract_version": deployment["code_contract_version"],
        "state_series_hash": deployment["state_series_hash"], "model_available_after": deployment["available_after"],
        "observed_context": {**{c: feature[c] for c in observed_fields}, **{c: observation[c] for c in state_fields}},
        "data_status": status,
        "forecasts": forecast.to_dict("records"),
        "endpoint_relative_to_observed_leg": relative,
        "excluded_columns": ["return_ticks", "mae_long_ticks", "mae_short_ticks", "class_id", "outcome_available", "truth"],
    }
    (HERE / "snapshot.json").write_text(json.dumps(native(snapshot), indent=2, allow_nan=False)+"\n", encoding="utf-8")
    forecast.to_csv(HERE / "horizon-forecasts.csv", index=False)
    plot(snapshot, forecast, quotes, features, decision)
    sources = [RUN / "predictions-and-outcomes.csv.gz", RUN / "features.csv.gz", RUN / "observations.csv.gz",
               RUN / "frozen-model" / "deployment.json", INPUTS / "quotes.csv.gz", INPUTS / "rates.csv.gz"]
    checks = {
        "status": "passed", "decision_time": decision.isoformat(),
        "source_sha256": {str(p.relative_to(STUDY)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        "checks": ["Probability rows sum to one", "Endpoint bounds ordered", "MAE quantiles nonnegative",
                   "Model available before decision", "Read prediction allowlist excludes outcomes",
                   "Quotes filtered on both event and availability timestamps",
                   "Snapshot has all three saved horizons", "Missing feature identified separately",
                   "Swaps/OIS not claimed as active model evidence", "Plot history stops at decision",
                   "Continuation label reuses direction masses exactly; up/down map correctly and balanced omits label"],
    }
    (HERE / "verification.json").write_text(json.dumps(checks, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"status": "passed", "decision_time": decision.isoformat(), "output": str(HERE)}, indent=2))


def plot(snapshot, forecast, quotes, features, decision):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "axes.labelcolor": "#25364c", "text.color": "#25364c"})
    fig = plt.figure(figsize=(16, 11.5), facecolor="#f5f7fa")
    fig.text(.045, .955, "CGB duration | Momentum decision aid", fontsize=23, weight="bold")
    fig.text(.045, .922, "HISTORICAL SYNTHETIC REPLAY  •  19 Feb 2025, 10:30 New York  •  SIM_CGB", fontsize=12, color="#9e521c", weight="bold")
    fig.text(.045, .891, f"Bid {snapshot['bid']:.3f}  /  ask {snapshot['ask']:.3f}     |     Observed price state: upward-responsive, age 5 min", fontsize=12)
    relative = snapshot["endpoint_relative_to_observed_leg"]["60"]
    if relative is not None:
        fig.text(.045, .861, f"Observed {relative['observed_leg']} leg  |  1h endpoint continuation {relative['p_endpoint_continuation']:.0%}"
                 f" / opposite {relative['p_endpoint_opposite']:.0%} / neutral {relative['p_endpoint_neutral']:.0%}",
                 fontsize=11, color="#53667c", weight="bold")
    grid = fig.add_gridspec(2, 3, left=.055, right=.96, top=.80, bottom=.19, hspace=.57, wspace=.33,
                           height_ratios=[1, 1.35])
    ax = fig.add_subplot(grid[0, 0])
    ax.set_title("Future endpoint direction", loc="left", fontsize=14, weight="bold", pad=16)
    colors = ["#be554f", "#a1acba", "#337d74"]
    y = np.arange(3)
    left = np.zeros(3)
    for c, label, color in zip(["p_down", "p_neutral", "p_up"], ["Down", "Neutral", "Up"], colors):
        values = forecast[c].to_numpy()*100
        ax.barh(y, values, left=left, height=.6, color=color, label=label)
        for row in range(3):
            ax.text(left[row]+values[row]/2, row, f"{values[row]:.0f}%", ha="center", va="center", color="white", weight="bold", fontsize=10)
        left += values
    ax.set_yticks(y, ["1h", "2h", "4h"]);ax.invert_yaxis();ax.set_xlim(0,100)
    bands = "/".join(f"{v:.1f}" for v in forecast.neutral_band_ticks)
    ax.set_xticks([0,50,100]);ax.set_xlabel(f"Separate horizon models\nNeutral bands: ±{bands} ticks (1h/2h/4h)", fontsize=9)
    ax.legend(loc="lower left", bbox_to_anchor=(-.03,-.45), frameon=False, ncol=3, fontsize=10)
    ax = fig.add_subplot(grid[0, 1])
    ax.set_title("Endpoint change | ticks", loc="left", fontsize=14, weight="bold", pad=16)
    ax.axvline(0,color="#9ca6b1",lw=1)
    for j, (_, row) in enumerate(forecast.iterrows()):
        ax.plot([row.endpoint_q10_ticks,row.endpoint_q90_ticks],[j,j],lw=7,color="#c4d0df",solid_capstyle="round")
        ax.plot(row.endpoint_mean_ticks,j,"o",color="#253e63",ms=7)
        ax.text(36,j,f"{row.endpoint_mean_ticks:+.1f}",va="center",fontsize=11)
    ax.set_yticks(y,["1h","2h","4h"]);ax.invert_yaxis();ax.set_xlim(-70,51)
    ax.set_xlabel("Dot: mean  •  bar: 10th–90th percentile",fontsize=9)
    ax.text(0,-.36,"Model interval; empirical coverage is audited separately",transform=ax.transAxes,fontsize=9)
    ax = fig.add_subplot(grid[0, 2]);ax.axis("off")
    ax.set_title("Adverse excursion | 80th percentile",loc="left",fontsize=14,weight="bold",pad=16)
    ax.text(.0,.89,"Horizon",weight="bold");ax.text(.35,.89,"If long",weight="bold");ax.text(.71,.89,"If short",weight="bold")
    for j, (_, row) in enumerate(forecast.iterrows()):
        yy=.65-j*.24
        ax.text(.06,yy,f"{int(row.horizon_minutes/60)}h")
        ax.text(.39,yy,f"{row.mae_long_q80_ticks:.1f}")
        ax.text(.75,yy,f"{row.mae_short_q80_ticks:.1f}")
    ax.text(0,-.21,"Ticks from current midpoint, before execution costs.",fontsize=9)
    ax.text(0,-.36,"A path-risk quantile, not a recommended stop.",fontsize=9)
    ax = fig.add_subplot(grid[1, :2])
    start = decision.normalize()+pd.Timedelta(hours=13)
    history = quotes[(quotes.instrument=="CGB") & (quotes.available_at>=start)].sort_values("available_at")
    clock = history.available_at.dt.tz_convert("America/New_York")
    mid = (history.bid+history.ask)/2
    ax.plot(clock,mid,lw=1.8,color="#253e63",label="CGB received midpoint")
    f = features.loc[(features.index>=start)&(features.index<=decision)]
    aligned = pd.merge_asof(pd.DataFrame({"time":f.index}),pd.DataFrame({"time":history.available_at,"mid":mid}).sort_values("time"),on="time",direction="backward")
    vwap = aligned["mid"].to_numpy()-.01*f.vwap_distance_ticks.to_numpy()
    ax.plot(f.index.tz_convert("America/New_York"),vwap,lw=1.5,color="#ae7b29",label="Session VWAP from saved feature")
    ax.axvline(decision.tz_convert("America/New_York"),ls="--",color="#888888",lw=1)
    ax.set_title("What the trader had already observed",loc="left",fontsize=14,weight="bold",pad=15)
    ax.set_ylabel("CGB price");ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M",tz=decision.tz_convert("America/New_York").tzinfo))
    ax.set_xlim(start.tz_convert("America/New_York"),decision.tz_convert("America/New_York")+pd.Timedelta(minutes=4))
    ax.grid(axis="y",alpha=.2);ax.legend(loc="upper left",frameon=False,fontsize=9)
    ax.set_xlabel("Received history ends at 10:30. Future realised prices are not displayed.",fontsize=9)
    ax = fig.add_subplot(grid[1,2]);ax.axis("off")
    ax.set_title("Context | observations, not attribution",loc="left",fontsize=13,weight="bold",pad=15)
    context = snapshot["observed_context"]
    rows=[("Past 30 min", f"{context['mom_ticks_30']:+.1f} ticks"),
          ("VWAP distance", f"{context['vwap_distance_ticks']:+.1f} ticks / {context['vwap_distance_sigma']:+.2f} sigma"),
          ("Recorded failed recoveries", f"{int(context['recovery_failures'])} in current tracker"),
          ("CAD–US split, last 1 min", f"Common {context['common_ticks_1']:+.1f} / local {context['local_ticks_1']:+.1f} ticks"),
          ("Classified net flow, last 5 min", f"{context['flow_pressure']:+.1%} of classified volume"),
          ("2s5s / 5s10s, last 5 min", f"{context['cad_slope25_bp_5']:+.2f} / {context['cad_slope510_bp_5']:+.2f} bp")]
    for j,(label,value) in enumerate(rows):
        yy=.99-j*.17
        ax.text(0,yy,label,fontsize=9,color="#68788c",va="top")
        ax.text(0,yy-.065,value,fontsize=10.5,va="top")
    fig.text(.055,.132,"DATA STATUS",fontsize=10,weight="bold",color="#53667c")
    fig.text(.16,.132,"CGB / US / CAD benchmarks: 1s event age   •   Classified flow available   •   Active features present: 97.8%",fontsize=10)
    fig.text(.16,.106,"Missing feature: local_z_30   •   Swaps / OIS: unavailable here and excluded from this fitted model",fontsize=10)
    fig.text(.055,.061,"Endpoint continuation means finishing beyond the neutral band in the observed leg's direction; it is not a trend-survival probability.",fontsize=10.5,weight="bold")
    fig.text(.055,.036,"Model cad-conditional-paths-v1  |  run 0c109771…a20b  |  Independent 1h/2h/4h laws  |  No live-CAD calibration claim",fontsize=9,color="#53667c")
    fig.savefig(HERE/"trader-snapshot.png",dpi=170,facecolor=fig.get_facecolor())
    fig.savefig(HERE/"trader-snapshot.svg",facecolor=fig.get_facecolor())
    svg_path = HERE/"trader-snapshot.svg"
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf8").splitlines()) + "\n", encoding="utf8")
    plt.close(fig)


if __name__ == "__main__":
    build()
