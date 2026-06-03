from api.services.rate_limiter import InMemoryRateLimiter


def test_rate_limiter_blocks_requests_after_limit():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    first = limiter.check("chat:user-1")
    second = limiter.check("chat:user-1")
    third = limiter.check("chat:user-1")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds > 0
