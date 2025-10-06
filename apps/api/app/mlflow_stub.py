from __future__ import annotations

import os
from typing import Any, Dict
from .config import settings


def log_params(params: Dict[str, Any]) -> None:
    enabled_env = os.getenv("ROBOROUTER_MLFLOW", "false").lower() == "true"
    enabled_cfg = bool(getattr(settings, "mlflow_enabled", False))
    if not (enabled_env or enabled_cfg):
        return
    try:
        import mlflow  # type: ignore
        if getattr(settings, "mlflow_tracking_uri", None):
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        for k, v in params.items():
            mlflow.log_param(k, v)
    except Exception:
        pass


def log_metrics(metrics: Dict[str, float]) -> None:
    enabled_env = os.getenv("ROBOROUTER_MLFLOW", "false").lower() == "true"
    enabled_cfg = bool(getattr(settings, "mlflow_enabled", False))
    if not (enabled_env or enabled_cfg):
        return
    try:
        import mlflow  # type: ignore
        if getattr(settings, "mlflow_tracking_uri", None):
            mlflow.set_tracking_uri(settings.mlflow_tracking_uri)
        mlflow.log_metrics(metrics)
    except Exception:
        pass


