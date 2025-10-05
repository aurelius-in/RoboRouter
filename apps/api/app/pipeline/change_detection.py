from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from ..config import settings
from ..utils.change import format_delta_table
from ..utils.tracing import span


logger = logging.getLogger(__name__)


def run_change_detection(baseline_path: str, current_path: str, out_dir: str) -> Dict[str, str | float]:
    """Voxel-diff change detection stub.

    Generates a tiny change mask summary and a delta table JSON.
    Returns file paths and stub precision/recall/F1 metrics.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    if settings.change_use_learned:
        with span("change_detection.learned_stub"):
            mask_stats = {"added": 30, "removed": 12, "moved": 7}
    else:
        with span("change_detection.stub"):
            # Stub: pretend we detected changes in 3 classes
            mask_stats = {"added": 42, "removed": 17, "moved": 5}
    change_mask_path = str(Path(out_dir) / "change_mask_summary.json")
    with open(change_mask_path, "w", encoding="utf-8") as f:
        json.dump({"mask_stats": mask_stats, "voxel_size_m": settings.change_voxel_size_m}, f)

    delta = format_delta_table(mask_stats)
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


