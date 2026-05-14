from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ai_orchestrator.infrastructure.db.approval_repositories import SqlAlchemyApprovalRepository
from ai_orchestrator.infrastructure.db.audit_repositories import SqlAlchemyExecutionEventRepository
from ai_orchestrator.infrastructure.db.repositories import (
    SqlAlchemyArtifactRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyWorkflowRepository,
)


class SqlAlchemyUnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.workflows = SqlAlchemyWorkflowRepository(session)
        self.tasks = SqlAlchemyTaskRepository(session)
        self.artifacts = SqlAlchemyArtifactRepository(session)
        self.approvals = SqlAlchemyApprovalRepository(session)
        self.execution_events = SqlAlchemyExecutionEventRepository(session)


@asynccontextmanager
async def unit_of_work(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[SqlAlchemyUnitOfWork]:
    async with session_factory() as session:
        async with session.begin():
            yield SqlAlchemyUnitOfWork(session)
