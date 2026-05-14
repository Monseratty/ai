from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai_orchestrator.api.deps import get_orchestrator
from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.domain.enums import TaskKind, TaskStatus, WorkflowStatus

router = APIRouter(prefix="/workflows", tags=["workflows"])


class CreateWorkflowRequest(BaseModel):
    user_task: str = Field(min_length=1)


class WorkflowResponse(BaseModel):
    id: UUID
    status: WorkflowStatus
    user_task: str


class TaskResponse(BaseModel):
    id: UUID
    kind: TaskKind
    status: TaskStatus
    title: str
    description: str
    dependency_ids: list[UUID]


class WorkflowSnapshotResponse(BaseModel):
    workflow: WorkflowResponse
    tasks: list[TaskResponse]


class ArtifactResponse(BaseModel):
    id: UUID
    task_id: UUID | None
    kind: str
    path: str | None
    content_hash: str | None
    metadata: dict


class ExecutionEventResponse(BaseModel):
    id: UUID
    task_id: UUID | None
    event_type: str
    payload: dict


class TaskExecutionResponse(BaseModel):
    task_id: UUID
    workflow_id: UUID
    summary: str
    skipped: bool = False


@router.post("", response_model=WorkflowResponse, status_code=202)
async def create_workflow(
    request: CreateWorkflowRequest,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> WorkflowResponse:
    workflow = await orchestrator.create_workflow(request.user_task)
    return WorkflowResponse(id=workflow.id, status=workflow.status, user_task=workflow.user_task)


@router.get("", response_model=list[WorkflowResponse])
async def list_workflows(
    limit: int = 50,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> list[WorkflowResponse]:
    workflows = await orchestrator.list_workflows(limit=limit)
    return [
        WorkflowResponse(id=workflow.id, status=workflow.status, user_task=workflow.user_task)
        for workflow in workflows
    ]


@router.get("/{workflow_id}", response_model=WorkflowSnapshotResponse)
async def get_workflow(
    workflow_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> WorkflowSnapshotResponse:
    snapshot = await orchestrator.get_workflow_snapshot(workflow_id)
    return WorkflowSnapshotResponse(
        workflow=WorkflowResponse(
            id=snapshot.workflow.id,
            status=snapshot.workflow.status,
            user_task=snapshot.workflow.user_task,
        ),
        tasks=[
            TaskResponse(
                id=task.id,
                kind=task.kind,
                status=task.status,
                title=task.title,
                description=task.description,
                dependency_ids=task.dependency_ids,
            )
            for task in snapshot.tasks
        ],
    )


@router.get("/{workflow_id}/artifacts", response_model=list[ArtifactResponse])
async def list_workflow_artifacts(
    workflow_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> list[ArtifactResponse]:
    artifacts = await orchestrator.list_workflow_artifacts(workflow_id)
    return [
        ArtifactResponse(
            id=artifact.id,
            task_id=artifact.task_id,
            kind=str(artifact.kind),
            path=artifact.path,
            content_hash=artifact.content_hash,
            metadata=artifact.metadata,
        )
        for artifact in artifacts
    ]


@router.get("/{workflow_id}/history", response_model=list[ExecutionEventResponse])
async def list_execution_history(
    workflow_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> list[ExecutionEventResponse]:
    events = await orchestrator.list_execution_history(workflow_id)
    return [
        ExecutionEventResponse(
            id=event.id,
            task_id=event.task_id,
            event_type=event.event_type,
            payload=event.payload,
        )
        for event in events
    ]


@router.post("/tasks/{task_id}/execute", response_model=TaskExecutionResponse)
async def execute_task(
    task_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> TaskExecutionResponse:
    result = await orchestrator.execute_queued_task(task_id)
    if result is None:
        task = await orchestrator.get_task(task_id)
        return TaskExecutionResponse(
            task_id=task.id,
            workflow_id=task.workflow_id,
            summary="Task was not queued and was skipped.",
            skipped=True,
        )
    return TaskExecutionResponse(
        task_id=result.task_id,
        workflow_id=result.workflow_id,
        summary=result.summary,
    )


@router.post("/tasks/{task_id}/retry", response_model=TaskResponse)
async def retry_task(
    task_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> TaskResponse:
    task = await orchestrator.retry_task(task_id)
    return _task_response(task)


@router.post("/{workflow_id}/cancel", response_model=WorkflowResponse)
async def cancel_workflow(
    workflow_id: UUID,
    orchestrator: OrchestratorService = Depends(get_orchestrator),
) -> WorkflowResponse:
    workflow = await orchestrator.cancel_workflow(workflow_id)
    return WorkflowResponse(id=workflow.id, status=workflow.status, user_task=workflow.user_task)


def _task_response(task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        kind=task.kind,
        status=task.status,
        title=task.title,
        description=task.description,
        dependency_ids=task.dependency_ids,
    )
