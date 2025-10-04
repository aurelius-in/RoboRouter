from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends

from ..deps import require_api_key

router = APIRouter(tags=["Auth"])


@router.get("/auth/ping")
def auth_ping(_: Any = Depends(require_api_key)) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return {"authorized": True, "message": "API key valid"}


