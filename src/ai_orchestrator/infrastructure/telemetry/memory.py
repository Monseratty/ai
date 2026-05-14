from __future__ import annotations

from typing import Any

from ai_orchestrator.interfaces.telemetry import Telemetry


class InMemoryTelemetry(Telemetry):
    def __init__(self) -> None:
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.counters: list[tuple[str, int, dict[str, Any]]] = []
        self.observations: list[tuple[str, float, dict[str, Any]]] = []

    async def event(self, name: str, attributes: dict[str, Any]) -> None:
        self.events.append((name, attributes))

    async def increment(
        self, name: str, attributes: dict[str, Any] | None = None, value: int = 1
    ) -> None:
        self.counters.append((name, value, attributes or {}))

    async def observe(
        self, name: str, value: float, attributes: dict[str, Any] | None = None
    ) -> None:
        self.observations.append((name, value, attributes or {}))
