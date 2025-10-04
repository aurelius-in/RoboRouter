from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_models_list() -> None:  # type: ignore[no-untyped-def]
    client = TestClient(app)
    r = client.get("/models")
    assert r.status_code == 200
    body = r.json()
    assert "segmentation" in body and isinstance(body["segmentation"], list)


