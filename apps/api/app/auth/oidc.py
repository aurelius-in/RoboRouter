from __future__ import annotations

from typing import Any, Dict, Optional

from ..config import settings


def is_enabled() -> bool:
    return bool(getattr(settings, "oidc_enabled", False))


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Best-effort OIDC token verification stub.

    In production, validate signature and audience/issuer. Here we only gate on config flag.
    """
    if not is_enabled():
        return {"sub": "anonymous", "iss": None}
    # Real implementation would validate against the issuer JWKS
    if token and token.startswith("eyJ"):
        return {"sub": "stub", "iss": getattr(settings, "oidc_issuer", None)}
    return None


