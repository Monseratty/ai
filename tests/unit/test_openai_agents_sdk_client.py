from __future__ import annotations

from uuid import uuid4
import asyncio
import pytest

from ai_orchestrator.application.agents.schemas import AgentInput, PlannerOutput
from ai_orchestrator.application.agents.config import AgentModelConfig
from ai_orchestrator.domain.enums import TaskKind
from ai_orchestrator.infrastructure.openai.agents_sdk_client import (
    AgentOutputValidationError,
    OpenAIAgentsSDKClient,
)


def test_openai_agents_client_renders_structured_payload_without_mutating_input() -> None:
    client = OpenAIAgentsSDKClient(model="gpt-5.2")
    request = AgentInput(
        workflow_id=uuid4(),
        objective="Build queue adapter",
        memory=["Use bounded retries."],
        artifacts=[{"kind": "diff", "path": "artifacts/change.diff"}],
    )

    payload = client.render_input(request)

    assert "Build queue adapter" in payload
    assert "Use bounded retries." in payload
    assert request.memory == ["Use bounded retries."]


def test_openai_agents_client_coerces_dict_final_output_to_schema() -> None:
    client = OpenAIAgentsSDKClient(model="gpt-5.2")

    output = client.coerce_output(
        {
            "summary": "Plan",
            "tasks": [
                {
                    "kind": TaskKind.CODING.value,
                    "title": "Code",
                    "description": "Implement code.",
                    "depends_on": [],
                }
            ],
        },
        PlannerOutput,
    )

    assert output.tasks[0].kind is TaskKind.CODING


def test_openai_agents_client_retries_invalid_structured_output() -> None:
    asyncio.run(_assert_openai_agents_client_retries_invalid_structured_output())


async def _assert_openai_agents_client_retries_invalid_structured_output() -> None:
    calls = []

    async def runner(*, agent_name, instructions, model, output_type, rendered_input):
        calls.append((agent_name, model, rendered_input))
        if len(calls) == 1:
            return {"summary": "bad", "tasks": [{"kind": "coding", "title": "Missing description"}]}
        return {
            "summary": "Plan",
            "tasks": [
                {
                    "kind": "coding",
                    "title": "Code",
                    "description": "Implement code.",
                    "depends_on": [],
                }
            ],
        }

    client = OpenAIAgentsSDKClient(model="gpt-5.2", runner=runner, max_output_retries=2)

    output = await client.plan(AgentInput(workflow_id=uuid4(), objective="Plan"))

    assert output.summary == "Plan"
    assert len(calls) == 2


def test_openai_agents_client_raises_typed_error_after_retry_exhaustion() -> None:
    async def run() -> None:
        async def runner(**kwargs):
            return {"summary": "bad", "tasks": [{"kind": "coding", "title": "Missing description"}]}

        client = OpenAIAgentsSDKClient(model="gpt-5.2", runner=runner, max_output_retries=1)
        await client.plan(AgentInput(workflow_id=uuid4(), objective="Plan"))

    with pytest.raises(AgentOutputValidationError):
        asyncio.run(run())


def test_openai_agents_client_uses_per_agent_model_config() -> None:
    asyncio.run(_assert_openai_agents_client_uses_per_agent_model_config())


async def _assert_openai_agents_client_uses_per_agent_model_config() -> None:
    models = []

    async def runner(**kwargs):
        models.append(kwargs["model"])
        return {
            "summary": "Plan",
            "tasks": [
                {
                    "kind": "coding",
                    "title": "Code",
                    "description": "Implement code.",
                    "depends_on": [],
                }
            ],
        }

    client = OpenAIAgentsSDKClient(
        model_config=AgentModelConfig(
            planner_model="planner-model",
            coder_model="coder-model",
            tester_model="tester-model",
            reviewer_model="reviewer-model",
        ),
        runner=runner,
    )

    await client.plan(AgentInput(workflow_id=uuid4(), objective="Plan"))

    assert models == ["planner-model"]
