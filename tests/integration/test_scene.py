from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


def test_scene_detail(tmp_path) -> None:  # type: ignore[no-untyped-def]
	client = TestClient(app)
	src = tmp_path / "empty.laz"
	src.touch()
	r = client.post("/ingest", json={"source_uri": str(src), "crs": "EPSG:3857", "sensor_meta": {}})
	assert r.status_code == 200
	scene_id = r.json()["scene_id"]

	s = client.get(f"/scene/{scene_id}")
	assert s.status_code == 200
	body = s.json()
	assert body["id"] == scene_id
	assert isinstance(body["artifacts"], list)
	assert isinstance(body["metrics"], list)

    rlist = client.get("/scenes?offset=0&limit=10")
    assert rlist.status_code == 200
    lst = rlist.json()
    assert isinstance(lst, dict)
    assert isinstance(lst.get("items"), list)
    assert any(item["id"] == scene_id for item in lst.get("items", []))

