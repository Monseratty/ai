from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Callable
from hashlib import sha256
from typing import Protocol
from time import time


class RateLimitExceeded(RuntimeError):
    """Raised when a client exceeds the configured request rate."""


class RateLimiter(Protocol):
    async def check(self, key: str) -> None:
        """Raise RateLimitExceeded if the key has exceeded its request budget."""


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

    async def check(self, key: str) -> None:
        current = self._now()
        requests = self._requests[key]
        while requests and requests[0] <= current - self._window_seconds:
            requests.popleft()
        if len(requests) >= self._limit:
            raise RateLimitExceeded("Rate limit exceeded.")
        requests.append(current)


class RedisClient(Protocol):
    async def incr(self, key: str) -> int:
        """Increment a key and return the new value."""

    async def expire(self, key: str, seconds: int) -> object:
        """Set key expiration."""


class RedisRateLimiter:
    def __init__(
        self,
        *,
        redis: RedisClient,
        limit: int,
        window_seconds: int = 60,
        namespace: str = "aio:rate-limit",
    ) -> None:
        self._redis = redis
        self._limit = limit
        self._window_seconds = window_seconds
        self._namespace = namespace

    async def check(self, key: str) -> None:
        redis_key = self._key_for(key)
        count = await self._redis.incr(redis_key)
        if count == 1:
            await self._redis.expire(redis_key, self._window_seconds)
        if count > self._limit:
            raise RateLimitExceeded("Rate limit exceeded.")

    def _key_for(self, key: str) -> str:
        digest = sha256(key.encode("utf-8")).hexdigest()
        return f"{self._namespace}:{digest}"
