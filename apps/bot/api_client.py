from typing import Any

import httpx

from bot.config import BotSettings


class JobFlowApiClient:
    def __init__(self, settings: BotSettings):
        self.base_url = settings.api_base_url.rstrip("/")
        self.timeout = settings.api_timeout_seconds

    async def ask(self, user_id: str, question: str, top_k: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"user_id": user_id, "message": question}
        if top_k is not None:
            payload["top_k"] = top_k
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/chat", json=payload)
            response.raise_for_status()
            return response.json()

    async def search_jobs(self, query: str, user_id: str | None = None, top_k: int | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query}
        if user_id is not None:
            payload["user_id"] = user_id
        if top_k is not None:
            payload["top_k"] = top_k
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/jobs/search", json=payload)
            response.raise_for_status()
            return response.json()

    async def reset_history(self, user_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(f"{self.base_url}/chat/history/{user_id}")
            response.raise_for_status()
            return response.json()
