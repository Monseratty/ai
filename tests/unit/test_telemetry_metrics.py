from __future__ import annotations

import asyncio

from ai_orchestrator.infrastructure.telemetry.memory import InMemoryTelemetry


def test_in_memory_telemetry_records_events_counters_and_observations() -> None:
    asyncio.run(_assert_in_memory_telemetry_records_events_counters_and_observations())


async def _assert_in_memory_telemetry_records_events_counters_and_observations() -> None:
    telemetry = InMemoryTelemetry()

    await telemetry.event("workflow.created", {"workflow_id": "wf"})
    await telemetry.increment("workflows.created", {"status": "planned"})
    await telemetry.observe("task.duration_ms", 12.5, {"kind": "coding"})

    assert telemetry.events == [("workflow.created", {"workflow_id": "wf"})]
    assert telemetry.counters == [("workflows.created", 1, {"status": "planned"})]
    assert telemetry.observations == [("task.duration_ms", 12.5, {"kind": "coding"})]
