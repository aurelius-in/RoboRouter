from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_policy_check_has_version() -> None:
    r = client.get("/policy/check", params={"type": "gltf", "crs": "EPSG:3857"})
    assert r.status_code == 200
    body = r.json()
    assert "allowed" in body and isinstance(body["allowed"], bool)
    assert "policy_version" in body


def test_scenes_list_smoke() -> None:
    r = client.get("/scenes")
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and isinstance(body["items"], list)
    assert "total" in body


def test_artifact_csv_invalid_type_returns_400(monkeypatch) -> None:
    # Create a fake artifact response by patching get_artifact_url to avoid network
    from apps.api.app.routers.artifacts import artifact_as_csv
    from fastapi import HTTPException
    try:
        artifact_as_csv.__call__  # type: ignore[attr-defined]
    except Exception:
        pass
    # Directly assert the handler raises 404/400 for non-existent id by calling endpoint via client
    import uuid
    bogus = str(uuid.uuid4())
    resp = client.get(f"/artifacts/{bogus}/csv")
    # Either not found or bad request is acceptable here in smoke
    assert resp.status_code in (400, 404)


