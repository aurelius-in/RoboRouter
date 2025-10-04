from __future__ import annotations

import yaml
from pathlib import Path
from typing import Set

_CACHE: Set[str] | None = None


def allowed_crs() -> Set[str]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    cfg_path = Path("configs/crs_profiles.yaml")
    values: Set[str] = set()
    try:
        if cfg_path.exists():
            data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            for k, v in (data or {}).items():
                if isinstance(k, str):
                    values.add(k)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            values.add(item)
    except Exception:
        values = set()
    _CACHE = values or {"EPSG:3857", "EPSG:4978", "EPSG:26915"}
    return _CACHE


def validate_crs(crs: str) -> bool:
    if not isinstance(crs, str) or not crs.upper().startswith("EPSG:"):
        return False
    return crs in allowed_crs()


