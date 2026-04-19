from __future__ import annotations

from pathlib import Path


def default_log_dir(package_root: Path) -> Path:
    return package_root / "logs"
