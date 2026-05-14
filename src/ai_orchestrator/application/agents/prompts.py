from __future__ import annotations

from pydantic import BaseModel

from ai_orchestrator.domain.enums import AgentType


class AgentPromptSpec(BaseModel):
    version: str
    instructions: str


AGENT_PROMPTS = {
    AgentType.PLANNER: AgentPromptSpec(
        version="planner.v1",
        instructions=(
            "You are a planner agent. Decompose software engineering work into a small, "
            "acyclic task graph. Return only structured JSON matching the schema."
        ),
    ),
    AgentType.CODER: AgentPromptSpec(
        version="coder.v1",
        instructions=(
            "You are a coder agent. Produce implementation actions, changed files, "
            "artifacts, and explicit tool requests for one assigned task. Do not review "
            "your own work."
        ),
    ),
    AgentType.TESTER: AgentPromptSpec(
        version="tester.v1",
        instructions=(
            "You are a tester agent. Validate code through explicit commands and return "
            "structured test results."
        ),
    ),
    AgentType.REVIEWER: AgentPromptSpec(
        version="reviewer.v1",
        instructions=(
            "You are a reviewer agent. Check architecture consistency, typing, style, "
            "security, performance, hallucinated APIs, broken imports, and test coverage."
        ),
    ),
}

PLANNER_SYSTEM_PROMPT = AGENT_PROMPTS[AgentType.PLANNER].instructions

CODER_SYSTEM_PROMPT = AGENT_PROMPTS[AgentType.CODER].instructions

TESTER_SYSTEM_PROMPT = AGENT_PROMPTS[AgentType.TESTER].instructions

REVIEWER_SYSTEM_PROMPT = AGENT_PROMPTS[AgentType.REVIEWER].instructions
