"""CAD duration research: observations, forecasts, and separate accounting."""
from .features import ResearchConfig, FEATURE_MODULES, prepare_panel, build_features
from .model import make_targets, split_sessions, fit_research, latest_readings, predict_frozen
from .execution import futures_touch_benchmark, cash_bond_touch_benchmark
