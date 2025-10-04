from __future__ import annotations

import os
from typing import Any, Dict


def log_params(params: Dict[str, Any]) -> None:
    if os.getenv("ROBOROUTER_MLFLOW", "false").lower() != "true":
        return
    try:
        import mlflow  # type: ignore

        for k, v in params.items():
            mlflow.log_param(k, v)
    except Exception:
        pass


def log_metrics(metrics: Dict[str, float]) -> None:
    if os.getenv("ROBOROUTER_MLFLOW", "false").lower() != "true":
        return
    try:
        import mlflow  # type: ignore

        mlflow.log_metrics(metrics)
    except Exception:
        pass


