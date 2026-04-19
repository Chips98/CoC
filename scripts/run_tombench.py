"""Thin wrapper: evaluate CoC on a ToMBench-style JSONL split."""
from __future__ import annotations

import asyncio
from _runner import run  # noqa: E402

if __name__ == "__main__":
    asyncio.run(run("tombench"))
