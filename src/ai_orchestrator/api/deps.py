from __future__ import annotations

from collections.abc import AsyncIterator
from collections.abc import Callable
from functools import lru_cache

try:
    from fastapi import Header, HTTPException
except ImportError:  # pragma: no cover - exercised in environments without FastAPI.
    def Header(default=None):
        return default

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str) -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.config.settings import Settings
from ai_orchestrator.config.settings import get_settings
from ai_orchestrator.infrastructure.composition import CompositionRoot
from ai_orchestrator.api.security import ApiAuthError, verify_bearer_token
from ai_orchestrator.api.rate_limit import (
    InMemoryRateLimiter,
    RateLimiter,
    RateLimitExceeded,
    RedisRateLimiter,
)


@lru_cache(maxsize=1)
def get_composition_root() -> CompositionRoot:
    return CompositionRoot(settings=get_settings())


@lru_cache(maxsize=1)
def get_rate_limiter() -> RateLimiter:
    return build_rate_limiter(get_settings())


def build_rate_limiter(
    settings: Settings,
    *,
    redis_factory: Callable[[str], object] | None = None,
) -> RateLimiter:
    if settings.api_rate_limit_backend == "memory":
        return InMemoryRateLimiter(limit=settings.api_rate_limit_per_minute)
    if settings.api_rate_limit_backend == "redis":
        if redis_factory is None:
            from redis.asyncio import Redis

            redis_factory = lambda url: Redis.from_url(url, decode_responses=True)

        return RedisRateLimiter(
            redis=redis_factory(settings.redis_url),
            limit=settings.api_rate_limit_per_minute,
        )
    raise ValueError(f"Unsupported API rate limit backend: {settings.api_rate_limit_backend}")


async def get_orchestrator() -> AsyncIterator[OrchestratorService]:
    async with get_composition_root().orchestrator() as orchestrator:
        yield orchestrator


async def get_approval_service() -> AsyncIterator[ApprovalService]:
    root = get_composition_root()
    async with root.unit() as unit:
        yield root.approval_service_for_unit_of_work(unit)


async def get_pull_request_service() -> AsyncIterator[PullRequestService]:
    root = get_composition_root()
    async with root.unit() as unit:
        yield root.pull_request_service_for_unit_of_work(unit)


async def require_api_auth(authorization: str | None = Header(default=None)) -> None:
    try:
        verify_bearer_token(
            configured_token=get_composition_root().settings.api_token,
            authorization=authorization,
        )
        key = authorization or "anonymous"
        await get_rate_limiter().check(key)
    except ApiAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
