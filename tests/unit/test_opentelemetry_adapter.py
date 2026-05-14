from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.telemetry.opentelemetry import OpenTelemetryAdapter


def test_opentelemetry_adapter_uses_injected_meter_and_tracer() -> None:
    asyncio.run(_assert_opentelemetry_adapter_uses_injected_meter_and_tracer())


async def _assert_opentelemetry_adapter_uses_injected_meter_and_tracer() -> None:
    calls = []

    class Counter:
        def add(self, value, attributes=None):
            calls.append(("counter", value, attributes))

    class Histogram:
        def record(self, value, attributes=None):
            calls.append(("histogram", value, attributes))

    class Meter:
        def create_counter(self, name):
            calls.append(("create_counter", name))
            return Counter()

        def create_histogram(self, name):
            calls.append(("create_histogram", name))
            return Histogram()

    class Span:
        def __enter__(self):
            calls.append(("span_enter",))
            return self

        def __exit__(self, exc_type, exc, tb):
            calls.append(("span_exit",))
            return False

        def set_attribute(self, key, value):
            calls.append(("attribute", key, value))

    class Tracer:
        def start_as_current_span(self, name):
            calls.append(("span", name))
            return Span()

    telemetry = OpenTelemetryAdapter(meter=Meter(), tracer=Tracer())

    await telemetry.increment("tasks.approved", {"kind": "coding"})
    await telemetry.observe("tasks.duration", 1.5, {"kind": "coding"})
    await telemetry.event("workflow.created", {"workflow_id": "wf"})

    assert ("counter", 1, {"kind": "coding"}) in calls
    assert ("histogram", 1.5, {"kind": "coding"}) in calls
    assert ("span", "workflow.created") in calls
    assert ("attribute", "workflow_id", "wf") in calls
