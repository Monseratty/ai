from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai_orchestrator.application.orchestrator.service import OrchestratorService
from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.application.sandbox.validation import SandboxValidationService
from ai_orchestrator.application.tools.execution import ToolExecutionService
from ai_orchestrator.application.tools.permissions import ToolPermissionPolicy
from ai_orchestrator.application.agents.config import AgentModelConfig
from ai_orchestrator.application.git.branching import BranchNamingPolicy
from ai_orchestrator.config.settings import Settings
from ai_orchestrator.infrastructure.artifacts.filesystem import FilesystemArtifactStore
from ai_orchestrator.infrastructure.db.session import create_session_factory
from ai_orchestrator.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork, unit_of_work
from ai_orchestrator.infrastructure.openai.agents_sdk_client import OpenAIAgentsSDKClient
from ai_orchestrator.infrastructure.queue.celery_queue import CeleryTaskQueue
from ai_orchestrator.infrastructure.telemetry.logging import StructuredLoggingTelemetry
from ai_orchestrator.infrastructure.telemetry.opentelemetry import OpenTelemetryAdapter
from ai_orchestrator.infrastructure.git.composite import CompositeGitService
from ai_orchestrator.infrastructure.git.github_pr import GitHubPullRequestProvider
from ai_orchestrator.infrastructure.git.gitpython_repo import GitPythonService
from ai_orchestrator.infrastructure.sandbox.docker_executor import DockerSandboxExecutor
from ai_orchestrator.infrastructure.sandbox.run_service import SandboxRunService
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspaceManager
from ai_orchestrator.interfaces.sandbox import SandboxPolicy
from ai_orchestrator.infrastructure.testing.fakes import (
    FakeAgentClient,
    InMemoryArtifactRepository,
    InMemoryApprovalRepository,
    InMemoryExecutionEventRepository,
    InMemoryTaskRepository,
    InMemoryWorkflowRepository,
)
from ai_orchestrator.domain.enums import AgentType, ReviewDecision, TaskKind


class TestingUnitOfWork:
    def __init__(self) -> None:
        self.workflows = InMemoryWorkflowRepository()
        self.tasks = InMemoryTaskRepository()
        self.artifacts = InMemoryArtifactRepository()
        self.approvals = InMemoryApprovalRepository()
        self.execution_events = InMemoryExecutionEventRepository()


class CompositionRoot:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self._session_factory = None
        self._memory_unit = TestingUnitOfWork() if settings.state_backend == "memory" else None
        self.queue = CeleryTaskQueue()
        self.artifact_store = FilesystemArtifactStore(settings.artifact_root)
        self.agent_client = self._create_agent_client(settings)
        self.telemetry = self._create_telemetry(settings)
        self.git = self._create_git_service(settings)
        self.workspace_manager = SandboxWorkspaceManager(
            workspace_root=settings.sandbox_workspace_root
        )
        self.sandbox = SandboxRunService(
            executor=DockerSandboxExecutor(),
            base_policy=SandboxPolicy(
                image=settings.sandbox_image,
                timeout_seconds=settings.sandbox_timeout_seconds,
                memory=settings.sandbox_memory,
                cpus=settings.sandbox_cpus,
                allowed_commands=settings.sandbox_allowed_commands,
            ),
        )
        self.sandbox_validation = SandboxValidationService(runner=self.sandbox)
        self.tool_permission_policy = self._create_tool_permission_policy(settings)
        self.tool_executor = ToolExecutionService(
            runner=self.sandbox,
            allowed_tools=settings.sandbox_allowed_commands,
            permission_policy=self.tool_permission_policy,
        )

    @property
    def session_factory(self):
        if self._session_factory is None:
            self._session_factory = create_session_factory(self.settings.database_url)
        return self._session_factory

    @asynccontextmanager
    async def unit(self) -> AsyncIterator[SqlAlchemyUnitOfWork | TestingUnitOfWork]:
        if self._memory_unit is not None:
            yield self._memory_unit
            return
        if self.settings.state_backend != "postgres":
            raise ValueError(f"Unsupported state backend: {self.settings.state_backend}")
        async with unit_of_work(self.session_factory) as uow:
            yield uow

    @asynccontextmanager
    async def orchestrator(self) -> AsyncIterator[OrchestratorService]:
        async with self.unit() as uow:
            yield self.orchestrator_for_unit_of_work(uow)

    def orchestrator_for_unit_of_work(
        self, uow: SqlAlchemyUnitOfWork | TestingUnitOfWork
    ) -> OrchestratorService:
        return OrchestratorService(
            workflows=uow.workflows,
            tasks=uow.tasks,
            artifacts=uow.artifacts,
            queue=self.queue,
            agents=self.agent_client,
            telemetry=self.telemetry,
            execution_events=uow.execution_events,
            artifact_store=self.artifact_store,
            git=self.git,
            workspace_manager=self.workspace_manager,
            repo_path=self.settings.repo_path,
            tool_executor=self.tool_executor,
            branch_naming=BranchNamingPolicy(prefix=self.settings.branch_prefix),
        )

    def approval_service_for_unit_of_work(
        self, uow: SqlAlchemyUnitOfWork | TestingUnitOfWork
    ) -> ApprovalService:
        return ApprovalService(uow.approvals)

    def pull_request_service_for_unit_of_work(
        self, uow: SqlAlchemyUnitOfWork | TestingUnitOfWork
    ) -> PullRequestService:
        if self.git is None:
            raise RuntimeError("Git integration is disabled. Set AIO_GIT_ENABLED=true.")
        return PullRequestService(
            git=self.git,
            approvals=self.approval_service_for_unit_of_work(uow),
        )

    def testing_unit_of_work(self) -> TestingUnitOfWork:
        return TestingUnitOfWork()

    def _create_agent_client(self, settings: Settings):
        if settings.agent_backend == "fake":
            return FakeAgentClient(reviewer_decision=ReviewDecision.APPROVE)
        if settings.agent_backend == "openai":
            return OpenAIAgentsSDKClient(
                model_config=AgentModelConfig(
                    planner_model=settings.planner_model or settings.openai_model,
                    coder_model=settings.coder_model or settings.openai_model,
                    tester_model=settings.tester_model or settings.openai_model,
                    reviewer_model=settings.reviewer_model or settings.openai_model,
                )
            )
        raise ValueError(f"Unsupported agent backend: {settings.agent_backend}")

    def _create_git_service(self, settings: Settings):
        if not settings.git_enabled:
            return None
        local = GitPythonService(settings.repo_path)
        if settings.pull_request_provider == "local":
            return local
        if settings.pull_request_provider == "github":
            if settings.github_repository is None or settings.github_token is None:
                raise ValueError(
                    "GitHub pull request provider requires github_repository and github_token."
                )
            return CompositeGitService(
                local=local,
                pull_requests=GitHubPullRequestProvider(
                    repository_full_name=settings.github_repository,
                    token=settings.github_token,
                ),
            )
        raise ValueError(f"Unsupported pull request provider: {settings.pull_request_provider}")

    def _create_telemetry(self, settings: Settings):
        if settings.telemetry_backend == "logging":
            return StructuredLoggingTelemetry()
        if settings.telemetry_backend == "opentelemetry":
            return OpenTelemetryAdapter()
        raise ValueError(f"Unsupported telemetry backend: {settings.telemetry_backend}")

    def _create_tool_permission_policy(self, settings: Settings) -> ToolPermissionPolicy:
        return ToolPermissionPolicy(
            grants={
                (AgentType.CODER, TaskKind.CODING): set(settings.sandbox_allowed_commands),
                (AgentType.CODER, TaskKind.FEEDBACK_FIX): set(settings.sandbox_allowed_commands),
                (AgentType.TESTER, TaskKind.TESTING): set(settings.sandbox_allowed_commands),
            }
        )
