from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_ingest_stub_ok(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # create empty file to act as input when PDAL not installed
    src = tmp_path / "empty.laz"
    src.touch()

    client = TestClient(app)
    resp = client.post(
        "/ingest",
        json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {"sensor": "test"}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert uuid.UUID(body["scene_id"])  # parseable
    assert isinstance(body["artifact_ids"], list)
    assert "metrics" in body

