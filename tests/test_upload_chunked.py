from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.app.main import app


client = TestClient(app)


def test_chunked_upload_roundtrip(tmp_path) -> None:  # type: ignore[no-redef]
    # init
    r = client.post("/upload/chunk/init", params={"filename": "hello.txt"})
    assert r.status_code == 200
    upload_id = r.json()["upload_id"]
    # two chunks
    files = {
        "upload_id": (None, upload_id),
        "chunk_index": (None, "0"),
        "total_chunks": (None, "2"),
        "chunk": ("chunk0", b"hello ", "application/octet-stream"),
    }
    r1 = client.post("/upload/chunk", files=files)
    assert r1.status_code == 200

    files2 = {
        "upload_id": (None, upload_id),
        "chunk_index": (None, "1"),
        "total_chunks": (None, "2"),
        "chunk": ("chunk1", b"world", "application/octet-stream"),
    }
    r2 = client.post("/upload/chunk", files=files2)
    assert r2.status_code == 200

    # complete
    rc = client.post("/upload/chunk/complete", params={"upload_id": upload_id})
    assert rc.status_code == 200
    path = rc.json()["path"]
    with open(path, "rb") as f:
        data = f.read()
    assert data == b"hello world"


