from __future__ import annotations

from pathlib import Path
from typing import Dict

import yaml


DEFAULTS: Dict[str, float] = {
    "rmse_max": 0.10,
    "miou_min": 0.70,
    "change_f1_min": 0.70,
}


def load_thresholds(path: str = "configs/thresholds.yaml") -> Dict[str, float]:
    p = Path(path)
    if not p.exists():
        return dict(DEFAULTS)
    try:
        data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        out: Dict[str, float] = dict(DEFAULTS)
        for k, v in (data or {}).items():
            try:
                out[str(k)] = float(v)
            except Exception:
                continue
        return out
    except Exception:
        return dict(DEFAULTS)


