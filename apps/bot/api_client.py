from typing import Any

import httpx

from bot.config import BotSettings


class JobFlowApiError(Exception):
    """Raised when the Discord bot cannot complete a JobFlow API request."""

    pass


class JobFlowApiClient:
    """Async HTTP client used by the Discord bot to call the JobFlow API."""

    def __init__(self, settings: BotSettings):
        """Store API base URL and timeout settings."""
        self.base_url = settings.api_base_url.rstrip("/")
        self.timeout = settings.api_timeout_seconds

    async def ask(self, user_id: str, question: str, top_k: int | None = None) -> dict[str, Any]:
        """Call the API chat endpoint for a Discord user question."""
        payload: dict[str, Any] = {"user_id": user_id, "message": question}
        if top_k is not None:
            payload["top_k"] = top_k
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await self._post(client, "/chat", payload)
            self._raise_for_status(response)
            return response.json()

    async def search_jobs(self, query: str, user_id: str | None = None, top_k: int | None = None) -> dict[str, Any]:
        """Call the API job-search endpoint without LLM generation."""
        payload: dict[str, Any] = {"query": query}
        if user_id is not None:
            payload["user_id"] = user_id
        if top_k is not None:
            payload["top_k"] = top_k
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await self._post(client, "/jobs/search", payload)
            self._raise_for_status(response)
            return response.json()

    async def reset_history(self, user_id: str) -> dict[str, Any]:
        """Delete stored chat history for a Discord user."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            path = f"/chat/history/{user_id}"
            try:
                response = await client.delete(f"{self.base_url}{path}")
            except httpx.TimeoutException as exc:
                raise JobFlowApiError(self._timeout_message(path)) from exc
            except httpx.RequestError as exc:
                raise JobFlowApiError(self._request_error_message(path, exc)) from exc
            self._raise_for_status(response)
            return response.json()

    async def _post(self, client: httpx.AsyncClient, path: str, payload: dict[str, Any]) -> httpx.Response:
        """Send a JSON POST request and wrap transport errors for bot output."""
        try:
            return await client.post(f"{self.base_url}{path}", json=payload)
        except httpx.TimeoutException as exc:
            raise JobFlowApiError(self._timeout_message(path)) from exc
        except httpx.RequestError as exc:
            raise JobFlowApiError(self._request_error_message(path, exc)) from exc

    def _timeout_message(self, path: str) -> str:
        """Build a user-facing timeout message for an API path."""
        return (
            f"Timed out waiting for JobFlow API after {self.timeout:g}s while calling {path}. "
            "The API may still be processing the request; increase API_TIMEOUT_SECONDS if this happens often."
        )

    def _request_error_message(self, path: str, exc: httpx.RequestError) -> str:
        """Build a user-facing network error message for an API path."""
        detail = str(exc) or exc.__class__.__name__
        return f"Could not reach JobFlow API at {self.base_url}{path}: {detail}"

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Raise JobFlowApiError when the API returns a non-success status."""
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = self._error_detail(response)
            raise JobFlowApiError(f"{response.status_code} {response.reason_phrase}: {detail}") from exc

    @staticmethod
    def _error_detail(response: httpx.Response) -> str:
        """Extract a readable error detail from a JobFlow API response."""
        try:
            payload = response.json()
        except ValueError:
            return response.text.strip() or "No response body"

        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, dict):
            return str(detail.get("message") or detail)
        if detail:
            return str(detail)
        return str(payload)
