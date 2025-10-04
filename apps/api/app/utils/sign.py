from __future__ import annotations

import hmac
import hashlib
import os
from typing import Any, Dict


def sign_dict(data: Dict[str, Any], secret_env: str = "ROBOROUTER_AUDIT_SECRET") -> str | None:
    secret = os.getenv(secret_env)
    if not secret:
        return None
    msg = "|".join(f"{k}={data[k]}" for k in sorted(data.keys()))
    return hmac.new(secret.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()


