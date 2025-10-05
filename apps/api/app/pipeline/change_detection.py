from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from ..config import settings
from ..utils.change import format_delta_table
from ..utils.tracing import span


logger = logging.getLogger(__name__)


def run_change_detection(baseline_path: str, current_path: str, out_dir: str, pose_drift: float | None = None) -> Dict[str, str | float]:
    """Voxel-diff change detection stub.

    Generates a tiny change mask summary and a delta table JSON.
    Returns file paths and stub precision/recall/F1 metrics.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if settings.change_use_learned:
        with span("change_detection.learned_stub"):
            d = float(pose_drift if pose_drift is not None else settings.change_pose_drift_default)
            # Scale counts with drift for illustration
            base = {"added": 30, "removed": 12, "moved": 7}
            mask_stats = {k: int(v * (1.0 + d)) for k, v in base.items()}
    else:
        with span("change_detection.stub"):
            # Stub: pretend we detected changes in 3 classes
            mask_stats = {"added": 42, "removed": 17, "moved": 5}
    change_mask_path = str(Path(out_dir) / "change_mask_summary.json")
    with open(change_mask_path, "w", encoding="utf-8") as f:
        json.dump({"mask_stats": mask_stats, "voxel_size_m": settings.change_voxel_size_m}, f)

    delta = format_delta_table(mask_stats)
    # Class-wise deltas (stub): generate per-class added/removed counts
    try:
        import numpy as _np
        num_classes = int(getattr(settings, "seg_num_classes", 5))
        rng = _np.random.default_rng(42)
        by_class_added = {str(i): int(rng.integers(0, max(1, mask_stats.get("added", 0) // max(1, num_classes)))) for i in range(num_classes)}
        by_class_removed = {str(i): int(rng.integers(0, max(1, mask_stats.get("removed", 0) // max(1, num_classes)))) for i in range(num_classes)}
        delta["by_class"] = {"added": by_class_added, "removed": by_class_removed}
    except Exception:
        pass
    # Add simple drift metric (placeholder): magnitude proportional to moved count
    drift_metric = float(mask_stats.get("moved", 0)) / max(1.0, float(sum(mask_stats.values())))
    delta["drift"] = drift_metric
    delta_table_path = str(Path(out_dir) / "delta_table.json")
    with open(delta_table_path, "w", encoding="utf-8") as f:
        json.dump(delta, f)

    precision, recall = 0.80, 0.75
    f1 = 2 * precision * recall / (precision + recall)
    logger.info(
        "Change detection stub wrote overlays: mask=%s delta=%s | P=%.2f R=%.2f F1=%.2f",
        change_mask_path,
        delta_table_path,
        precision,
        recall,
        f1,
    )

    return {
        "change_mask_path": change_mask_path,
        "delta_table_path": delta_table_path,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "drift": drift_metric,
    }


