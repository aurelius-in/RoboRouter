from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_export_allowed_potree(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    e = client.post(f"/export?scene_id={scene_id}&type=potree&crs=EPSG:3857")
    assert e.status_code == 200
    body = e.json()
    assert body["type"] == "potree"
    assert body["uri"].startswith("s3://")


def test_export_blocked_type(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    e = client.post(f"/export?scene_id={scene_id}&type=exe&crs=EPSG:3857")
    assert e.status_code == 403

