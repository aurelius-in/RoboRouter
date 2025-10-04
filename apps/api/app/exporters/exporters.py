from __future__ import annotations

from pathlib import Path

from .base import ensure_parent, has_tool, run_cmd


def export_potree(input_laz: str, out_dir: str) -> str:
    ensure_parent(out_dir + "/dummy")
    try:
        if not (input_laz.endswith(".laz") or input_laz.endswith(".las")):
            raise ValueError("potree export expects LAS/LAZ input")
        if has_tool("PotreeConverter"):  # typical binary name
            run_cmd(["PotreeConverter", input_laz, "-o", out_dir])
        else:
            Path(out_dir, "README.txt").write_text("Potree tiles placeholder\n", encoding="utf-8")
    except Exception:
        # Fallback placeholder on any failure
        Path(out_dir, "ERROR.txt").write_text("Potree export failed; placeholder created\n", encoding="utf-8")
    return out_dir


def export_laz(input_laz: str, out_laz: str) -> str:
    ensure_parent(out_laz)
    try:
        if not (input_laz.endswith(".laz") or input_laz.endswith(".las")):
            raise ValueError("laz export expects LAS/LAZ input")
        if has_tool("laszip"):
            run_cmd(["laszip", "-i", input_laz, "-o", out_laz])
        else:
            Path(out_laz).write_text("LAZ placeholder (no laszip)\n", encoding="utf-8")
    except Exception:
        Path(out_laz).write_text("LAZ export failed; placeholder\n", encoding="utf-8")
    return out_laz


def export_gltf(input_laz: str, out_gltf: str) -> str:
    ensure_parent(out_gltf)
    # Placeholder: real pipeline would mesh/triangulate first
    try:
        Path(out_gltf).write_text("glTF placeholder\n", encoding="utf-8")
    except Exception:
        Path(out_gltf).write_text("glTF export failed; placeholder\n", encoding="utf-8")
    return out_gltf


def export_webm(input_view: str, out_webm: str) -> str:
    ensure_parent(out_webm)
    try:
        if has_tool("ffmpeg"):
            # This would encode a capture; using placeholder for now
            Path(out_webm).write_text("WebM placeholder (recorded)\n", encoding="utf-8")
        else:
            Path(out_webm).write_text("WebM placeholder\n", encoding="utf-8")
    except Exception:
        Path(out_webm).write_text("WebM export failed; placeholder\n", encoding="utf-8")
    return out_webm


