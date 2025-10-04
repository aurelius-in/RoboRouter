from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_golden_scene_gates(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)

    src = tmp_path / "empty.laz"
    src.touch()

    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    p = client.post(f"/pipeline/run?scene_id={scene_id}", json={"steps": ["registration", "segmentation", "change_detection"], "config_overrides": {}})
    assert p.status_code == 200
    body = p.json()

    # Registration gate
    assert body["metrics"]["rmse"] <= 0.10
    assert body["metrics"]["inlier_ratio"] >= 0.70

    # Segmentation gate
    assert body["metrics"]["miou"] >= 0.70

    # Change detection gate
    assert body["metrics"]["change_f1"] >= 0.70


