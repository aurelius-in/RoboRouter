from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

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


