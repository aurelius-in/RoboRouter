from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, Request

from ..deps import require_api_key, require_oidc_user
from ..auth.oidc import verify_token

router = APIRouter(tags=["Auth"])


@router.get("/auth/ping")
def auth_ping(_: Any = Depends(require_api_key)) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    return {"authorized": True, "message": "API key valid"}


@router.get("/auth/me")
def auth_me(request: Request, _: Any = Depends(require_oidc_user)) -> Dict[str, Any]:  # type: ignore[no-untyped-def]
    authz = request.headers.get("Authorization") or request.headers.get("authorization")
    token = (authz.split(" ", 1)[1] if authz and " " in authz else "")
    claims = verify_token(token) or {}
    return {"claims": claims}


