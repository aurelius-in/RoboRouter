from __future__ import annotations

import uuid
from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_models_list_and_register() -> None:
    r = client.get("/models")
    assert r.status_code == 200
    body = r.json()
    assert "segmentation" in body
    r2 = client.post("/models/register", params={"name": "dummy", "uri": "models:/dummy"})
    assert r2.status_code == 200


def test_policy_check_post() -> None:
    r = client.post("/policy/check", json={"export_type": "gltf", "crs": "EPSG:3857"})
    assert r.status_code == 200
    body = r.json()
    assert "allowed" in body and "reason" in body and "policy_version" in body


def test_artifact_head_404() -> None:
    bogus = str(uuid.uuid4())
    r = client.get(f"/artifacts/head/{bogus}")
    assert r.status_code == 404


def test_gates_smoke() -> None:
    # Unlikely to have a real scene yet; allow 200 or 422/404 based on validation
    sid = str(uuid.uuid4())
    r = client.get(f"/gates?scene_id={sid}")
    assert r.status_code in (200, 404, 422)


