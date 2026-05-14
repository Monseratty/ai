from __future__ import annotations

from uuid import UUID

from ai_orchestrator.application.git.branching import BranchNamingPolicy


def test_branch_naming_policy_builds_safe_unique_branch_name() -> None:
    policy = BranchNamingPolicy(prefix="codex/")
    workflow_id = UUID("12345678-1234-5678-1234-567812345678")

    branch_name = policy.for_workflow(
        workflow_id=workflow_id,
        user_task="Add API auth + reviewer loop!!!",
    )

    assert branch_name == "codex/add-api-auth-reviewer-loop-12345678"


def test_branch_naming_policy_uses_fallback_slug_for_symbol_only_tasks() -> None:
    policy = BranchNamingPolicy(prefix="feature/")
    workflow_id = UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")

    branch_name = policy.for_workflow(workflow_id=workflow_id, user_task="!!!")

    assert branch_name == "feature/workflow-aaaaaaaa"
