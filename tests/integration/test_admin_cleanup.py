from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_admin_cleanup() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.post("/admin/cleanup")
    assert r.status_code == 200
    body = r.json()
    assert "deleted" in body and "cutoff" in body


