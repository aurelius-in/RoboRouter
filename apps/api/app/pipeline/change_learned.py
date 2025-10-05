from __future__ import annotations

from typing import Dict


def run_learned_change(baseline_path: str, current_path: str, *, pose_drift: float) -> Dict[str, int]:
    """Placeholder learned change detector.

    Returns class-agnostic mask stats scaled by pose_drift.
    """
    base = {"added": 30, "removed": 12, "moved": 7}
    factor = 1.0 + float(max(0.0, pose_drift))
    return {k: int(v * factor) for k, v in base.items()}


