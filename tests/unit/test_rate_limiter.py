from __future__ import annotations

import asyncio

import pytest

from ai_orchestrator.api.rate_limit import (
    InMemoryRateLimiter,
    RateLimitExceeded,
    RedisRateLimiter,
)


def test_in_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60, now=lambda: 1000.0)

    asyncio.run(limiter.check("client"))
    asyncio.run(limiter.check("client"))

    with pytest.raises(RateLimitExceeded):
        asyncio.run(limiter.check("client"))


def test_in_memory_rate_limiter_resets_after_window() -> None:
    current_time = 1000.0

    def now() -> float:
        return current_time

    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, now=now)
    asyncio.run(limiter.check("client"))
    current_time = 1061.0
    asyncio.run(limiter.check("client"))


class FakeRedis:
    def __init__(self, counts: list[int]) -> None:
        self.counts = counts
        self.expirations: list[tuple[str, int]] = []
        self.keys: list[str] = []

    async def incr(self, key: str) -> int:
        self.keys.append(key)
        return self.counts.pop(0)

    async def expire(self, key: str, seconds: int) -> None:
        self.expirations.append((key, seconds))


def test_redis_rate_limiter_sets_expiration_on_first_hit() -> None:
    redis = FakeRedis([1])
    limiter = RedisRateLimiter(redis=redis, limit=10, window_seconds=60, namespace="api")

    asyncio.run(limiter.check("token"))

    assert len(redis.keys) == 1
    assert redis.keys[0].startswith("api:")
    assert "token" not in redis.keys[0]
    assert redis.expirations == [(redis.keys[0], 60)]


def test_redis_rate_limiter_blocks_after_limit() -> None:
    redis = FakeRedis([3])
    limiter = RedisRateLimiter(redis=redis, limit=2, window_seconds=60)

    with pytest.raises(RateLimitExceeded):
        asyncio.run(limiter.check("client"))
