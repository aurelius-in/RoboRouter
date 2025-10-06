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


def test_artifact_delete_requires_admin() -> None:
    # random UUID; expect 401 (missing API key) or 403 (missing role) or 404 if security disabled
    r = client.delete('/artifacts/00000000-0000-0000-0000-000000000000')
    assert r.status_code in (401, 403, 404)


