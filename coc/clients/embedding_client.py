"""Minimal async OpenAI-compatible embedding client."""
from __future__ import annotations

from typing import List

from openai import AsyncOpenAI


class EmbeddingClient:
    def __init__(
        self,
        base_url: str,
        model_name: str,
        api_key: str = "",
        timeout: int = 120,
    ) -> None:
        self.model_name = model_name
        self._client = AsyncOpenAI(
            base_url=base_url.rstrip("/"),
            api_key=api_key or "EMPTY",
            timeout=timeout,
        )

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        resp = await self._client.embeddings.create(
            model=self.model_name, input=texts
        )
        return [item.embedding for item in resp.data]

    async def embed(self, text: str) -> List[float]:
        results = await self.embed_texts([text])
        return results[0] if results else []

    async def close(self) -> None:
        await self._client.close()
