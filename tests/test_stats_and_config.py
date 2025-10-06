from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_stats_shape() -> None:
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    # Presence checks
    for key in ("scenes", "artifacts", "metrics", "exports"):
        assert key in body


def test_config_shape() -> None:
    r = client.get("/config")
    assert r.status_code == 200
    cfg = r.json()
    # Minimal keys that should exist
    assert "minio_bucket_processed" in cfg
    assert "presign_expires_seconds" in cfg


