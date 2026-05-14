from __future__ import annotations

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ai_orchestrator.domain.enums import TaskKind, TaskStatus, WorkflowStatus
from ai_orchestrator.domain.models.artifact import Artifact
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.db.models import ArtifactRow, TaskRow, WorkflowRow


def workflow_to_row(workflow: Workflow) -> WorkflowRow:
    return WorkflowRow(
        id=workflow.id,
        user_task=workflow.user_task,
        status=workflow.status.value,
        branch_name=workflow.branch_name,
        base_ref=workflow.base_ref,
        max_retries=workflow.max_retries,
        created_at=workflow.created_at,
        updated_at=workflow.updated_at,
    )


def row_to_workflow(row: WorkflowRow) -> Workflow:
    return Workflow(
        id=row.id,
        user_task=row.user_task,
        status=WorkflowStatus(row.status),
        branch_name=row.branch_name,
        base_ref=row.base_ref,
        max_retries=row.max_retries,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def task_to_row(task: Task) -> TaskRow:
    return TaskRow(
        id=task.id,
        workflow_id=task.workflow_id,
        parent_task_id=task.parent_task_id,
        kind=task.kind.value,
        title=task.title,
        description=task.description,
        status=task.status.value,
        priority=task.priority,
        attempt_count=task.attempt_count,
        max_attempts=task.max_attempts,
        input=task.input,
        output=task.output,
        dependency_ids=[str(dependency_id) for dependency_id in task.dependency_ids],
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def row_to_task(row: TaskRow) -> Task:
    return Task(
        id=row.id,
        workflow_id=row.workflow_id,
        parent_task_id=row.parent_task_id,
        kind=TaskKind(row.kind),
        title=row.title,
        description=row.description,
        status=TaskStatus(row.status),
        priority=row.priority,
        attempt_count=row.attempt_count,
        max_attempts=row.max_attempts,
        input=row.input,
        output=row.output,
        dependency_ids=[UUID(value) for value in row.dependency_ids],
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def artifact_to_row(artifact: Artifact) -> ArtifactRow:
    return ArtifactRow(
        id=artifact.id,
        workflow_id=artifact.workflow_id,
        task_id=artifact.task_id,
        kind=str(artifact.kind),
        path=artifact.path,
        content_hash=artifact.content_hash,
        metadata_json=artifact.metadata,
        created_at=artifact.created_at,
    )


def row_to_artifact(row: ArtifactRow) -> Artifact:
    return Artifact(
        id=row.id,
        workflow_id=row.workflow_id,
        task_id=row.task_id,
        kind=row.kind,
        path=row.path,
        content_hash=row.content_hash,
        metadata=row.metadata_json,
        created_at=row.created_at,
    )


class SqlAlchemyWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, workflow: Workflow) -> None:
        self._session.add(workflow_to_row(workflow))

    async def get(self, workflow_id: UUID) -> Workflow:
        row = await self._session.get(WorkflowRow, workflow_id)
        if row is None:
            raise KeyError(f"Workflow {workflow_id} not found.")
        return row_to_workflow(row)

    async def update(self, workflow: Workflow) -> None:
        await self._session.merge(workflow_to_row(workflow))

    async def list_recent(self, limit: int = 50) -> list[Workflow]:
        result = await self._session.execute(
            select(WorkflowRow).order_by(WorkflowRow.created_at.desc()).limit(limit)
        )
        return [row_to_workflow(row) for row in result.scalars().all()]


class SqlAlchemyTaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add_many(self, tasks: list[Task]) -> None:
        self._session.add_all([task_to_row(task) for task in tasks])

    async def add(self, task: Task) -> None:
        self._session.add(task_to_row(task))

    async def get(self, task_id: UUID) -> Task:
        row = await self._session.get(TaskRow, task_id)
        if row is None:
            raise KeyError(f"Task {task_id} not found.")
        return row_to_task(row)

    async def claim_queued(self, task_id: UUID) -> Task | None:
        result = await self._session.execute(
            update(TaskRow)
            .where(TaskRow.id == task_id, TaskRow.status == TaskStatus.QUEUED.value)
            .values(status=TaskStatus.RUNNING.value, attempt_count=TaskRow.attempt_count + 1)
            .returning(TaskRow)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return row_to_task(row)

    async def update(self, task: Task) -> None:
        await self._session.merge(task_to_row(task))

    async def list_by_workflow(self, workflow_id: UUID) -> list[Task]:
        result = await self._session.execute(
            select(TaskRow).where(TaskRow.workflow_id == workflow_id).order_by(TaskRow.created_at)
        )
        return [row_to_task(row) for row in result.scalars().all()]


class SqlAlchemyArtifactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, artifact: Artifact) -> None:
        self._session.add(artifact_to_row(artifact))

    async def list_by_task(self, task_id: UUID) -> list[Artifact]:
        result = await self._session.execute(
            select(ArtifactRow).where(ArtifactRow.task_id == task_id).order_by(ArtifactRow.created_at)
        )
        return [row_to_artifact(row) for row in result.scalars().all()]

    async def list_by_workflow(self, workflow_id: UUID) -> list[Artifact]:
        result = await self._session.execute(
            select(ArtifactRow)
            .where(ArtifactRow.workflow_id == workflow_id)
            .order_by(ArtifactRow.created_at)
        )
        return [row_to_artifact(row) for row in result.scalars().all()]
