from __future__ import annotations

from fastapi import HTTPException, Request, status

from .config import settings


def require_api_key(request: Request) -> None:  # type: ignore[no-untyped-def]
    """Dependency that enforces API key if configured.

    Used on sensitive routes even if a global middleware exists.
    """
    if not settings.api_key:
        return
    key = request.headers.get("X-API-Key") or request.headers.get("x-api-key")
    if key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


