from __future__ import annotations

from typing import Any

from ai_orchestrator.interfaces.telemetry import Telemetry


class OpenTelemetryAdapter(Telemetry):
    def __init__(self, *, meter=None, tracer=None) -> None:
        self._meter = meter or self._default_meter()
        self._tracer = tracer or self._default_tracer()
        self._counters = {}
        self._histograms = {}

    async def event(self, name: str, attributes: dict[str, Any]) -> None:
        with self._tracer.start_as_current_span(name) as span:
            for key, value in attributes.items():
                span.set_attribute(key, value)

    async def increment(
        self, name: str, attributes: dict[str, Any] | None = None, value: int = 1
    ) -> None:
        counter = self._counters.get(name)
        if counter is None:
            counter = self._meter.create_counter(name)
            self._counters[name] = counter
        counter.add(value, attributes=attributes or {})

    async def observe(
        self, name: str, value: float, attributes: dict[str, Any] | None = None
    ) -> None:
        histogram = self._histograms.get(name)
        if histogram is None:
            histogram = self._meter.create_histogram(name)
            self._histograms[name] = histogram
        histogram.record(value, attributes=attributes or {})

    def _default_meter(self):
        try:
            from opentelemetry import metrics
        except ImportError as exc:
            raise RuntimeError("Install opentelemetry-api to use OpenTelemetryAdapter.") from exc
        return metrics.get_meter("ai_orchestrator")

    def _default_tracer(self):
        try:
            from opentelemetry import trace
        except ImportError as exc:
            raise RuntimeError("Install opentelemetry-api to use OpenTelemetryAdapter.") from exc
        return trace.get_tracer("ai_orchestrator")
