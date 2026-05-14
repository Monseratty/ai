from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from time import time


class RateLimitExceeded(RuntimeError):
    """Raised when a client exceeds the configured request rate."""


class InMemoryRateLimiter:
    def __init__(
        self,
        *,
        limit: int,
        window_seconds: int = 60,
        now: Callable[[], float] = time,
    ) -> None:
        self._limit = limit
        self._window_seconds = window_seconds
        self._now = now
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        current = self._now()
        requests = self._requests[key]
        while requests and requests[0] <= current - self._window_seconds:
            requests.popleft()
        if len(requests) >= self._limit:
            raise RateLimitExceeded("Rate limit exceeded.")
        requests.append(current)
