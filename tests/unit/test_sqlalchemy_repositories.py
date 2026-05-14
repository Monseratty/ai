from __future__ import annotations

from ai_orchestrator.domain.enums import TaskKind, TaskStatus, WorkflowStatus
from ai_orchestrator.domain.models.artifact import Artifact
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.db.repositories import (
    artifact_to_row,
    row_to_artifact,
    row_to_task,
    row_to_workflow,
    task_to_row,
    workflow_to_row,
)


def test_workflow_row_roundtrip_preserves_domain_fields() -> None:
    workflow = Workflow(user_task="Build orchestration", status=WorkflowStatus.PLANNED)

    restored = row_to_workflow(workflow_to_row(workflow))

    assert restored == workflow


def test_task_row_roundtrip_preserves_dependency_ids_and_structured_payloads() -> None:
    dependency = Task(workflow_id=Workflow(user_task="root").id, kind=TaskKind.CODING, title="A", description="A")
    task = Task(
        workflow_id=dependency.workflow_id,
        kind=TaskKind.TESTING,
        title="Test",
        description="Run tests",
        status=TaskStatus.BLOCKED,
        input={"command": "pytest"},
        output={"passed": True},
        dependency_ids=[dependency.id],
    )

    restored = row_to_task(task_to_row(task))

    assert restored == task


def test_artifact_row_roundtrip_preserves_metadata() -> None:
    workflow = Workflow(user_task="root")
    task = Task(workflow_id=workflow.id, kind=TaskKind.CODING, title="Code", description="Code")
    artifact = Artifact(
        workflow_id=workflow.id,
        task_id=task.id,
        kind="diff",
        path="artifacts/change.diff",
        metadata={"lines": 42},
    )

    restored = row_to_artifact(artifact_to_row(artifact))

    assert restored == artifact
