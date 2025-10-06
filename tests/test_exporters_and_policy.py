from __future__ import annotations

from pathlib import Path

from apps.api.app.exporters.exporters import export_gltf
from apps.api.app.policy.opa import _load_policy, evaluate_export_policy


def test_export_gltf_minimal(tmp_path: Path) -> None:
    inp = tmp_path / "in.laz"
    inp.write_text("placeholder\n", encoding="utf-8")
    out = tmp_path / "out.gltf"
    p = export_gltf(str(inp), str(out), draco=True, simplify=0.25)
    assert Path(p).exists()
    text = Path(p).read_text(encoding="utf-8")
    assert '"asset"' in text and '"generator"' in text


def test_policy_loader_and_eval() -> None:
    allowed_types, allowed_crs, version = _load_policy()
    assert isinstance(version, str) and len(version) > 0
    ok, reason = evaluate_export_policy({"type": "gltf", "crs": "EPSG:3857"})
    assert isinstance(ok, bool)
    assert isinstance(reason, str)


