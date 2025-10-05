from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, Iterator


@contextmanager
def temporary_settings(settings_obj: Any, updates: Dict[str, Any]) -> Iterator[None]:  # type: ignore[type-arg]
    if not updates:
        yield
        return
    original: Dict[str, Any] = {}
    try:
        for k, v in updates.items():
            if hasattr(settings_obj, k):
                original[k] = getattr(settings_obj, k)
                setattr(settings_obj, k, v)
        yield
    finally:
        for k, v in original.items():
            setattr(settings_obj, k, v)


