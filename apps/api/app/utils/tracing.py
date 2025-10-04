from __future__ import annotations

import contextlib
import time
from typing import Iterator


@contextlib.contextmanager
def span(name: str) -> Iterator[None]:
    start = time.time()
    try:
        yield
    finally:
        dur = (time.time() - start) * 1000.0
        print(f"[trace] {name} took {dur:.1f} ms")


