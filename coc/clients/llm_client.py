"""Minimal async OpenAI-compatible chat client.

Works with any OpenAI-compatible endpoint: OpenAI, vLLM, TGI, llama.cpp
server, DashScope, etc.  Exposes the single method the engine needs:

    await client.one_chat(messages, temperature=0.0) -> str
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from openai import AsyncOpenAI


class LLMClient:
    def __init__(
        self,
        model_name: str,
        api_base: str,
        api_key: str = "EMPTY",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        timeout: float = 120.0,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = AsyncOpenAI(
            base_url=api_base,
            api_key=api_key or "EMPTY",
            timeout=timeout,
        )

    async def one_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        resp = await self._client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature if temperature is None else temperature,
            max_tokens=self.max_tokens if max_tokens is None else max_tokens,
        )
        return resp.choices[0].message.content or ""

    async def close(self) -> None:
        await self._client.close()
