from __future__ import annotations

import asyncio

from ai_orchestrator.domain.enums import TaskKind, TaskStatus
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.testing.fakes import InMemoryTaskRepository


def test_in_memory_task_repository_claims_only_queued_tasks() -> None:
    asyncio.run(_assert_in_memory_task_repository_claims_only_queued_tasks())


async def _assert_in_memory_task_repository_claims_only_queued_tasks() -> None:
    workflow = Workflow(user_task="claim")
    queued = Task(
        workflow_id=workflow.id,
        kind=TaskKind.CODING,
        title="Queued",
        description="Queued",
        status=TaskStatus.QUEUED,
    )
    succeeded = Task(
        workflow_id=workflow.id,
        kind=TaskKind.CODING,
        title="Succeeded",
        description="Succeeded",
        status=TaskStatus.SUCCEEDED,
    )
    repo = InMemoryTaskRepository()
    await repo.add_many([queued, succeeded])

    claimed = await repo.claim_queued(queued.id)
    skipped = await repo.claim_queued(succeeded.id)

    assert claimed is not None
    assert claimed.status is TaskStatus.RUNNING
    assert claimed.attempt_count == 1
    assert skipped is None
