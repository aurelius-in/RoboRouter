from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_metrics_endpoint() -> None:
    client = TestClient(app)
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "roborouter_requests_total" in r.text

