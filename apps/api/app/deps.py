from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request, status

from .config import settings
from .auth.oidc import verify_token


def require_api_key(request: Request) -> None:  # type: ignore[no-untyped-def]
    """Dependency that enforces API key if configured.

    Used on sensitive routes even if a global middleware exists.
    """
    if not settings.api_key:
        return
    key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")



def require_role(required_role: str):
    def _inner(request: Request) -> None:  # type: ignore[no-untyped-def]
        role = request.headers.get("X-Role") or request.headers.get("x-role")
        if not role or role.lower() != required_role.lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return _inner


def require_oidc_user(request: Request) -> None:  # type: ignore[no-untyped-def]
    if not getattr(settings, "oidc_enabled", False):
        return
    authz = request.headers.get("Authorization") or request.headers.get("authorization")
    if not authz or not authz.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authz.split(" ", 1)[1]
    claims = verify_token(token)
    if not claims:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


def require_scene_access(scene_id: Any, request: Request) -> None:  # type: ignore[no-untyped-def]
    """Best-effort scene-level authorization.

    If authz_enforce_scenes is enabled, require either X-Role: admin or an X-Scene-Access header
    containing the scene_id.
    """
    if not getattr(settings, "authz_enforce_scenes", False):
        return
    role = (request.headers.get("X-Role") or "").lower()
    if role == "admin":
        return
    allow = request.headers.get("X-Scene-Access") or ""
    if str(scene_id) not in allow:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden for scene")

