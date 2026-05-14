from __future__ import annotations

import pytest

from ai_orchestrator.api.rate_limit import InMemoryRateLimiter, RateLimitExceeded


def test_in_memory_rate_limiter_blocks_after_limit() -> None:
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60, now=lambda: 1000.0)

    limiter.check("client")
    limiter.check("client")

    with pytest.raises(RateLimitExceeded):
        limiter.check("client")


def test_in_memory_rate_limiter_resets_after_window() -> None:
    current_time = 1000.0

    def now() -> float:
        return current_time

    limiter = InMemoryRateLimiter(limit=1, window_seconds=60, now=now)
    limiter.check("client")
    current_time = 1061.0
    limiter.check("client")
