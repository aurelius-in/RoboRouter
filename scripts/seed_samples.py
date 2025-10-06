from __future__ import annotations

import json
from pathlib import Path

SAMPLES_DIR = Path("samples")


def main() -> None:
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    # Tiny placeholder sample metadata
    (SAMPLES_DIR / "scene1.json").write_text(json.dumps({"uri": "./data/sample1.laz", "crs": "EPSG:3857"}, indent=2) + "\n", encoding="utf-8")
    print("Seeded sample metadata in ./samples")


if __name__ == "__main__":
    main()
