from __future__ import annotations

from typing import Protocol

from ai_orchestrator.application.agents.schemas import (
    AgentInput,
    CoderOutput,
    PlannerOutput,
    ReviewerOutput,
    TesterOutput,
)


class AgentClient(Protocol):
    async def plan(self, request: AgentInput) -> PlannerOutput: ...

    async def code(self, request: AgentInput) -> CoderOutput: ...

    async def test(self, request: AgentInput) -> TesterOutput: ...

    async def review(self, request: AgentInput) -> ReviewerOutput: ...

