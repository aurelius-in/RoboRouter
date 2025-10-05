from __future__ import annotations

from typing import Any, Dict, Tuple, Optional
from ..utils.crs import allowed_crs
from ..config import settings
import json
from pathlib import Path


def _load_policy() -> tuple[set[str], set[str], Optional[str], Optional[str]]:
    """Load dynamic policy from a JSON file if configured.

    Expected JSON schema (minimal):
      {
        "allowed_export_types": ["potree", "laz", "gltf", "webm"],
        "allowed_crs": ["EPSG:3857", ...]  // optional override
      }
    """
    default_types = {"potree", "laz", "gltf", "webm"}
    types = default_types
    crs_over = None
    path = settings.opa_policy_path
    version: Optional[str] = None
    policy_path_str: Optional[str] = None
    if path:
        p = Path(path)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    v = data.get("version")
                    if isinstance(v, (str, int, float)):
                        version = str(v)
                    t = data.get("allowed_export_types")
                    if isinstance(t, list):
                        types = {str(x).lower() for x in t}
                    c = data.get("allowed_crs")
                    if isinstance(c, list):
                        crs_over = {str(x).upper() for x in c}
                    policy_path_str = str(p)
            except Exception:
                # Try YAML as a fallback
                try:
                    import yaml  # type: ignore
                    data = yaml.safe_load(p.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        v = data.get("version")
                        if isinstance(v, (str, int, float)):
                            version = str(v)
                        t = data.get("allowed_export_types")
                        if isinstance(t, list):
                            types = {str(x).lower() for x in t}
                        c = data.get("allowed_crs")
                        if isinstance(c, list):
                            crs_over = {str(x).upper() for x in c}
                        policy_path_str = str(p)
                except Exception:
                    pass
    return types, (crs_over or set()), version, policy_path_str


def evaluate_export_policy(policy_input: Dict[str, Any]) -> Tuple[bool, str]:
    """Lightweight policy gate mirroring OPA intent.

    Returns (allowed, reason). If disallowed, reason explains why.
    """
    export_type = str(policy_input.get("type", "")).lower()
    crs = str(policy_input.get("crs", "")).upper()

    allowed_types, crs_override, _ = _load_policy()

    if export_type not in allowed_types:
        return False, f"export type '{export_type}' is not allowed"
    allowed_crs_set = crs_override or allowed_crs()
    if crs and crs not in allowed_crs_set:
        return False, f"CRS '{crs}' is not permitted"

    rounding_mm = policy_input.get("rounding_mm")
    if isinstance(rounding_mm, (int, float)) and rounding_mm < 0:
        return False, "negative rounding is not allowed"

    return True, "allowed by policy"


