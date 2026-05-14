from __future__ import annotations

import logging
from typing import Any

from ai_orchestrator.interfaces.telemetry import Telemetry


class StructuredLoggingTelemetry(Telemetry):
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger("ai_orchestrator.telemetry")

    async def event(self, name: str, attributes: dict[str, Any]) -> None:
        self._logger.info("telemetry_event", extra={"event_name": name, "attributes": attributes})

    async def increment(
        self, name: str, attributes: dict[str, Any] | None = None, value: int = 1
    ) -> None:
        self._logger.info(
            "telemetry_counter",
            extra={"metric_name": name, "value": value, "attributes": attributes or {}},
        )

    async def observe(
        self, name: str, value: float, attributes: dict[str, Any] | None = None
    ) -> None:
        self._logger.info(
            "telemetry_observation",
            extra={"metric_name": name, "value": value, "attributes": attributes or {}},
        )
