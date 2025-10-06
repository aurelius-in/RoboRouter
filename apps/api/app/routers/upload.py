from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import os
import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile


router = APIRouter(tags=["Upload"])


@router.post("/upload")
async def upload(file: UploadFile = File(...)) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / file.filename
    # Avoid overwriting silently: add suffix if exists
    i = 1
    base = dest.stem
    ext = dest.suffix
    while dest.exists():
        dest = uploads_dir / f"{base}_{i}{ext}"
        i += 1
    data = await file.read()
    dest.write_bytes(data)
    return {"path": str(dest.resolve())}


# Resumable, chunked upload API (best-effort local implementation)

SESSIONS_DIR = Path("uploads/sessions")
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload/chunk/init")
def init_chunked_upload(filename: str) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """Initialize a chunked upload and return an upload_id."""
    upload_id = str(uuid.uuid4())
    session_dir = SESSIONS_DIR / upload_id
    (session_dir / "chunks").mkdir(parents=True, exist_ok=True)
    (session_dir / "filename").write_text(filename, encoding="utf-8")
    return {"upload_id": upload_id}


@router.post("/upload/chunk")
async def upload_chunk(upload_id: str = File(..., alias="upload_id"), chunk_index: int = File(...), total_chunks: int = File(...), chunk: UploadFile = File(...)) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """Upload a single chunk for an existing upload_id.

    Stores chunks to uploads/sessions/<upload_id>/chunks/<index>.
    """
    session_dir = SESSIONS_DIR / upload_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="upload_id not found")
    try:
        idx = int(chunk_index)
        total = int(total_chunks)
    except Exception:
        raise HTTPException(status_code=400, detail="invalid chunk indices")
    if idx < 0 or total <= 0 or idx >= total:
        raise HTTPException(status_code=400, detail="chunk_index/total_chunks out of range")
    target = session_dir / "chunks" / f"{idx:08d}"
    data = await chunk.read()
    with open(target, "wb") as f:
        f.write(data)
    return {"upload_id": upload_id, "chunk_index": idx, "total_chunks": total}


@router.post("/upload/chunk/complete")
def complete_chunked_upload(upload_id: str) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    """Finalize a chunked upload by concatenating chunk files in order to final destination under uploads/."""
    session_dir = SESSIONS_DIR / upload_id
    if not session_dir.exists():
        raise HTTPException(status_code=404, detail="upload_id not found")
    try:
        filename = (session_dir / "filename").read_text(encoding="utf-8").strip()
    except Exception:
        raise HTTPException(status_code=400, detail="session missing filename")
    chunks_dir = session_dir / "chunks"
    parts = sorted([p for p in chunks_dir.glob("*") if p.is_file()])
    if not parts:
        raise HTTPException(status_code=400, detail="no chunks uploaded")
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / filename
    with open(dest, "wb") as out:
        for p in parts:
            with open(p, "rb") as f:
                out.write(f.read())
    # cleanup session best-effort
    try:
        for p in parts:
            try:
                os.remove(p)
            except Exception:
                pass
        try:
            os.remove(session_dir / "filename")
        except Exception:
            pass
        try:
            (session_dir / "chunks").rmdir()
        except Exception:
            pass
        try:
            session_dir.rmdir()
        except Exception:
            pass
    except Exception:
        pass
    return {"path": str(dest.resolve())}

