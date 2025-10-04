from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_nav_map_and_plan(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)

    # Ingest to create a scene
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    m = client.get(f"/nav/map/{scene_id}")
    assert m.status_code == 200
    mid = m.json()["artifact_id"]
    assert mid

    p = client.post("/nav/plan", json={"scene_id": scene_id, "start": [0, 0], "goal": [10, 0], "constraints": {}})
    assert p.status_code == 200
    body = p.json()
    assert body["allowed"] in [True, False]
    assert isinstance(body["route"], list)

