from __future__ import annotations

import pytest

from ai_orchestrator.application.orchestrator.policies import ToolPermissionError
from ai_orchestrator.application.tools.permissions import ToolPermissionPolicy
from ai_orchestrator.domain.enums import AgentType, TaskKind


def test_tool_permission_policy_allows_granted_tool_for_agent_and_task() -> None:
    policy = ToolPermissionPolicy(grants={(AgentType.TESTER, TaskKind.TESTING): {"pytest"}})

    policy.validate(
        tool_name="pytest",
        agent_type=AgentType.TESTER,
        task_kind=TaskKind.TESTING,
    )


def test_tool_permission_policy_rejects_missing_context_grant() -> None:
    policy = ToolPermissionPolicy(grants={(AgentType.TESTER, TaskKind.TESTING): {"pytest"}})

    with pytest.raises(ToolPermissionError):
        policy.validate(
            tool_name="pytest",
            agent_type=AgentType.CODER,
            task_kind=TaskKind.CODING,
        )


def test_tool_permission_policy_allows_legacy_unscoped_calls() -> None:
    policy = ToolPermissionPolicy(grants={(AgentType.TESTER, TaskKind.TESTING): {"pytest"}})

    policy.validate(tool_name="pytest", agent_type=None, task_kind=None)
