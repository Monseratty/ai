from __future__ import annotations

from typing import Any, Protocol


class Telemetry(Protocol):
    async def event(self, name: str, attributes: dict[str, Any]) -> None: ...

    async def increment(
        self, name: str, attributes: dict[str, Any] | None = None, value: int = 1
    ) -> None: ...

    async def observe(
        self, name: str, value: float, attributes: dict[str, Any] | None = None
    ) -> None: ...
