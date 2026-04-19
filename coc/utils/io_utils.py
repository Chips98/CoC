from __future__ import annotations

import fcntl
import json
from datetime import datetime
from pathlib import Path
from typing import Any


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def dump_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def append_jsonl(path: Path, payload: Any) -> None:
    """Bug #6 fix: 带文件锁的原子 append，防止并发写截断 JSON 行"""
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            handle.flush()
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def now_ts() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_jsonl(path: Path) -> list[dict]:
    """加载 JSONL 文件"""
    if not path.exists():
        return []
    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_text(path: Path) -> str:
    """加载文本文件"""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")
