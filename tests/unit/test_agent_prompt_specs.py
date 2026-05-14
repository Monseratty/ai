from __future__ import annotations

from ai_orchestrator.application.agents.prompts import AGENT_PROMPTS
from ai_orchestrator.domain.enums import AgentType


def test_agent_prompts_are_versioned_for_auditability() -> None:
    assert set(AGENT_PROMPTS) == {
        AgentType.PLANNER,
        AgentType.CODER,
        AgentType.TESTER,
        AgentType.REVIEWER,
    }
    assert AGENT_PROMPTS[AgentType.REVIEWER].version == "reviewer.v1"
    assert "hallucinated APIs" in AGENT_PROMPTS[AgentType.REVIEWER].instructions
