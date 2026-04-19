"""CoC — top-level agent entry point.

Provides an async `answer()` interface compatible with the evaluation
harnesses shipped under `scripts/`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from .core.engine import CoCEngine
from .utils.task_utils import normalize_task_input


class CoCAgent:
    """Chain-of-Cognition social reasoning agent."""

    def __init__(
        self,
        llm_client,
        language: str = "en",
        config_path: Optional[Path] = None,
    ):
        self.llm_client = llm_client
        self.language = language
        self.engine = CoCEngine(llm_client, config_path=config_path)

    async def answer(self, task_input: Dict[str, Any]) -> Dict[str, Any]:
        normalized = normalize_task_input(task_input, self.language)
        return await self.engine.run(normalized)

    async def close(self) -> None:
        await self.engine.close()
