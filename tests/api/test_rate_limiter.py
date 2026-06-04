from api.config import Settings
from api.services.rate_limiter import InMemoryRateLimiter, RedisRateLimiter


def test_rate_limiter_blocks_requests_after_limit():
    limiter = InMemoryRateLimiter(max_requests=2, window_seconds=60)

    first = limiter.check("chat:user-1")
    second = limiter.check("chat:user-1")
    third = limiter.check("chat:user-1")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds > 0


class FakeRedisClient:
    def __init__(self):
        self.values = {}
        self.expirations = {}

    def incr(self, key):
        self.values[key] = self.values.get(key, 0) + 1
        return self.values[key]

    def expire(self, key, seconds):
        self.expirations[key] = seconds

    def ttl(self, key):
        return self.expirations.get(key, -1)

    def ping(self):
        return True


def test_redis_rate_limiter_uses_shared_counter_and_ttl():
    client = FakeRedisClient()
    settings = Settings(
        rate_limit_requests=2,
        rate_limit_window_seconds=60,
        redis_rate_limit_prefix="test:rate_limit",
    )
    limiter = RedisRateLimiter(settings, client=client)

    first = limiter.check("chat:user-1")
    second = limiter.check("chat:user-1")
    third = limiter.check("chat:user-1")

    assert first.allowed is True
    assert second.allowed is True
    assert third.allowed is False
    assert third.retry_after_seconds == 60
    assert client.values["test:rate_limit:chat:user-1"] == 3
