from dataclasses import dataclass
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int


class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}
        self._lock = Lock()

    def check(self, key: str) -> RateLimitDecision:
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
