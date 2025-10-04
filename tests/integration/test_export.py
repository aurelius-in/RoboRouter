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
    assert "artifact_id" in body

    # Verify we can obtain a presigned URL to open inline (index.html)
    from apps.api.app.db import SessionLocal
    from apps.api.app.models import Artifact
    from sqlalchemy import select
    db = SessionLocal()
    try:
        art = db.execute(select(Artifact).where(Artifact.scene_id == scene_id, Artifact.type == "export_potree")).scalars().first()
        assert art is not None
        a = client.get(f"/artifacts/{art.id}")
        assert a.status_code == 200
        url = a.json()["url"]
        assert url.startswith("http")
    finally:
        db.close()


def test_export_blocked_type(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    e = client.post(f"/export?scene_id={scene_id}&type=exe&crs=EPSG:3857")
    assert e.status_code == 403


def test_export_allowed_other_types(tmp_path) -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    src = tmp_path / "empty.laz"
    src.touch()
    r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
    assert r.status_code == 200
    scene_id = r.json()["scene_id"]

    for t in ["laz", "gltf", "webm"]:
        e = client.post(f"/export?scene_id={scene_id}&type={t}&crs=EPSG:3857")
        assert e.status_code == 200
        body = e.json()
        assert body["type"] == t
        assert body["uri"].startswith("s3://")
        assert "artifact_id" in body

