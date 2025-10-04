from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_pipeline_registration_stub(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)

    src = tmp_path / "empty.laz"
    src.touch()

    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    p = client.post(f"/pipeline/run?scene_id={scene_id}", json={"steps": ["registration"], "config_overrides": {}})
    assert p.status_code == 200
    body = p.json()
    assert body["scene_id"] == scene_id
    assert "rmse" in body["metrics"]
    assert "inlier_ratio" in body["metrics"]
    assert len(body["artifacts"]) >= 2

