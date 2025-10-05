from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional


def has_pdal() -> bool:
    return shutil.which("pdal") is not None


def build_ingest_pipeline(
    input_path: str,
    output_path: str,
    *,
    voxel_size: float,
    stddev_mult: float,
    mean_k: int,
    intensity_min: float,
    intensity_max: float,
    out_srs: Optional[str] | None = None,
) -> Dict:
    # Reader autodetect for common formats (E57/PLY/LAS/LAZ). Fallback to implicit reader via path string.
    reader_stage: str | Dict[str, str]
    lower = input_path.lower()
    if lower.endswith(".e57"):
        reader_stage = {"type": "readers.e57", "filename": input_path}
    elif lower.endswith(".ply"):
        reader_stage = {"type": "readers.ply", "filename": input_path}
    elif lower.endswith(".laz") or lower.endswith(".las"):
        reader_stage = input_path  # LAS/LAZ readers usually autodetected
    else:
        reader_stage = input_path

    stages = [
        reader_stage,
        {"type": "filters.statisticaloutlier", "mean_k": mean_k, "multiplier": stddev_mult},
        {"type": "filters.voxelgrid", "leaf_x": voxel_size, "leaf_y": voxel_size, "leaf_z": voxel_size},
        {"type": "filters.range", "limits": f"Intensity[{intensity_min}:{intensity_max}]"},
    ]
    if out_srs:
        stages.append({"type": "filters.reprojection", "out_srs": out_srs})
    stages.append({"type": "writers.las", "filename": output_path})
    return {"pipeline": stages}


def run_pipeline(pipeline: Dict) -> None:
    cmd = ["pdal", "pipeline", "--stdin"]
    subprocess.run(cmd, input=json.dumps(pipeline), text=True, check=True)


def get_point_count(file_path: str) -> Optional[int]:
    if not has_pdal():
        return None
    try:
        result = subprocess.run(
            ["pdal", "info", "--metadata", file_path], capture_output=True, text=True, check=True
        )
        meta = json.loads(result.stdout)
        readers = meta.get("metadata", {}).get("readers.las") or meta.get("metadata", {}).get("readers.laz")
        if isinstance(readers, dict):
            count = readers.get("count")
            if isinstance(count, int):
                return count
        return None
    except Exception:
        return None


