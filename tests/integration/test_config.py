from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_get_config() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/config")
    assert r.status_code == 200
    body = r.json()
    assert "thresholds" in body and isinstance(body["thresholds"], dict)
    assert "allowed_crs" in body and isinstance(body["allowed_crs"], list)
    assert "presign_expires_seconds" in body
    assert "rate_limit_rpm" in body
    assert "retention_days" in body


