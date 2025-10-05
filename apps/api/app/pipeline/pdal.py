from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple


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


def get_bounds_and_srs(file_path: str) -> Tuple[Optional[Dict[str, float]], Optional[str]]:
    """Return (bounds, srs_wkt_or_name) using pdal info where possible.

    Bounds contains minx,miny,minz,maxx,maxy,maxz. SRS may be a WKT or EPSG string.
    """
    if not has_pdal():
        return None, None
    try:
        result = subprocess.run(
            ["pdal", "info", "--metadata", file_path], capture_output=True, text=True, check=True
        )
        meta = json.loads(result.stdout)
        md = meta.get("metadata", {}) if isinstance(meta, dict) else {}
        readers = md.get("readers.las") or md.get("readers.laz") or md.get("readers.ply") or md.get("readers.e57")
        bounds: Optional[Dict[str, float]] = None
        if isinstance(readers, dict):
            # PDAL often exposes bounds under 'bounds' or similar
            b = readers.get("bounds") or readers.get("minmax")
            if isinstance(b, dict):
                try:
                    bounds = {
                        "minx": float(b.get("minx")),
                        "miny": float(b.get("miny")),
                        "minz": float(b.get("minz", 0.0)),
                        "maxx": float(b.get("maxx")),
                        "maxy": float(b.get("maxy")),
                        "maxz": float(b.get("maxz", 0.0)),
                    }
                except Exception:
                    bounds = None
        # SRS parsing - PDAL may provide in 'srs' key
        srs = None
        srs_block = md.get("srs") if isinstance(md.get("srs"), dict) else (readers.get("comp_spatialreference") if isinstance(readers, dict) else None)  # type: ignore[assignment]
        if isinstance(srs_block, dict):
            # Try proj4 or wkt or horizontal name
            srs = srs_block.get("proj4") or srs_block.get("prettywkt") or srs_block.get("wkt") or srs_block.get("horizontal")
        elif isinstance(srs_block, str):
            srs = srs_block
        return bounds, srs
    except Exception:
        return None, None


