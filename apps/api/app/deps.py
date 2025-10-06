from __future__ import annotations

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

