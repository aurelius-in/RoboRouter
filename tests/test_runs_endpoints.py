from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_runs_list_smoke() -> None:
    r = client.get("/runs")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body


def test_runs_csv_smoke() -> None:
    r = client.get("/runs/csv")
    # In an empty DB this may be 404; allow both
    assert r.status_code in (200, 404)

