from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_delete_scene(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    d = client.delete(f"/scene/{scene_id}")
    assert d.status_code == 200
    b = d.json()
    assert b.get("deleted") == scene_id


