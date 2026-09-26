"""CAD research targets, causal dynamics, supervised heads, and held-out reporting.

This package version imports the same feature contract used in the notebook.
It does not load data, place orders, infer hidden institutional positions, or claim
that a physical analogy establishes a financial forecasting law.
"""
from .features import ResearchConfig, FEATURE_MODULES
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import logsumexp
from scipy.stats import norm


def make_targets(panel, features, cfg):
    """Future midpoint outcomes; every grid observation through expiry is required."""
    out = {}
    if panel is None or len(panel) == 0:
        return out
    for horizon in cfg.horizons_minutes:
        if horizon % cfg.grid_minutes:
            raise ValueError("Every horizon must be a multiple of grid_minutes.")
        n = horizon // cfg.grid_minutes
        y = pd.DataFrame(index=panel.index)
        for col in ("return_ticks", "mae_long_ticks", "mae_short_ticks", "class_id"):
            y[col] = np.nan
        y["target_end"] = pd.Series(pd.NaT, index=y.index, dtype="datetime64[ns, UTC]")
        y["neutral_band_ticks"] = cfg.neutral_band_sigma * features.sigma_ticks * np.sqrt(n)
        for _, group in panel.groupby("segment_id", sort=False):
            idx = group.index
            mid = group.cgb_mid.where(group.cgb_valid)
            future_min = mid.iloc[::-1].rolling(n + 1, min_periods=n + 1).min().iloc[::-1]
            future_max = mid.iloc[::-1].rolling(n + 1, min_periods=n + 1).max().iloc[::-1]
            last = mid.shift(-n)
            end = pd.Series(idx, index=idx).shift(-n)
            band = y.loc[idx, "neutral_band_ticks"]
            good = (future_min.notna() & last.notna() & band.notna()
                    & ((end - pd.Series(idx, index=idx)) == pd.Timedelta(minutes=horizon))
                    & (end <= group.session_close))
            ret = (last - mid) / cfg.tick_size
            y.loc[idx, "return_ticks"] = ret.where(good)
            y.loc[idx, "mae_long_ticks"] = ((mid - future_min) / cfg.tick_size).clip(lower=0).where(good)
            y.loc[idx, "mae_short_ticks"] = ((future_max - mid) / cfg.tick_size).clip(lower=0).where(good)
            cls = pd.Series(np.where(ret < -band, 0, np.where(ret > band, 2, 1)), index=idx)
            y.loc[idx, "class_id"] = cls.where(good)
            y.loc[idx, "target_end"] = end.where(good)
        out[int(horizon)] = y
    return out


def split_sessions(panel, cfg):
    """One chronological holdout; complete sessions plus explicit boundary embargo."""
    empty = pd.DatetimeIndex([], tz="UTC", name="decision_time")
    if panel is None or len(panel) == 0:
        return {"train": empty, "cal": empty, "test": empty, "metadata": {"status": "no_data"}}
    ordered = panel.groupby("session_id", sort=False).apply(
        lambda x: x.index.min(), include_groups=False).sort_values().index.tolist()
    need = cfg.min_train_sessions + cfg.min_cal_sessions + cfg.min_test_sessions
    if len(ordered) < need:
        return {"train": empty, "cal": empty, "test": empty,
                "metadata": {"status": "insufficient_history", "sessions": len(ordered), "required": need}}
    nt, nc = cfg.min_test_sessions, cfg.min_cal_sessions
    sessions = {"train": ordered[:-(nt + nc)], "cal": ordered[-(nt + nc):-nt], "test": ordered[-nt:]}
    splits = {name: panel.index[panel.session_id.isin(ids)] for name, ids in sessions.items()}
    removed, cutoffs = {}, {}
    for left, right in (("train", "cal"), ("cal", "test")):
        cutoff = splits[right].min() - pd.Timedelta(minutes=cfg.embargo_minutes)
        before = len(splits[left])
        splits[left] = splits[left][splits[left] < cutoff]
        removed[left], cutoffs[left] = before - len(splits[left]), str(cutoff)
    splits["metadata"] = {"status": "ready", "sessions": sessions,
                          "embargo_minutes": cfg.embargo_minutes,
                          "embargo_rows_removed": removed, "cutoffs": cutoffs,
                          "purge_rule": "A label's entire horizon must end inside its own retained partition."}
    return splits


def _session_weights(session_ids):
    """Each included session contributes equal total mass; no class rebalancing."""
    s = pd.Series(np.asarray(session_ids))
    weights = 1.0 / s.map(s.value_counts()).to_numpy(dtype=float)
    return weights / weights.sum() * len(weights)


@dataclass
class LocalDrift:
    phi: float
    q: float
    r: float
    optimizer_success: bool
    optimizer_message: str
    n_observations: int
    boundary_warning: bool


def _filter_drift(returns, segments, model):
    """Forward Kalman filter only. Missing returns reset state, never become zero."""
    means, variances = np.empty(len(returns)), np.empty(len(returns))
    innovation, innovation_var = np.full(len(returns), np.nan), np.full(len(returns), np.nan)
    mean, variance, previous = 0.0, 0.0, None
    for i, (value, segment) in enumerate(zip(returns, segments)):
        if previous is None or segment != previous:
            mean, variance = 0.0, model.q / max(1.0 - model.phi ** 2, 1e-6)
        else:
            mean, variance = model.phi * mean, model.phi ** 2 * variance + model.q
        if np.isfinite(value):
            residual, total = value - mean, variance + model.r
            gain = variance / total
            mean, variance = mean + gain * residual, (1.0 - gain) * variance
            innovation[i], innovation_var[i] = residual, total
        else:
            mean, variance = 0.0, model.q / max(1.0 - model.phi ** 2, 1e-6)
        means[i], variances[i], previous = mean, max(variance, 0.0), segment
    return means, variances, innovation, innovation_var


def fit_local_drift(panel_train):
    """Estimate phi,Q,R on training observations using equal-session Gaussian NLL."""
    returns = panel_train.cgb_ret_ticks.to_numpy(dtype=float)
    valid = np.isfinite(returns)
    if valid.sum() < 200:
        raise ValueError("At least 200 valid training returns are required for the dynamics expert.")
    scale = max(float(np.nanvar(returns)), 0.0625)
    weights = np.zeros(len(returns))
    weights[valid] = _session_weights(panel_train.session_id.to_numpy()[valid])
    segments = panel_train.segment_id.to_numpy()

    def objective(theta):
        model = LocalDrift(float(theta[0]), float(np.exp(theta[1])), float(np.exp(theta[2])), False, "", 0, False)
        _, _, error, variance = _filter_drift(returns, segments, model)
        losses = 0.5 * (np.log(2 * np.pi * variance[valid]) + error[valid] ** 2 / variance[valid])
        return float(np.average(losses, weights=weights[valid]))

    floor, ceiling = scale * 1e-6, scale * 100
    result = minimize(objective, [0.9, np.log(scale * .03), np.log(scale * .7)], method="L-BFGS-B",
                      bounds=[(0.0, .999), (np.log(floor), np.log(ceiling)), (np.log(floor), np.log(ceiling))],
                      options={"maxiter": 200, "ftol": 1e-9})
    phi, q, r = float(result.x[0]), float(np.exp(result.x[1])), float(np.exp(result.x[2]))
    if not result.success or not np.isfinite(result.fun):
        raise ValueError("Dynamics likelihood fit did not converge: " + str(result.message))
    boundary = phi < .001 or phi > .998 or min(q, r) <= floor * 1.1 or max(q, r) >= ceiling / 1.1
    return LocalDrift(phi, q, r, bool(result.success), str(result.message), int(valid.sum()), boundary)


def filter_local_drift(panel, model):
    means, variances, errors, noise = _filter_drift(panel.cgb_ret_ticks.to_numpy(dtype=float),
                                                  panel.segment_id.to_numpy(), model)
    return pd.DataFrame({"drift_mean": means, "drift_variance": variances,
                         "innovation": errors, "innovation_variance": noise}, index=panel.index)


def drift_terminal_moments(filtered, model, steps):
    """Distribution of sum r_(t+1)...r_(t+n), conditional on current filtered state."""
    powers = model.phi ** np.arange(1, steps + 1)
    initial_loading = float(powers.sum())
    shock_loadings = np.cumsum(model.phi ** np.arange(steps))
    variance = (initial_loading ** 2 * filtered.drift_variance.to_numpy()
                + model.q * np.dot(shock_loadings, shock_loadings) + steps * model.r)
    return initial_loading * filtered.drift_mean.to_numpy(), np.maximum(variance, 1e-12)


def _gaussian_classes(mean, std, band):
    down = norm.cdf((-band - mean) / std)
    up = norm.sf((band - mean) / std)
    return _normalize_probabilities(np.column_stack((down, np.maximum(1 - down - up, 0), up)))


def _normalize_probabilities(p):
    p = np.clip(np.asarray(p, dtype=float), 1e-9, 1)
    return p / p.sum(axis=1, keepdims=True)


def opinion_pool(p_ml, p_dynamics, weight, temperature):
    """Dependent conditional forecasts; convex log pool, not likelihood multiplication."""
    logits = (weight * np.log(_normalize_probabilities(p_ml))
              + (1 - weight) * np.log(_normalize_probabilities(p_dynamics))) / temperature
    return np.exp(logits - logsumexp(logits, axis=1, keepdims=True))


def fit_opinion_pool(p_ml, p_dynamics, classes, weights):
    classes = np.asarray(classes, dtype=int)

    def objective(theta):
        p = opinion_pool(p_ml, p_dynamics, theta[0], np.exp(theta[1]))
        return float(np.average(-np.log(p[np.arange(len(classes)), classes]), weights=weights))

    result = minimize(objective, [.5, 0.0], method="L-BFGS-B", bounds=[(0, 1), (np.log(.5), np.log(5))])
    if not result.success or not np.isfinite(result.fun):
        raise ValueError("Calibration optimization did not converge: " + str(result.message))
    return {"weight_ml": float(result.x[0]), "temperature": float(np.exp(result.x[1])),
            "calibration_nll": float(result.fun), "optimizer_success": bool(result.success)}


def phase_transition_diagnostic(panel, features, train_index, smoothing=.5):
    """Descriptive train-only transitions, with adjacent same-segment pairs only."""
    counts = np.zeros((7, 7), dtype=int)
    allowed = panel.index.isin(train_index)
    codes, segments = features.phase_code.to_numpy(), panel.segment_id.to_numpy()
    for i in range(1, len(panel)):
        if (allowed[i - 1] and allowed[i] and segments[i - 1] == segments[i]
                and 0 <= codes[i - 1] < 7 and 0 <= codes[i] < 7):
            counts[int(codes[i - 1]), int(codes[i])] += 1
    prior = counts + smoothing
    probability = prior / prior.sum(axis=1, keepdims=True)
    return {"counts": counts, "probability": probability, "smoothing": smoothing,
            "use": "description only; not a target or a constraint on future price direction"}


def _metrics(p, classes, returns, mean_prediction, session_ids):
    classes = np.asarray(classes, dtype=int)
    weights = _session_weights(session_ids)
    truth = np.eye(3)[classes]
    losses = -np.log(np.clip(p[np.arange(len(classes)), classes], 1e-9, 1))
    brier = np.sum((p - truth) ** 2, axis=1)
    absolute = np.abs(np.asarray(returns) - np.asarray(mean_prediction))
    rows = pd.DataFrame({"session_id": np.asarray(session_ids), "log_loss": losses,
                         "brier": brier, "endpoint_abs_error_ticks": absolute})
    if hasattr(returns, "index"):
        rows.index = returns.index
    per_session = rows.groupby("session_id").mean()
    confidence, prediction = p.max(axis=1), p.argmax(axis=1)
    reliability = pd.DataFrame({"confidence": confidence, "correct": prediction == classes,
                                "weight": weights, "bin": np.minimum((confidence * 5).astype(int), 4)})
    bins = []
    for bin_id, group in reliability.groupby("bin"):
        bins.append({"bin": int(bin_id), "rows": len(group),
                     "mean_confidence": float(np.average(group.confidence, weights=group.weight)),
                     "accuracy": float(np.average(group.correct, weights=group.weight))})
    return {"log_loss": float(np.average(losses, weights=weights)),
            "brier": float(np.average(brier, weights=weights)),
            "endpoint_mae_ticks": float(np.average(absolute, weights=weights)),
            "rows": len(classes), "sessions": len(per_session),
            "per_session": per_session, "pointwise_losses": rows, "reliability": pd.DataFrame(bins)}


def _feature_columns(features, cfg):
    if "cgb" not in cfg.feature_modules:
        raise ValueError("The cgb feature module is mandatory.")
    selected = []
    for module in cfg.feature_modules:
        if module not in FEATURE_MODULES:
            raise ValueError(f"Unknown feature module {module!r}; choose from {tuple(FEATURE_MODULES)}")
        selected.extend(FEATURE_MODULES[module])
    selected = list(dict.fromkeys(selected))
    missing = set(selected).difference(features.columns)
    if missing:
        raise ValueError(f"Missing constructed feature columns: {sorted(missing)}")
    return selected


def _label_indices(y, candidate, core_valid):
    idx = y.index.intersection(candidate)
    good = (y.loc[idx, "class_id"].notna() & y.loc[idx, "target_end"].isin(candidate)
            & core_valid.loc[idx])
    return idx[good]


def _module_coverage(panel, features, train_index, cfg):
    coverage = {}
    for name in cfg.feature_modules:
        cols = FEATURE_MODULES[name]
        complete = np.isfinite(features.loc[train_index, cols]).all(axis=1)
        usable = train_index[complete]
        coverage[name] = {"rows": len(usable), "sessions": panel.loc[usable, "session_id"].nunique()}
    return coverage


def fit_research(panel, features, targets, cfg):
    """Fit once on TRAIN, pool on CAL, report on TEST. No execution or auto-selection."""
    base = {"status": "no_data", "horizons": {}, "report": pd.DataFrame(), "splits": {}, "config": cfg}
    if panel is None or features is None or len(panel) == 0:
        return base
    splits = split_sessions(panel, cfg)
    base["splits"] = splits
    if splits["metadata"]["status"] != "ready":
        base.update(status="insufficient_history", reason=splits["metadata"])
        return base
    columns = _feature_columns(features, cfg)
    x = features[columns].replace([np.inf, -np.inf], np.nan)
    core = np.isfinite(x[FEATURE_MODULES["cgb"]]).all(axis=1) & panel.cgb_valid & (features.phase_code >= 0)
    coverage = _module_coverage(panel, features, splits["train"], cfg)
    base.update(feature_columns=columns, module_coverage=coverage)
    deficient = {name: value for name, value in coverage.items()
                 if value["sessions"] < cfg.min_train_sessions or value["rows"] < 100}
    if deficient:
        base.update(status="insufficient_history", reason={"module_training_coverage": deficient})
        return base
    try:
        from xgboost import XGBClassifier, XGBRegressor
    except ImportError:
        base.update(status="dependency_missing", reason="Install xgboost >= 2.0 for reg:quantileerror.")
        return base
    try:
        dynamics = fit_local_drift(panel.loc[splits["train"]])
    except ValueError as exc:
        base.update(status="dynamics_fit_failed", reason=str(exc))
        return base
    filtered = filter_local_drift(panel, dynamics)
    base.update(dynamics=dynamics, filtered_state=filtered, filter_history_start=panel.index[0],
                available_after=splits["cal"].max(),
                phase_transitions=phase_transition_diagnostic(panel, features, splits["train"]))
    settings = dict(n_estimators=100, max_depth=2, learning_rate=.03, min_child_weight=10,
                    subsample=1.0, colsample_bytree=1.0, reg_lambda=10.0,
                    tree_method="hist", device=cfg.xgb_device, random_state=cfg.random_state, n_jobs=2)
    reports = []
    for horizon in cfg.horizons_minutes:
        entry = {"status": "insufficient_history"}
        base["horizons"][int(horizon)] = entry
        if horizon not in targets:
            entry["reason"] = "Targets have not been constructed for this horizon."
            continue
        y = targets[horizon]
        used = {name: _label_indices(y, splits[name], core) for name in ("train", "cal", "test")}
        session_counts = {name: panel.loc[idx, "session_id"].nunique() for name, idx in used.items()}
        entry.update(indices=used, eligible_sessions=session_counts,
                     rows={name: len(idx) for name, idx in used.items()})
        minimum = {"train": cfg.min_train_sessions, "cal": cfg.min_cal_sessions, "test": cfg.min_test_sessions}
        if any(session_counts[name] < minimum[name] for name in minimum) or any(len(i) < 30 for i in used.values()):
            entry["reason"] = "Full-horizon valid outcomes do not cover the required sessions and at least 30 rows per partition."
            continue
        tr, ca, te = (used[name] for name in ("train", "cal", "test"))
        horizon_coverage = _module_coverage(panel, features, tr, cfg)
        entry["module_training_coverage"] = horizon_coverage
        if any(value["sessions"] < cfg.min_train_sessions or value["rows"] < 100 for value in horizon_coverage.values()):
            entry["reason"] = "An enabled module lacks training coverage on this horizon's eligible outcomes."
            continue
        if set(y.loc[tr, "class_id"].astype(int)) != {0, 1, 2}:
            entry.update(status="insufficient_outcome_coverage", reason="TRAIN must contain down, neutral, and up outcomes.")
            continue
        wt, wc = _session_weights(panel.loc[tr, "session_id"]), _session_weights(panel.loc[ca, "session_id"])
        clf = XGBClassifier(objective="multi:softprob", num_class=3, eval_metric="mlogloss", **settings)
        mean_model = XGBRegressor(objective="reg:squarederror", **settings)
        long_risk = XGBRegressor(objective="reg:quantileerror", quantile_alpha=.8, **settings)
        short_risk = XGBRegressor(objective="reg:quantileerror", quantile_alpha=.8, **settings)
        clf.fit(x.loc[tr], y.loc[tr, "class_id"].astype(int), sample_weight=wt)
        mean_model.fit(x.loc[tr], y.loc[tr, "return_ticks"], sample_weight=wt)
        long_risk.fit(x.loc[tr], y.loc[tr, "mae_long_ticks"], sample_weight=wt)
        short_risk.fit(x.loc[tr], y.loc[tr, "mae_short_ticks"], sample_weight=wt)
        eligible = panel.index[core]
        p_ml = pd.DataFrame(np.nan, index=panel.index, columns=["down", "neutral", "up"])
        p_ml.loc[eligible] = clf.predict_proba(x.loc[eligible])
        n = horizon // cfg.grid_minutes
        mean_dyn, variance_dyn = drift_terminal_moments(filtered, dynamics, n)
        band = cfg.neutral_band_sigma * features.sigma_ticks.to_numpy() * np.sqrt(n)
        p_dyn = pd.DataFrame(_gaussian_classes(mean_dyn, np.sqrt(variance_dyn), band), index=panel.index, columns=p_ml.columns)
        p_null = pd.DataFrame(_gaussian_classes(np.zeros(len(panel)), features.sigma_ticks.to_numpy() * np.sqrt(n), band),
                              index=panel.index, columns=p_ml.columns)
        try:
            pool = fit_opinion_pool(p_ml.loc[ca].to_numpy(), p_dyn.loc[ca].to_numpy(), y.loc[ca, "class_id"], wc)
        except ValueError as exc:
            entry.update(status="calibration_failed", reason=str(exc))
            continue
        p_final = pd.DataFrame(opinion_pool(p_ml.to_numpy(), p_dyn.to_numpy(), pool["weight_ml"], pool["temperature"]),
                               index=panel.index, columns=p_ml.columns)
        predictions = pd.DataFrame(index=panel.index)
        for name, probabilities in (("ml", p_ml), ("dynamics", p_dyn), ("pooled", p_final), ("zero_drift", p_null)):
            for j, cls in enumerate(("down", "neutral", "up")):
                predictions[f"{name}_p_{cls}"] = probabilities.iloc[:, j].where(core)
        predictions["endpoint_mean_ticks"] = np.nan
        predictions["mae_long_q80_ticks"] = np.nan
        predictions["mae_short_q80_ticks"] = np.nan
        predictions.loc[eligible, "endpoint_mean_ticks"] = mean_model.predict(x.loc[eligible])
        predictions.loc[eligible, "mae_long_q80_ticks"] = np.maximum(long_risk.predict(x.loc[eligible]), 0)
        predictions.loc[eligible, "mae_short_q80_ticks"] = np.maximum(short_risk.predict(x.loc[eligible]), 0)
        predictions["dynamics_mean_ticks"] = pd.Series(mean_dyn, index=panel.index).where(core)
        predictions["dynamics_std_ticks"] = pd.Series(np.sqrt(variance_dyn), index=panel.index).where(core)
        predictions["indicator"] = (p_final.up - p_final.down).where(core)
        predictions["predictive_entropy"] = (-(p_final * np.log(p_final)).sum(axis=1) / np.log(3)).where(core)
        midpoint = .5 * (p_ml + p_dyn)
        disagreement = .5 * ((p_ml * np.log(p_ml / midpoint)).sum(axis=1) + (p_dyn * np.log(p_dyn / midpoint)).sum(axis=1))
        predictions["expert_js_divergence"] = disagreement.where(core)
        optional = [col for col in columns if col not in FEATURE_MODULES["cgb"]]
        missing_optional = x[optional].isna().any(axis=1) if optional else pd.Series(False, index=x.index)
        predictions["data_status"] = np.where(~panel.cgb_valid, "invalid_current_quote",
            np.where(~core, "insufficient_core_history", np.where(missing_optional, "optional_inputs_missing", "available")))
        predictions["model_use"] = np.where(panel.index <= splits["train"].max(), "in_sample",
            np.where(panel.index <= splits["cal"].max(), "calibration_period", "held_out_or_later"))
        predictions["horizon_eligible_now"] = (panel.index + pd.Timedelta(minutes=horizon) <= panel.session_close)
        unavailable = ~predictions.horizon_eligible_now
        forecast_columns = [col for col in predictions if col not in ("data_status", "model_use", "horizon_eligible_now")]
        predictions.loc[unavailable, forecast_columns] = np.nan
        predictions.loc[unavailable & core, "data_status"] = "outside_session_horizon"
        # Predicting remains possible when the future outcome is not yet observed.
        sessions_test, classes_test = panel.loc[te, "session_id"], y.loc[te, "class_id"].astype(int)
        mean_ml_test = predictions.loc[te, "endpoint_mean_ticks"].to_numpy()
        prior_counts = np.bincount(y.loc[tr, "class_id"].astype(int), weights=wt, minlength=3) + .5
        prior = prior_counts / prior_counts.sum()
        prior_test = np.repeat(prior[None, :], len(te), axis=0)
        # A transparent direction-persistence benchmark with TRAIN-only conditional frequencies.
        past_direction = np.sign(features.mom_z_30).fillna(0).astype(int)
        persistence, persistence_mean = {}, {}
        for sign in (-1, 0, 1):
            mask = past_direction.loc[tr].to_numpy() == sign
            counts = np.bincount(y.loc[tr[mask], "class_id"].astype(int), weights=wt[mask], minlength=3) + .5
            persistence[sign] = counts / counts.sum()
            persistence_mean[sign] = float(np.average(y.loc[tr[mask], "return_ticks"], weights=wt[mask])) if mask.any() else 0.0
        persistence_test = np.array([persistence[int(sign)] for sign in past_direction.loc[te]])
        expert_pairs = {
            "zero_drift": (p_null.loc[te].to_numpy(), np.zeros(len(te))),
            "train_frequency": (prior_test, np.repeat(np.average(y.loc[tr, "return_ticks"], weights=wt), len(te))),
            "past_direction": (persistence_test, np.array([persistence_mean[int(sign)] for sign in past_direction.loc[te]])),
            "dynamics": (p_dyn.loc[te].to_numpy(), predictions.loc[te, "dynamics_mean_ticks"].to_numpy()),
            "ml": (p_ml.loc[te].to_numpy(), mean_ml_test),
            "pooled": (p_final.loc[te].to_numpy(), mean_ml_test),
        }
        metrics = {}
        for name, (probabilities, mean_prediction) in expert_pairs.items():
            metric = _metrics(probabilities, classes_test, y.loc[te, "return_ticks"], mean_prediction, sessions_test)
            metrics[name] = metric
            reports.append({"horizon_minutes": horizon, "expert": name,
                            **{key: metric[key] for key in ("log_loss", "brier", "endpoint_mae_ticks", "rows", "sessions")}})
        risk_report = {}
        for direction in ("long", "short"):
            actual = y.loc[te, f"mae_{direction}_ticks"].to_numpy()
            estimated = predictions.loc[te, f"mae_{direction}_q80_ticks"].to_numpy()
            residual = actual - estimated
            pinball = np.maximum(.8 * residual, -.2 * residual)
            weights_test = _session_weights(sessions_test)
            risk_report[direction] = {"pinball_q80": float(np.average(pinball, weights=weights_test)),
                                      "observed_q80_coverage": float(np.average(actual <= estimated, weights=weights_test))}
        entry.update(status="ready", models={"classifier": clf, "mean": mean_model, "mae_long_q80": long_risk,
                                             "mae_short_q80": short_risk}, pool=pool, predictions=predictions,
                     metrics=metrics, risk_metrics=risk_report, feature_columns=columns,
                     baseline_prior=prior, persistence_probabilities=persistence,
                     notes="Endpoint mean and path quantiles are separate ML heads, not moments of the pooled class probabilities.")
    base["report"] = pd.DataFrame(reports)
    ready = sum(item["status"] == "ready" for item in base["horizons"].values())
    base["status"] = "ready" if ready == len(cfg.horizons_minutes) else ("partial" if ready else "no_eligible_horizons")
    return base


def latest_readings(research):
    """Latest causal row from each fitted horizon; does not refit or need its label."""
    rows = []
    for horizon, fitted in research.get("horizons", {}).items():
        if fitted.get("status") != "ready":
            rows.append({"horizon_minutes": horizon, "status": fitted.get("status"), "reason": fitted.get("reason")})
            continue
        row = fitted["predictions"].iloc[-1].to_dict()
        unavailable = row["data_status"] in ("invalid_current_quote", "insufficient_core_history", "outside_session_horizon")
        row.update(horizon_minutes=horizon, decision_time=fitted["predictions"].index[-1],
                   status="forecast_unavailable" if unavailable else "research_forecast")
        rows.append(row)
    return pd.DataFrame(rows)


def predict_frozen(research, panel, features, cfg):
    """Replay known history through frozen models; return latest row at each horizon.

    Supply the complete prepared history beginning at filter_history_start, with
    newly received observations appended. Recompute causal features, not fitted
    parameters. A production incremental filter can replace this transparent replay.
    """
    if panel is None or len(panel) == 0 or "dynamics" not in research:
        return pd.DataFrame()
    if panel.index[0] != research["filter_history_start"]:
        raise ValueError("Frozen replay requires history beginning at the original filter_history_start.")
    if cfg != research["config"]:
        raise ValueError("Frozen inference must use the configuration used to train the model.")
    if panel.index[-1] <= research["available_after"]:
        raise ValueError("This fitted model was not available until its calibration outcomes were observed.")
    x = features[research["feature_columns"]].replace([np.inf, -np.inf], np.nan)
    last, now = panel.iloc[-1], panel.index[-1]
    core_good = (bool(last.cgb_valid) and bool(np.isfinite(x.iloc[-1][FEATURE_MODULES["cgb"]]).all())
                 and features.phase_code.iloc[-1] >= 0)
    filtered = filter_local_drift(panel, research["dynamics"]).iloc[[-1]]
    optional = [col for col in x if col not in FEATURE_MODULES["cgb"]]
    data_status = ("invalid_current_quote" if not last.cgb_valid else "insufficient_core_history" if not core_good
                   else "optional_inputs_missing" if x.iloc[-1][optional].isna().any() else "available")
    rows = []
    for horizon, fitted in research["horizons"].items():
        row = {"decision_time": now, "horizon_minutes": horizon, "data_status": data_status,
               "horizon_eligible_now": now + pd.Timedelta(minutes=horizon) <= last.session_close}
        if fitted["status"] != "ready" or not core_good or not row["horizon_eligible_now"]:
            row["status"] = fitted["status"] if fitted["status"] != "ready" else "forecast_unavailable"
            if not row["horizon_eligible_now"]:
                row["data_status"] = "outside_session_horizon"
            rows.append(row)
            continue
        models, pool = fitted["models"], fitted["pool"]
        mean, variance = drift_terminal_moments(filtered, research["dynamics"], horizon // cfg.grid_minutes)
        band = cfg.neutral_band_sigma * features.sigma_ticks.iloc[-1] * np.sqrt(horizon // cfg.grid_minutes)
        p_dyn = _gaussian_classes(mean, np.sqrt(variance), band)
        p_ml = models["classifier"].predict_proba(x.iloc[[-1]])
        p = opinion_pool(p_ml, p_dyn, pool["weight_ml"], pool["temperature"])[0]
        midpoint = .5 * (p_ml[0] + p_dyn[0])
        js = .5 * np.sum(p_ml[0] * np.log(p_ml[0] / midpoint) + p_dyn[0] * np.log(p_dyn[0] / midpoint))
        row.update(status="research_forecast", pooled_p_down=p[0], pooled_p_neutral=p[1], pooled_p_up=p[2],
                   indicator=p[2] - p[0], predictive_entropy=-np.dot(p, np.log(p)) / np.log(3), expert_js_divergence=js,
                   dynamics_mean_ticks=mean[0], dynamics_std_ticks=np.sqrt(variance[0]),
                   endpoint_mean_ticks=float(models["mean"].predict(x.iloc[[-1]])[0]),
                   mae_long_q80_ticks=max(float(models["mae_long_q80"].predict(x.iloc[[-1]])[0]), 0),
                   mae_short_q80_ticks=max(float(models["mae_short_q80"].predict(x.iloc[[-1]])[0]), 0))
        rows.append(row)
    return pd.DataFrame(rows)


def simulate_current_path(model, drift_mean, drift_variance, steps, draws=2000, seed=1729):
    """Conditional Gaussian paths in ticks, starting at zero; not observed market paths."""
    if steps < 1 or draws < 1 or drift_variance < 0:
        raise ValueError("steps/draws must be positive and variance nonnegative.")
    rng = np.random.default_rng(seed)
    state = rng.normal(drift_mean, np.sqrt(drift_variance), size=draws)
    paths = np.zeros((draws, steps + 1))
    for step in range(1, steps + 1):
        state = model.phi * state + rng.normal(0, np.sqrt(model.q), size=draws)
        paths[:, step] = paths[:, step - 1] + state + rng.normal(0, np.sqrt(model.r), size=draws)
    return paths
