from __future__ import annotations

from ai_orchestrator.domain.enums import AgentType, ReviewDecision
from ai_orchestrator.domain.models.agent_run import AgentRun
from ai_orchestrator.domain.models.execution import ExecutionEvent
from ai_orchestrator.domain.models.memory import MemoryRecord
from ai_orchestrator.domain.models.review import ReviewResult
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.db.audit_repositories import (
    agent_run_to_row,
    execution_event_to_row,
    memory_record_to_row,
    review_result_to_row,
    row_to_agent_run,
    row_to_execution_event,
    row_to_memory_record,
    row_to_review_result,
)


def test_agent_run_roundtrip_preserves_structured_io_and_error() -> None:
    workflow = Workflow(user_task="root")
    run = AgentRun(
        workflow_id=workflow.id,
        task_id=None,
        agent_type=AgentType.PLANNER,
        model="gpt-5.2",
        status="failed",
        input={"objective": "plan"},
        output=None,
        error="schema validation failed",
    )

    assert row_to_agent_run(agent_run_to_row(run)) == run


def test_review_result_roundtrip_preserves_decision_and_findings() -> None:
    workflow = Workflow(user_task="root")
    review = ReviewResult(
        workflow_id=workflow.id,
        task_id=workflow.id,
        decision=ReviewDecision.REQUEST_FIXES,
        findings=[{"category": "security", "message": "network enabled"}],
        required_fixes=["Disable sandbox network."],
    )

    assert row_to_review_result(review_result_to_row(review)) == review


def test_memory_and_execution_event_roundtrip_preserve_payloads() -> None:
    workflow = Workflow(user_task="root")
    memory = MemoryRecord(
        workflow_id=workflow.id,
        scope="workflow",
        kind="summary",
        content="Planner decomposed the work.",
        metadata={"source": "planner"},
    )
    event = ExecutionEvent(
        workflow_id=workflow.id,
        task_id=None,
        event_type="workflow.planned",
        payload={"task_count": 2},
    )

    assert row_to_memory_record(memory_record_to_row(memory)) == memory
    assert row_to_execution_event(execution_event_to_row(event)) == event
