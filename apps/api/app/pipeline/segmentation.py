from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

import numpy as np

from ..utils.math import binary_entropy
from ..config import settings
from ..utils.tracing import span


logger = logging.getLogger(__name__)


def run_segmentation(input_path: str, out_dir: str) -> Dict[str, str | float | int]:
    """CPU fallback segmentation stub.

    Generates small overlay summaries for classes, confidence and entropy.
    Returns paths of written artifacts and mIoU stub metric.
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    used_minkowski = 0
    used_cuda = 0
    if settings.seg_use_minkowski and settings.seg_model_path:
        with span("segmentation.minkowski_stub"):
            try:
                import torch  # type: ignore
                used_cuda = 1 if torch.cuda.is_available() else 0
                __import__("MinkowskiEngine")  # type: ignore
                used_minkowski = 1
            except Exception:
                used_minkowski = 0
            # Placeholder: treat as deterministic pseudo-preds when enabled
            rng = np.random.default_rng(123)
            num_points = 2000
            num_classes = int(getattr(settings, "seg_num_classes", 5))
            logits = rng.standard_normal((num_points, num_classes))
            probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
            classes = np.argmax(probs, axis=1)
            confidence = np.max(probs, axis=1)
            entropy = np.mean(binary_entropy(confidence))
    else:
        with span("segmentation.stub"):
        # Pretend we made predictions for N points
            num_points = 1000
            num_classes = int(getattr(settings, "seg_num_classes", 5))
            logits = np.random.randn(num_points, num_classes)
            probs = np.exp(logits) / np.sum(np.exp(logits), axis=1, keepdims=True)
            classes = np.argmax(probs, axis=1)
            confidence = np.max(probs, axis=1)
            entropy = np.mean(binary_entropy(confidence))  # approximate entropy from top-class prob

    # Summaries only (keep files tiny)
    class_counts = {int(c): int((classes == c).sum()) for c in range(num_classes)}
    confidence_mean = float(confidence.mean())

    classes_path = str(Path(out_dir) / "classes_summary.json")
    conf_path = str(Path(out_dir) / "confidence_summary.json")
    ent_path = str(Path(out_dir) / "entropy_summary.json")

    with open(classes_path, "w", encoding="utf-8") as f:
        json.dump({"class_counts": class_counts}, f)
    with open(conf_path, "w", encoding="utf-8") as f:
        json.dump({"confidence_mean": confidence_mean}, f)
    with open(ent_path, "w", encoding="utf-8") as f:
        json.dump({"entropy_mean": float(entropy)}, f)

    miou_stub = 0.75
    logger.info(
        "Segmentation stub wrote overlays: classes=%s confidence=%s entropy=%s | mIoU=%.3f",
        classes_path,
        conf_path,
        ent_path,
        miou_stub,
    )

    return {
        "classes_path": classes_path,
        "confidence_path": conf_path,
        "entropy_path": ent_path,
        "miou": miou_stub,
        "seg_used_minkowski": int(used_minkowski),
        "seg_used_cuda": int(used_cuda),
    }


