"""Shared evaluation runner used by run_tombench / run_socialiqa / run_sotopia.

Expects a JSONL input file where each line is one task item already in the
shape that `CoCAgent.answer` consumes (`task_name`, `context`, `question`,
`options`, `meta`, …). Converting your raw benchmark dump into this shape
is left as a per-benchmark exercise — the intent here is to showcase the
agent, not to re-ship benchmark data.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coc.agent import CoCAgent
from coc.clients.llm_client import LLMClient


def build_argparser(task_name: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=f"Run CoC on a {task_name} JSONL split."
    )
    p.add_argument("--data", required=True, type=Path,
                   help="Input JSONL (one task item per line).")
    p.add_argument("--out", required=True, type=Path,
                   help="Output directory (created if missing).")
    p.add_argument("--model_name", default=os.environ.get("COC_MODEL", "gpt-4o-mini"))
    p.add_argument("--api_base", default=os.environ.get("COC_API_BASE", "https://api.openai.com/v1"))
    p.add_argument("--api_key", default=os.environ.get("COC_API_KEY", "EMPTY"))
    p.add_argument("--max_workers", type=int, default=4)
    p.add_argument("--limit", type=int, default=None,
                   help="Only run the first N items (for smoke tests).")
    return p


def _load_items(path: Path, limit: int | None):
    items = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
            if limit and len(items) >= limit:
                break
    return items


async def _run_one(agent: CoCAgent, item: dict) -> dict:
    try:
        result = await agent.answer(item)
    except Exception as exc:                       # noqa: BLE001
        return {"error": str(exc), "item": item}
    return {"item": item, "result": result}


async def _bounded(agent, items, max_workers):
    sem = asyncio.Semaphore(max_workers)

    async def worker(it):
        async with sem:
            return await _run_one(agent, it)

    return await asyncio.gather(*(worker(it) for it in items))


async def run(task_name: str, argv: list[str] | None = None) -> None:
    args = build_argparser(task_name).parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    os.environ["COC_BENCHMARK"] = task_name

    llm = LLMClient(
        model_name=args.model_name,
        api_base=args.api_base,
        api_key=args.api_key,
    )
    agent = CoCAgent(llm_client=llm)

    items = _load_items(args.data, args.limit)
    print(f"[CoC/{task_name}] loaded {len(items)} items from {args.data}")

    try:
        outputs = await _bounded(agent, items, args.max_workers)
    finally:
        await agent.close()
        await llm.close()

    out_path = args.out / "predictions.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in outputs:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[CoC/{task_name}] wrote {out_path} ({len(outputs)} rows)")
