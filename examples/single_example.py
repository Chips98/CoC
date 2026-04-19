"""Run one social-reasoning question end-to-end through CoC.

Prerequisite: an OpenAI-compatible chat endpoint (OpenAI, vLLM, TGI …).
Point `api_base` below at your server and set `api_key` if required.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from coc.agent import CoCAgent
from coc.clients.llm_client import LLMClient


SAMPLE_ITEM = {
    "task_name": "tombench",
    "task_type": "mcq",
    "context": (
        "Sally puts a marble into a basket and leaves the room. "
        "While she is away, Anne moves the marble from the basket into a box. "
        "Sally then comes back."
    ),
    "question": "Where will Sally look for her marble?",
    "options": {
        "A": "In the basket.",
        "B": "In the box.",
        "C": "She will ask Anne.",
        "D": "She will give up searching.",
    },
    "meta": {"benchmark_task": "false belief task", "ability": "belief"},
}


async def main() -> None:
    llm = LLMClient(
        model_name="gpt-4o-mini",            # <- replace
        api_base="https://api.openai.com/v1",  # <- replace
        api_key="YOUR_API_KEY_HERE",          # <- replace
    )
    agent = CoCAgent(llm_client=llm)
    try:
        result = await agent.answer(SAMPLE_ITEM)
    finally:
        await agent.close()
        await llm.close()

    print("Cognition chain :", " → ".join(result.get("chain", [])))
    print("Final answer    :", result.get("answer"))
    print("Raw model text  :", (result.get("raw_answer") or "")[:200])
    print("Full result (JSON):")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1200])


if __name__ == "__main__":
    asyncio.run(main())
