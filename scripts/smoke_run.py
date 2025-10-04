from __future__ import annotations

import json
import sys
from urllib.request import urlopen


def main() -> int:
    try:
        with urlopen("http://localhost:8000/health", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") == "ok"
        print("Smoke OK:", data)
        return 0
    except Exception as exc:  # noqa: BLE001
        print("Smoke FAIL:", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())

