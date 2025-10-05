from __future__ import annotations

from typing import Dict, Any


def has_minkowski() -> bool:
    try:
        __import__("MinkowskiEngine")  # type: ignore
        return True
    except Exception:
        return False


def load_kpconv_model(model_path: str) -> Any:  # type: ignore[override]
    # Placeholder: in a real impl, load state dict and architecture
    return {"model": "kpconv_stub", "path": model_path}


def run_kpconv_inference(_: Any, num_points: int, num_classes: int) -> Dict[str, Any]:  # type: ignore[type-arg]
    # Placeholder deterministic logits generator for reproducibility
    import numpy as _np
    rng = _np.random.default_rng(123)
    logits = rng.standard_normal((num_points, num_classes))
    probs = _np.exp(logits) / _np.sum(_np.exp(logits), axis=1, keepdims=True)
    classes = _np.argmax(probs, axis=1)
    confidence = _np.max(probs, axis=1)
    return {"classes": classes, "confidence": confidence}


