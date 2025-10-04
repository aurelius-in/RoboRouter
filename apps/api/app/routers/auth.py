from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter

router = APIRouter(tags=["Auth"])


@router.get("/auth/ping")
def auth_ping() -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return {"authorized": True}


