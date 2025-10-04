from __future__ import annotations

from typing import Any, Dict, Tuple
from ..utils.crs import allowed_crs


ALLOWED_EXPORT_TYPES = {"potree", "laz", "gltf", "webm"}


def evaluate_export_policy(policy_input: Dict[str, Any]) -> Tuple[bool, str]:
    """Lightweight policy gate mirroring OPA intent.

    Returns (allowed, reason). If disallowed, reason explains why.
    """
    export_type = str(policy_input.get("type", "")).lower()
    crs = str(policy_input.get("crs", "")).upper()

    if export_type not in ALLOWED_EXPORT_TYPES:
        return False, f"export type '{export_type}' is not allowed"
    if crs and crs not in allowed_crs():
        return False, f"CRS '{crs}' is not permitted"

    rounding_mm = policy_input.get("rounding_mm")
    if isinstance(rounding_mm, (int, float)) and rounding_mm < 0:
        return False, "negative rounding is not allowed"

    return True, "allowed by policy"


