from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict


def has_pdal() -> bool:
    return shutil.which("pdal") is not None


def build_ingest_pipeline(input_path: str, output_path: str, *, voxel_size: float, stddev_mult: float,
                          intensity_min: float, intensity_max: float) -> Dict:
    return {
        "pipeline": [
            input_path,
            {"type": "filters.statisticaloutlier", "mean_k": 8, "multiplier": stddev_mult},
            {"type": "filters.voxelgrid", "leaf_x": voxel_size, "leaf_y": voxel_size, "leaf_z": voxel_size},
            {"type": "filters.range", "limits": f"Intensity[{intensity_min}:{intensity_max}]"},
            {"type": "writers.las", "filename": output_path},
        ]
    }


def run_pipeline(pipeline: Dict) -> None:
    cmd = ["pdal", "pipeline", "--stdin"]
    subprocess.run(cmd, input=json.dumps(pipeline), text=True, check=True)


