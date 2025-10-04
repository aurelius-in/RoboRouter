from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_auth_ping() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/auth/ping")
    assert r.status_code == 200
    assert r.json().get("authorized") is True


