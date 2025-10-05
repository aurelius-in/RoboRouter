from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def write_decision(action: str, payload: Dict[str, Any]) -> None:  # type: ignore[type-arg]
    try:
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "action": action,
            **payload,
        }
        with open(log_dir / "decisions.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except Exception:
        # Best-effort; do not raise
        pass


