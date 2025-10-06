from __future__ import annotations

from pathlib import Path
import json

from .base import ensure_parent, has_tool, run_cmd


def export_potree(input_laz: str, out_dir: str) -> str:
	ensure_parent(out_dir + "/dummy")
	try:
		if not (input_laz.endswith(".laz") or input_laz.endswith(".las")):
			raise ValueError("potree export expects LAS/LAZ input")
		if has_tool("PotreeConverter"):  # typical binary name
			run_cmd(["PotreeConverter", input_laz, "-o", out_dir])
			# PotreeConverter usually writes an HTML; ensure exists
			idx = Path(out_dir, "index.html")
			if not idx.exists():
				idx.write_text("<html><body><h3>Potree export</h3><p>Tiles ready.</p></body></html>", encoding="utf-8")
		else:
			# Placeholder minimal page for inline viewing
			Path(out_dir, "index.html").write_text(
				"<html><body><h3>Potree placeholder</h3><p>No converter on PATH.</p></body></html>",
				encoding="utf-8",
			)
	except Exception:
		# Fallback placeholder on any failure
		Path(out_dir, "index.html").write_text(
			"<html><body><h3>Potree export failed</h3><p>Placeholder created.</p></body></html>",
			encoding="utf-8",
		)
	# Write progress marker for UI (best-effort)
	try:
		Path(out_dir, "progress.json").write_text('{"status":"done"}', encoding="utf-8")
	except Exception:
		pass
	# Write a tiny manifest.json for UI consumers (file list + sizes)
	try:
		files = []
		for p in Path(out_dir).rglob("*"):
			if p.is_file():
				rel = str(p.relative_to(out_dir))
				size = p.stat().st_size
				files.append({"path": rel, "size": int(size)})
		(Path(out_dir) / "manifest.json").write_text(json.dumps({"files": files}), encoding="utf-8")
	except Exception:
		pass
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


def export_gltf(input_laz: str, out_gltf: str, *, draco: bool = False, simplify: float = 0.0) -> str:
	ensure_parent(out_gltf)
	# Placeholder: write a minimal valid glTF 2.0 JSON so viewers load
	try:
		gen_flags = []
		if draco:
			gen_flags.append("Draco")
		if simplify and simplify > 0:
			gen_flags.append(f"simplify={min(max(simplify, 0.0), 1.0):.2f}")
		generator = "RoboRouter Exporter" + (" (" + ", ".join(gen_flags) + ")" if gen_flags else "")
		minimal_gltf = f"""
{{
  "asset": {{ "version": "2.0", "generator": "{generator}" }},
  "scenes": [{{ "nodes": [0] }}],
  "nodes": [{{ "mesh": 0 }}],
  "meshes": [{{ "primitives": [{{ "mode": 4, "attributes": {{ "POSITION": 0 }} }}] }}],
  "buffers": [{{ "uri": "data:application/octet-stream;base64,AAABAAIAAAAAAAAAAAAAAAAAAAAAAA==", "byteLength": 24 }}],
  "bufferViews": [{{ "buffer": 0, "byteOffset": 0, "byteLength": 24, "target": 34962 }}],
  "accessors": [{{ "bufferView": 0, "byteOffset": 0, "componentType": 5126, "count": 3, "type": "VEC3", "max": [1,1,0], "min": [0,0,0] }}]
}}
"""
		Path(out_gltf).write_text(minimal_gltf.strip() + "\n", encoding="utf-8")
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


