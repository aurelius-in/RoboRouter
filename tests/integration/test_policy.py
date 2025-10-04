from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_policy_allowed() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/policy/check?type=potree&crs=EPSG:3857")
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is True


def test_policy_blocked_crs() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/policy/check?type=potree&crs=EPSG:9999")
    assert r.status_code == 200
    body = r.json()
    assert body["allowed"] is False

