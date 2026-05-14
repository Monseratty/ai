from __future__ import annotations

import asyncio
import os

import pytest

from ai_orchestrator.domain.enums import TaskKind, TaskStatus
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.infrastructure.db.repositories import (
    SqlAlchemyTaskRepository,
    SqlAlchemyWorkflowRepository,
)
from ai_orchestrator.infrastructure.db.session import create_session_factory

pytest.importorskip("asyncpg")


def require_integration() -> None:
    if os.getenv("AIO_RUN_INTEGRATION_TESTS") != "1":
        pytest.skip("Set AIO_RUN_INTEGRATION_TESTS=1 to run live integration tests.")


def test_postgres_repositories_persist_and_claim_task() -> None:
    require_integration()
    asyncio.run(_assert_postgres_repositories_persist_and_claim_task())


async def _assert_postgres_repositories_persist_and_claim_task() -> None:
    database_url = os.getenv(
        "AIO_DATABASE_URL",
        "postgresql+asyncpg://orchestrator:orchestrator@localhost:5432/orchestrator",
    )
    session_factory = create_session_factory(database_url)
    async with session_factory() as session:
        async with session.begin():
            workflows = SqlAlchemyWorkflowRepository(session)
            tasks = SqlAlchemyTaskRepository(session)
            workflow = Workflow(user_task="integration")
            await workflows.add(workflow)
            task = Task(
                workflow_id=workflow.id,
                kind=TaskKind.CODING,
                title="Code",
                description="Code",
            )
            await tasks.add(task.with_status(TaskStatus.QUEUED))
            await session.flush()

            claimed = await tasks.claim_queued(task.id)

            assert claimed is not None
            assert claimed.attempt_count == 1
