from __future__ import annotations

from pathlib import Path

from apps.api.app.pipeline.segmentation import run_segmentation
from apps.api.app.pipeline.change_detection import run_change_detection


def test_segmentation_stub_outputs(tmp_path: Path) -> None:
    inp = tmp_path / "in.laz"
    inp.write_text("placeholder\n", encoding="utf-8")
    out_dir = tmp_path / "seg"
    res = run_segmentation(str(inp), str(out_dir))
    assert float(res["miou"]) >= 0.0
    for k in ("classes_path", "confidence_path", "entropy_path"):
        assert Path(res[k]).exists()


def test_change_detection_stub_outputs(tmp_path: Path) -> None:
    base = tmp_path / "base.laz"
    cur = tmp_path / "cur.laz"
    base.write_text("b\n", encoding="utf-8")
    cur.write_text("c\n", encoding="utf-8")
    out_dir = tmp_path / "chg"
    res = run_change_detection(str(base), str(cur), str(out_dir))
    assert float(res["f1"]) >= 0.0
    for k in ("change_mask_path", "delta_table_path"):
        assert Path(res[k]).exists()


