from __future__ import annotations

import numpy as np


def binary_entropy(probability: np.ndarray) -> np.ndarray:
    """Compute binary entropy for probabilities p.

    Clips probabilities to avoid log(0).
    """
    eps = 1e-8
    p = np.clip(probability, eps, 1.0 - eps)
    return -(p * np.log(p) + (1.0 - p) * np.log(1.0 - p))


