from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ai_orchestrator.domain.enums import AgentType, ReviewDecision
from ai_orchestrator.domain.models.agent_run import AgentRun
from ai_orchestrator.domain.models.execution import ExecutionEvent
from ai_orchestrator.domain.models.memory import MemoryRecord
from ai_orchestrator.domain.models.review import ReviewResult
from ai_orchestrator.infrastructure.db.models import (
    AgentRunRow,
    ExecutionEventRow,
    MemoryRecordRow,
    ReviewResultRow,
)


def agent_run_to_row(run: AgentRun) -> AgentRunRow:
    return AgentRunRow(
        id=run.id,
        workflow_id=run.workflow_id,
        task_id=run.task_id,
        agent_type=run.agent_type.value,
        model=run.model,
        status=run.status,
        input=run.input,
        output=run.output,
        error=run.error,
        started_at=run.started_at,
        finished_at=run.finished_at,
    )


def row_to_agent_run(row: AgentRunRow) -> AgentRun:
    return AgentRun(
        id=row.id,
        workflow_id=row.workflow_id,
        task_id=row.task_id,
        agent_type=AgentType(row.agent_type),
        model=row.model,
        status=row.status,
        input=row.input,
        output=row.output,
        error=row.error,
        started_at=row.started_at,
        finished_at=row.finished_at,
    )


def review_result_to_row(review: ReviewResult) -> ReviewResultRow:
    return ReviewResultRow(
        id=review.id,
        workflow_id=review.workflow_id,
        task_id=review.task_id,
        decision=review.decision.value,
        findings=review.findings,
        required_fixes=review.required_fixes,
        created_at=review.created_at,
    )


def row_to_review_result(row: ReviewResultRow) -> ReviewResult:
    return ReviewResult(
        id=row.id,
        workflow_id=row.workflow_id,
        task_id=row.task_id,
        decision=ReviewDecision(row.decision),
        findings=row.findings,
        required_fixes=row.required_fixes,
        created_at=row.created_at,
    )


def memory_record_to_row(record: MemoryRecord) -> MemoryRecordRow:
    return MemoryRecordRow(
        id=record.id,
        workflow_id=record.workflow_id,
        scope=record.scope,
        kind=record.kind,
        content=record.content,
        embedding_ref=record.embedding_ref,
        metadata_json=record.metadata,
        created_at=record.created_at,
    )


def row_to_memory_record(row: MemoryRecordRow) -> MemoryRecord:
    return MemoryRecord(
        id=row.id,
        workflow_id=row.workflow_id,
        scope=row.scope,
        kind=row.kind,
        content=row.content,
        embedding_ref=row.embedding_ref,
        metadata=row.metadata_json,
        created_at=row.created_at,
    )


def execution_event_to_row(event: ExecutionEvent) -> ExecutionEventRow:
    return ExecutionEventRow(
        id=event.id,
        workflow_id=event.workflow_id,
        task_id=event.task_id,
        event_type=event.event_type,
        payload=event.payload,
        created_at=event.created_at,
    )


def row_to_execution_event(row: ExecutionEventRow) -> ExecutionEvent:
    return ExecutionEvent(
        id=row.id,
        workflow_id=row.workflow_id,
        task_id=row.task_id,
        event_type=row.event_type,
        payload=row.payload,
        created_at=row.created_at,
    )


class SqlAlchemyExecutionEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: ExecutionEvent) -> None:
        self._session.add(execution_event_to_row(event))

    async def list_by_workflow(self, workflow_id: UUID) -> list[ExecutionEvent]:
        result = await self._session.execute(
            select(ExecutionEventRow)
            .where(ExecutionEventRow.workflow_id == workflow_id)
            .order_by(ExecutionEventRow.created_at)
        )
        return [row_to_execution_event(row) for row in result.scalars().all()]
