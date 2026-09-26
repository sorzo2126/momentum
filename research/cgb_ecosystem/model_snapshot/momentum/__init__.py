"""CAD duration research: observations, forecasts, and separate accounting."""
from .features import ResearchConfig, FEATURE_MODULES, prepare_panel, build_features
from .model import make_targets, split_sessions, fit_research, latest_readings, predict_frozen
from .execution import futures_touch_benchmark, cash_bond_touch_benchmark
from .states import ScenarioConfig, build_state_observations
from .scenarios import fit_scenario_research, predict_scenarios, matured_feedback
from .deployment import save_deployment, load_deployment, save_live_reading, read_live_reading
