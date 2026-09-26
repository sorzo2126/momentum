"""Reproduce this study with its archived model, independently of future edits."""
from pathlib import Path
import sys

_snapshot = Path(__file__).resolve().parents[1] / "model_snapshot"
_loaded = sys.modules.get("momentum")
if _loaded is not None and Path(_loaded.__file__).resolve().parent != _snapshot / "momentum":
    raise RuntimeError("Start a fresh Python process: this study uses its archived momentum model.")
sys.path.insert(0, str(_snapshot))
