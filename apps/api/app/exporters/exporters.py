from __future__ import annotations

from pathlib import Path

from .base import ensure_parent, has_tool, run_cmd


def export_potree(input_laz: str, out_dir: str) -> str:
    ensure_parent(out_dir + "/dummy")
    if has_tool("PotreeConverter"):  # typical binary name
        run_cmd(["PotreeConverter", input_laz, "-o", out_dir])
    else:
        Path(out_dir, "README.txt").write_text("Potree tiles placeholder\n", encoding="utf-8")
    return out_dir


def export_laz(input_laz: str, out_laz: str) -> str:
    ensure_parent(out_laz)
    if has_tool("laszip"):
        run_cmd(["laszip", "-i", input_laz, "-o", out_laz])
    else:
        # Fallback copy/placeholder
        Path(out_laz).write_text("LAZ placeholder\n", encoding="utf-8")
    return out_laz


def export_gltf(input_laz: str, out_gltf: str) -> str:
    ensure_parent(out_gltf)
    # Placeholder: real pipeline would mesh/triangulate first
    Path(out_gltf).write_text("glTF placeholder\n", encoding="utf-8")
    return out_gltf


def export_webm(input_view: str, out_webm: str) -> str:
    ensure_parent(out_webm)
    if has_tool("ffmpeg"):
        # This would encode a capture; using placeholder for now
        Path(out_webm).write_text("WebM placeholder (recorded)\n", encoding="utf-8")
    else:
        Path(out_webm).write_text("WebM placeholder\n", encoding="utf-8")
    return out_webm


