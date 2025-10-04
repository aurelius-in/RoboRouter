from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_generate_report_stub(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)

    # Create a scene by ingesting a dummy file
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    # Generate report
    rep = client.post(f"/report/generate?scene_id={scene_id}")
    assert rep.status_code == 200
    body = rep.json()
    assert body["scene_id"] == scene_id
    assert "reasons" in body

