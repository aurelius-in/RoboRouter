from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_health_ok() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "api"


def test_meta() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/meta")
    assert r.status_code == 200
    body = r.json()
    assert "version" in body and "name" in body and isinstance(body.get("cors"), list)

