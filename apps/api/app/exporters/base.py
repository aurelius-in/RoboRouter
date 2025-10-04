from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def run_cmd(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


