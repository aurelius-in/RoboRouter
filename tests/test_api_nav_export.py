from __future__ import annotations

import os
import sys


def _ensure_path() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root not in sys.path:
        sys.path.insert(0, root)


_ensure_path()

from fastapi.testclient import TestClient  # noqa: E402
from apps.api.app.main import app  # type: ignore  # noqa: E402


client = TestClient(app)


def test_nav_map_and_plan() -> None:
    assert client.get('/nav/map?scene_id=foo&type=occupancy').status_code == 200
    assert client.get('/nav/plan?scene_id=foo&start=0,0,0&goal=1,1,0&planner=astar').status_code == 200


def test_export_bad_type() -> None:
    r = client.post('/export?scene_id=00000000-0000-0000-0000-000000000000&type=bad')
    # Scene not found likely first
    assert r.status_code in (400, 404)


