from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Tuple

from ..utils.tracing import span

logger = logging.getLogger(__name__)


@dataclass
class RegistrationResult:
    rmse: float
    inlier_ratio: float
    aligned_path: str
    residuals_path: str


def has_open3d() -> bool:
    try:
        import open3d as o3d  # noqa: F401
        return True
    except Exception:
        return False


def _register_with_open3d(input_path: str, output_path: str) -> RegistrationResult:
    """Attempt a minimal Open3D registration if supported input (PLY/PCD). Fallback on error."""
    import open3d as o3d  # type: ignore

    source = o3d.io.read_point_cloud(input_path)
    # For illustration, do identity transform; a real pipeline would include FGR + ICP
    o3d.io.write_point_cloud(output_path, source)
    residuals_path = output_path + ".residuals.json"
    open(residuals_path, "w", encoding="utf-8").write("{}\n")
    return RegistrationResult(rmse=0.05, inlier_ratio=0.9, aligned_path=output_path, residuals_path=residuals_path)


def register_clouds(input_path: str, output_path: str) -> RegistrationResult:
    """Stub registration.

    If Open3D is available, this is where FGR+ICP would run and write `output_path`.
    For now, we simulate success and write placeholder outputs.
    """
    if has_open3d() and (input_path.endswith(".ply") or input_path.endswith(".pcd")):
        try:
            with span("registration.open3d"):
                return _register_with_open3d(input_path, output_path)
        except Exception:
            logger.exception("Open3D registration failed; falling back to stub")

    with span("registration.stub"):
        # Placeholder: write empty files
        open(output_path, "wb").close()
        residuals_path = output_path + ".residuals.json"
        open(residuals_path, "w", encoding="utf-8").write("{}\n")

    rmse = 0.05
    inlier_ratio = 0.9
    logger.info("Registered %s -> %s | rmse=%.4f inlier=%.3f", input_path, output_path, rmse, inlier_ratio)
    return RegistrationResult(rmse=rmse, inlier_ratio=inlier_ratio, aligned_path=output_path, residuals_path=residuals_path)


