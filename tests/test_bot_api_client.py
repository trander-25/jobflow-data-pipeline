import httpx
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
