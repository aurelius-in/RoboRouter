from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_meta_includes_perf_and_orchestrator() -> None:
    r = client.get("/meta")
    assert r.status_code == 200
    body = r.json()
    assert "orchestrator" in body
    assert "orchestrator_max_retries" in body
    assert isinstance(body.get("perf"), dict)
    perf = body["perf"]
    assert "seg_batch_points" in perf
    assert "change_tiles" in perf


def test_auth_ping_and_me() -> None:
    # auth/ping requires API key only if configured; by default, it should be open via middleware guard for GET
    r = client.get("/auth/ping")
    assert r.status_code == 200
    body = r.json()
    assert body.get("authorized") is True

    r2 = client.get("/auth/me")
    assert r2.status_code == 200
    me = r2.json()
    assert "username" in me and "roles" in me


