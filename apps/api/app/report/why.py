from __future__ import annotations

from typing import Dict, List


def top_reasons(metrics: Dict[str, float]) -> List[str]:
    reasons: List[str] = []
    rmse = metrics.get("rmse")
    if rmse is not None and rmse > 0.1:
        reasons.append(f"High residuals observed (RMSE={rmse:.3f}); consider re-running registration with robust settings.")
    miou = metrics.get("miou")
    if miou is not None and miou < 0.6:
        reasons.append(f"Low segmentation confidence (mIoU={miou:.2f}); try higher resolution or different checkpoint.")
    change_f1 = metrics.get("change_f1")
    if change_f1 is not None and change_f1 < 0.7:
        reasons.append(f"Change detection F1={change_f1:.2f} suggests noisy deltas; adjust voxel size or thresholds.")
    if not reasons:
        reasons.append("All key indicators within expected thresholds.")
    return reasons


