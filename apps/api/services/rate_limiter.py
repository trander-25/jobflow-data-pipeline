from dataclasses import dataclass
from threading import Lock
from time import monotonic

from api.config import Settings


@dataclass(frozen=True)
class RateLimitDecision:
    """Decision returned by a rate limiter check."""

    allowed: bool
    remaining: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    """Process-local sliding-window rate limiter used as a local fallback."""

    def __init__(self, max_requests: int, window_seconds: int):
        """Initialize request limits and the in-memory timestamp store."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitDecision:
        """Check and record one request for a logical rate-limit key."""
        now = monotonic()
        cutoff = now - self.window_seconds

        with self._lock:
            timestamps = [timestamp for timestamp in self._requests.get(key, []) if timestamp > cutoff]
            if len(timestamps) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - timestamps[0])))
                self._requests[key] = timestamps
                return RateLimitDecision(allowed=False, remaining=0, retry_after_seconds=retry_after)

            timestamps.append(now)
            self._requests[key] = timestamps
            remaining = max(0, self.max_requests - len(timestamps))
            return RateLimitDecision(allowed=True, remaining=remaining, retry_after_seconds=0)


class RedisRateLimiter:
    """Redis-backed fixed-window rate limiter shared across API instances."""

    def __init__(self, settings: Settings, client=None):
        """Initialize Redis settings and create or reuse a Redis client."""
        self.max_requests = settings.rate_limit_requests
        self.window_seconds = settings.rate_limit_window_seconds
        self.key_prefix = settings.redis_rate_limit_prefix

        if client is not None:
            self.client = client
            return

        from redis import Redis

        self.client = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            socket_connect_timeout=settings.redis_socket_timeout_seconds,
            socket_timeout=settings.redis_socket_timeout_seconds,
            decode_responses=True,
        )

    def healthcheck(self) -> None:
        """Verify Redis is reachable."""
        self.client.ping()

    def check(self, key: str) -> RateLimitDecision:
        """Increment the Redis counter for a key and return the rate-limit decision."""
        redis_key = f"{self.key_prefix}:{key}"
        count = int(self.client.incr(redis_key))
        if count == 1:
            self.client.expire(redis_key, self.window_seconds)

        ttl = int(self.client.ttl(redis_key))
        retry_after = ttl if ttl > 0 else self.window_seconds

        if count > self.max_requests:
            return RateLimitDecision(allowed=False, remaining=0, retry_after_seconds=retry_after)

        remaining = max(0, self.max_requests - count)
        return RateLimitDecision(allowed=True, remaining=remaining, retry_after_seconds=0)
