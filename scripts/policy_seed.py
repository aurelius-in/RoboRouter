from __future__ import annotations

from pathlib import Path
import shutil

def main() -> None:
    src_dir = Path("configs/opa")
    dst_dir = Path("configs/opa")
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in ("policy.yaml", "policies.rego"):
        src = src_dir / name
        if src.exists():
            shutil.copy2(src, dst_dir / name)
    print("Seeded OPA policies in configs/opa")

if __name__ == "__main__":
    main()
