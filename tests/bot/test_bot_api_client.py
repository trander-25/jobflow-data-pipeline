import asyncio

import httpx
import pytest

from bot.api_client import JobFlowApiClient, JobFlowApiError
from bot.config import BotSettings


def test_api_client_error_detail_uses_fastapi_detail_message():
    client = JobFlowApiClient(BotSettings(api_base_url="http://api:8100"))
    response = httpx.Response(
        502,
        json={"detail": "Google GenAI request failed for model 'bad-model': model not found"},
        request=httpx.Request("POST", "http://api:8100/chat"),
    )

    try:
        client._raise_for_status(response)
    except JobFlowApiError as exc:
        assert "502 Bad Gateway" in str(exc)
        assert "bad-model" in str(exc)
        assert "model not found" in str(exc)
    else:
        raise AssertionError("Expected JobFlowApiError")


def test_api_client_timeout_error_is_descriptive(monkeypatch):
    client = JobFlowApiClient(BotSettings(api_base_url="http://api:8100", api_timeout_seconds=12))

    async def raise_timeout(*args, **kwargs):
        raise httpx.ReadTimeout("")

    monkeypatch.setattr(httpx.AsyncClient, "post", raise_timeout)

    with pytest.raises(JobFlowApiError) as exc_info:
        asyncio.run(client.ask(user_id="discord-user", question="cho tôi 2 job lương cao nhất"))

    message = str(exc_info.value)
    assert "Timed out waiting for JobFlow API after 12s" in message
    assert "/chat" in message
