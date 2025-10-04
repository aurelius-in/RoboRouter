from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m scripts.pipeline [ingest|registration|segmentation|change_detection|report]")
        sys.exit(1)
    step = sys.argv[1]
    print(f"[stub] would run {step} stage")


if __name__ == "__main__":
    main()


