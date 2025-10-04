from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_runs_list(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    # Seed a scene
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200

    rr = client.get("/runs?limit=5")
    assert rr.status_code == 200
    body = rr.json()
    assert "items" in body and isinstance(body["items"], list)

