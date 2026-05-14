from __future__ import annotations

from uuid import UUID
from pathlib import Path
from time import perf_counter

from ai_orchestrator.application.agents.schemas import AgentInput, CoderOutput, TesterOutput
from ai_orchestrator.application.git.branching import BranchNamingPolicy
from ai_orchestrator.application.tools.execution import ToolExecutionService, ToolRequest
from ai_orchestrator.domain.enums import AgentType, ReviewDecision, TaskKind, TaskStatus, WorkflowStatus
from ai_orchestrator.domain.models.artifact import Artifact
from ai_orchestrator.domain.models.execution import ExecutionEvent
from ai_orchestrator.domain.models.review import TaskExecutionResult
from ai_orchestrator.domain.models.snapshot import WorkflowSnapshot
from ai_orchestrator.domain.models.task import Task
from ai_orchestrator.domain.models.workflow import Workflow
from ai_orchestrator.interfaces.agent_client import AgentClient
from ai_orchestrator.interfaces.artifacts import ArtifactStore
from ai_orchestrator.interfaces.git import GitService
from ai_orchestrator.infrastructure.sandbox.workspace import SandboxWorkspaceManager, SandboxWorkspace
from ai_orchestrator.interfaces.repositories import (
    ArtifactRepository,
    ExecutionEventRepository,
    TaskRepository,
    WorkflowRepository,
)
from ai_orchestrator.interfaces.task_queue import TaskQueue
from ai_orchestrator.interfaces.telemetry import Telemetry


class OrchestratorService:
    def __init__(
        self,
        *,
        workflows: WorkflowRepository,
        tasks: TaskRepository,
        artifacts: ArtifactRepository,
        queue: TaskQueue,
        agents: AgentClient,
        telemetry: Telemetry,
        execution_events: ExecutionEventRepository | None = None,
        artifact_store: ArtifactStore | None = None,
        git: GitService | None = None,
        workspace_manager: SandboxWorkspaceManager | None = None,
        repo_path: Path | None = None,
        tool_executor: ToolExecutionService | None = None,
        branch_naming: BranchNamingPolicy | None = None,
        max_feedback_attempts: int = 2,
    ) -> None:
        self._workflows = workflows
        self._tasks = tasks
        self._artifacts = artifacts
        self._queue = queue
        self._agents = agents
        self._telemetry = telemetry
        self._execution_events = execution_events
        self._artifact_store = artifact_store
        self._git = git
        self._workspace_manager = workspace_manager
        self._repo_path = repo_path
        self._tool_executor = tool_executor
        self._branch_naming = branch_naming or BranchNamingPolicy()
        self._max_feedback_attempts = max_feedback_attempts

    async def create_workflow(self, user_task: str) -> Workflow:
        workflow = Workflow(user_task=user_task)
        if self._git is not None:
            branch_name = self._branch_naming.for_workflow(
                workflow_id=workflow.id,
                user_task=user_task,
            )
            await self._git.create_branch(branch_name, base_ref=workflow.base_ref)
            workflow = workflow.model_copy(update={"branch_name": branch_name})
        await self._workflows.add(workflow)
        await self._telemetry.event("workflow.created", {"workflow_id": str(workflow.id)})
        await self._telemetry.increment("workflows.created")
        await self._record_event(workflow.id, None, "workflow.created", {"user_task": user_task})

        planner_output = await self._agents.plan(
            AgentInput(workflow_id=workflow.id, objective=user_task)
        )
        planned_tasks = self._build_tasks(workflow, planner_output.tasks)
        await self._tasks.add_many(planned_tasks)

        ready_tasks = [task for task in planned_tasks if not task.dependency_ids]
        for task in ready_tasks:
            queued = task.with_status(TaskStatus.QUEUED)
            await self._tasks.update(queued)
            await self._queue.enqueue_task(queued.id)

        planned_workflow = workflow.with_status(WorkflowStatus.PLANNED)
        await self._workflows.update(planned_workflow)
        await self._telemetry.event(
            "workflow.planned",
            {"workflow_id": str(workflow.id), "task_count": len(planned_tasks)},
        )
        await self._telemetry.increment("workflows.planned", {"task_count": str(len(planned_tasks))})
        await self._record_event(
            workflow.id,
            None,
            "workflow.planned",
            {"task_count": len(planned_tasks)},
        )
        return planned_workflow

    async def execute_queued_task(self, task_id: UUID) -> TaskExecutionResult | None:
        claimed = await self._tasks.claim_queued(task_id)
        if claimed is None:
            await self._record_event_for_task_id(task_id, "task.claim_skipped", {})
            return None
        return await self._execute_claimed_task(claimed)

    async def execute_task(self, task_id: UUID) -> TaskExecutionResult:
        task = await self._tasks.get(task_id)
        running = task.with_status(TaskStatus.RUNNING)
        await self._tasks.update(running)
        return await self._execute_claimed_task(running)

    async def _execute_claimed_task(self, task: Task) -> TaskExecutionResult:
        started = perf_counter()
        workflow = await self._workflows.get(task.workflow_id)

        try:
            if task.kind is TaskKind.TESTING:
                return await self._execute_testing_task(workflow, task)

            if task.kind not in {TaskKind.CODING, TaskKind.FEEDBACK_FIX}:
                raise ValueError(f"Task kind {task.kind} is not executable by this workflow runner.")

            coder_output = await self._agents.code(
                AgentInput(workflow_id=workflow.id, task_id=task.id, objective=task.description)
            )
            await self._store_agent_artifacts(workflow.id, task.id, coder_output)
            workspace = await self._prepare_workspace_for_task(workflow.id, task.id)
            if not await self._execute_tool_requests(
                workflow.id,
                task.id,
                workspace,
                coder_output.tool_requests,
                agent_type=AgentType.CODER,
                task_kind=task.kind,
            ):
                failed = task.with_status(TaskStatus.FAILED).with_output(
                    {"coder": coder_output.model_dump(mode="json")}
                )
                await self._tasks.update(failed)
                await self._workflows.update(workflow.with_status(WorkflowStatus.FAILED))
                await self._telemetry.increment("tasks.failed", {"reason": "tool"})
                await self._record_event(workflow.id, task.id, "task.tool_failed", {})
                return TaskExecutionResult(
                    task_id=task.id,
                    workflow_id=workflow.id,
                    artifacts_created=len(coder_output.artifacts),
                    summary="Coder tool request failed.",
                )

            tester_output = await self._agents.test(
                AgentInput(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    objective=f"Validate task: {task.description}",
                    artifacts=coder_output.artifacts,
                )
            )
            await self._store_test_artifacts(workflow.id, task.id, tester_output)
            if not await self._execute_tool_requests(
                workflow.id,
                task.id,
                workspace,
                tester_output.tool_requests,
                agent_type=AgentType.TESTER,
                task_kind=TaskKind.TESTING,
            ):
                failed = task.with_status(TaskStatus.FAILED).with_output(
                    {
                        "coder": coder_output.model_dump(mode="json"),
                        "tester": tester_output.model_dump(mode="json"),
                    }
                )
                await self._tasks.update(failed)
                await self._workflows.update(workflow.with_status(WorkflowStatus.FAILED))
                await self._telemetry.increment("tasks.failed", {"reason": "tool"})
                await self._record_event(workflow.id, task.id, "task.tool_failed", {})
                return TaskExecutionResult(
                    task_id=task.id,
                    workflow_id=workflow.id,
                    artifacts_created=len(coder_output.artifacts) + len(tester_output.artifacts),
                    summary="Tester tool request failed.",
                )

            reviewer_output = await self._agents.review(
                AgentInput(
                    workflow_id=workflow.id,
                    task_id=task.id,
                    objective="Review completed coding and test artifacts.",
                    artifacts=[*coder_output.artifacts, *tester_output.artifacts],
                )
            )

            if tester_output.passed and reviewer_output.decision is ReviewDecision.APPROVE:
                succeeded = task.with_status(TaskStatus.SUCCEEDED).with_output(
                    {
                        "coder": coder_output.model_dump(mode="json"),
                        "tester": tester_output.model_dump(mode="json"),
                        "reviewer": reviewer_output.model_dump(mode="json"),
                    }
                )
                await self._tasks.update(succeeded)
                await self._advance_workflow_after_task_success(workflow.id)
                await self._telemetry.event("task.approved", {"task_id": str(task.id)})
                await self._telemetry.increment("tasks.approved", {"kind": task.kind.value})
                await self._record_event(
                    workflow.id, task.id, "task.approved", {"task_id": str(task.id)}
                )
                return TaskExecutionResult(
                    task_id=task.id,
                    workflow_id=workflow.id,
                    review_decision=reviewer_output.decision,
                    artifacts_created=len(coder_output.artifacts) + len(tester_output.artifacts),
                    summary="Task approved by reviewer.",
                )

            requires_fixes = task.with_status(TaskStatus.REQUIRES_FIXES).with_output(
                {
                    "coder": coder_output.model_dump(mode="json"),
                    "tester": tester_output.model_dump(mode="json"),
                    "reviewer": reviewer_output.model_dump(mode="json"),
                }
            )
            await self._tasks.update(requires_fixes)
            feedback_task = await self._create_feedback_task(
                requires_fixes, reviewer_output.required_fixes
            )
            await self._telemetry.event(
                "task.requires_fixes",
                {"task_id": str(task.id), "feedback_task_id": str(feedback_task.id)},
            )
            await self._telemetry.increment("tasks.requires_fixes", {"kind": task.kind.value})
            await self._record_event(
                workflow.id,
                task.id,
                "task.requires_fixes",
                {"feedback_task_id": str(feedback_task.id)},
            )
            return TaskExecutionResult(
                task_id=task.id,
                workflow_id=workflow.id,
                review_decision=reviewer_output.decision,
                created_feedback_task_id=feedback_task.id,
                artifacts_created=len(coder_output.artifacts) + len(tester_output.artifacts),
                summary="Reviewer requested fixes.",
            )
        finally:
            await self._telemetry.observe(
                "tasks.execution_duration_ms",
                (perf_counter() - started) * 1000,
                {"kind": task.kind.value},
            )

    async def _execute_testing_task(self, workflow: Workflow, task: Task) -> TaskExecutionResult:
        workspace = await self._prepare_workspace_for_task(workflow.id, task.id)
        tester_output = await self._agents.test(
            AgentInput(workflow_id=workflow.id, task_id=task.id, objective=task.description)
        )
        await self._store_test_artifacts(workflow.id, task.id, tester_output)
        tools_passed = await self._execute_tool_requests(
            workflow.id,
            task.id,
            workspace,
            tester_output.tool_requests,
            agent_type=AgentType.TESTER,
            task_kind=task.kind,
        )
        if not tools_passed:
            tester_output = tester_output.model_copy(update={"passed": False})
        status = TaskStatus.SUCCEEDED if tester_output.passed else TaskStatus.FAILED
        completed = task.with_status(status).with_output({"tester": tester_output.model_dump(mode="json")})
        await self._tasks.update(completed)
        if tester_output.passed:
            await self._advance_workflow_after_task_success(workflow.id)
            await self._record_event(workflow.id, task.id, "task.test_passed", {})
        else:
            await self._workflows.update(workflow.with_status(WorkflowStatus.FAILED))
            await self._record_event(workflow.id, task.id, "task.test_failed", {})
        return TaskExecutionResult(
            task_id=task.id,
            workflow_id=workflow.id,
            review_decision=None,
            artifacts_created=len(tester_output.artifacts),
            summary=tester_output.summary,
        )

    async def get_workflow_snapshot(self, workflow_id: UUID) -> WorkflowSnapshot:
        workflow = await self._workflows.get(workflow_id)
        tasks = await self._tasks.list_by_workflow(workflow_id)
        return WorkflowSnapshot(workflow=workflow, tasks=tasks)

    async def get_task(self, task_id: UUID) -> Task:
        return await self._tasks.get(task_id)

    async def list_workflows(self, limit: int = 50) -> list[Workflow]:
        return await self._workflows.list_recent(limit=limit)

    async def list_workflow_artifacts(self, workflow_id: UUID) -> list[Artifact]:
        return await self._artifacts.list_by_workflow(workflow_id)

    async def list_execution_history(self, workflow_id: UUID) -> list[ExecutionEvent]:
        if self._execution_events is None:
            return []
        return await self._execution_events.list_by_workflow(workflow_id)

    async def retry_task(self, task_id: UUID) -> Task:
        task = await self._tasks.get(task_id)
        if task.status not in {TaskStatus.FAILED, TaskStatus.REQUIRES_FIXES, TaskStatus.CANCELLED}:
            raise ValueError(f"Task {task_id} is not retryable from status {task.status}.")
        if task.attempt_count >= task.max_attempts:
            raise ValueError(f"Task {task_id} exceeded max attempts.")
        retried = task.with_status(TaskStatus.QUEUED)
        await self._tasks.update(retried)
        await self._queue.enqueue_task(retried.id)
        await self._record_event(task.workflow_id, task.id, "task.retry_queued", {})
        workflow = await self._workflows.get(task.workflow_id)
        if workflow.status in {WorkflowStatus.FAILED, WorkflowStatus.CANCELLED}:
            await self._workflows.update(workflow.with_status(WorkflowStatus.IN_PROGRESS))
        return retried

    async def cancel_workflow(self, workflow_id: UUID) -> Workflow:
        workflow = await self._workflows.get(workflow_id)
        tasks = await self._tasks.list_by_workflow(workflow_id)
        terminal = {TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CANCELLED}
        for task in tasks:
            if task.status not in terminal:
                await self._tasks.update(task.with_status(TaskStatus.CANCELLED))
        cancelled = workflow.with_status(WorkflowStatus.CANCELLED)
        await self._workflows.update(cancelled)
        await self._record_event(workflow_id, None, "workflow.cancelled", {})
        return cancelled

    def _build_tasks(self, workflow: Workflow, planned_tasks: list) -> list[Task]:
        tasks: list[Task] = []
        for planned in planned_tasks:
            tasks.append(
                Task(
                    workflow_id=workflow.id,
                    kind=planned.kind,
                    title=planned.title,
                    description=planned.description,
                    status=TaskStatus.BLOCKED if planned.depends_on else TaskStatus.PENDING,
                    input={"planned_task": planned.model_dump(mode="json")},
                )
            )

        for index, planned in enumerate(planned_tasks):
            dependency_ids = [tasks[dependency_index].id for dependency_index in planned.depends_on]
            if dependency_ids:
                tasks[index] = tasks[index].model_copy(update={"dependency_ids": dependency_ids})
        return tasks

    async def _store_agent_artifacts(
        self, workflow_id: UUID, task_id: UUID, output: CoderOutput
    ) -> None:
        for artifact in output.artifacts:
            await self._artifacts.add(await self._materialize_artifact(workflow_id, task_id, artifact))

    async def _store_test_artifacts(
        self, workflow_id: UUID, task_id: UUID, output: TesterOutput
    ) -> None:
        for artifact in output.artifacts:
            await self._artifacts.add(await self._materialize_artifact(workflow_id, task_id, artifact))

    async def _materialize_artifact(
        self, workflow_id: UUID, task_id: UUID, artifact: dict
    ) -> Artifact:
        if self._artifact_store is not None and "content" in artifact:
            return await self._artifact_store.write_text(
                workflow_id=workflow_id,
                task_id=task_id,
                kind=artifact.get("kind", "log"),
                filename=artifact.get("filename", "artifact.txt"),
                content=artifact["content"],
            )
        return Artifact(
            workflow_id=workflow_id,
            task_id=task_id,
            kind=artifact.get("kind", "log"),
            path=artifact.get("path"),
            metadata=artifact,
        )

    async def _prepare_workspace_for_task(
        self, workflow_id: UUID, task_id: UUID
    ) -> SandboxWorkspace | None:
        if self._workspace_manager is None or self._repo_path is None:
            return None
        return self._workspace_manager.prepare_workspace(
            repo_path=self._repo_path,
            workflow_id=str(workflow_id),
            task_id=str(task_id),
        )

    async def _execute_tool_requests(
        self,
        workflow_id: UUID,
        task_id: UUID,
        workspace: SandboxWorkspace | None,
        tool_requests: list[dict],
        agent_type: AgentType,
        task_kind: TaskKind,
    ) -> bool:
        if not tool_requests:
            return True
        if self._tool_executor is None or workspace is None:
            raise RuntimeError("Tool requests require configured tool executor and sandbox workspace.")
        all_ok = True
        for request_payload in tool_requests:
            result = await self._tool_executor.execute(
                workspace=workspace,
                request=ToolRequest.model_validate(request_payload),
                agent_type=agent_type,
                task_kind=task_kind,
            )
            await self._artifacts.add(
                Artifact(
                    workflow_id=workflow_id,
                    task_id=task_id,
                    kind="tool_result",
                    metadata=result.model_dump(mode="json"),
                )
            )
            all_ok = all_ok and result.ok
        return all_ok

    async def _create_feedback_task(self, task: Task, required_fixes: list[str]) -> Task:
        feedback_task = Task(
            workflow_id=task.workflow_id,
            parent_task_id=task.id,
            kind=TaskKind.FEEDBACK_FIX,
            title=f"Fix reviewer findings for {task.title}",
            description="\n".join(required_fixes) or "Address reviewer findings.",
            status=TaskStatus.QUEUED,
            max_attempts=self._max_feedback_attempts,
            input={"reviewer_required_fixes": required_fixes},
        )
        await self._tasks.add(feedback_task)
        await self._queue.enqueue_task(feedback_task.id)
        return feedback_task

    async def _advance_workflow_after_task_success(self, workflow_id: UUID) -> None:
        workflow = await self._workflows.get(workflow_id)
        workflow_tasks = await self._tasks.list_by_workflow(workflow_id)
        succeeded_task_ids = {
            task.id for task in workflow_tasks if task.status is TaskStatus.SUCCEEDED
        }

        for task in workflow_tasks:
            if task.status is not TaskStatus.BLOCKED:
                continue
            if all(dependency_id in succeeded_task_ids for dependency_id in task.dependency_ids):
                queued = task.with_status(TaskStatus.QUEUED)
                await self._tasks.update(queued)
                await self._queue.enqueue_task(queued.id)

        refreshed_tasks = await self._tasks.list_by_workflow(workflow_id)
        terminal_success = all(task.status is TaskStatus.SUCCEEDED for task in refreshed_tasks)
        next_status = WorkflowStatus.SUCCEEDED if terminal_success else WorkflowStatus.IN_PROGRESS
        await self._workflows.update(workflow.with_status(next_status))
        if terminal_success:
            try:
                await self._commit_successful_workflow(workflow, refreshed_tasks)
            except Exception as exc:
                if self._git is not None:
                    await self._git.rollback()
                await self._workflows.update(workflow.with_status(WorkflowStatus.FAILED))
                await self._record_event(
                    workflow.id,
                    None,
                    "git.commit_failed",
                    {"error": str(exc)},
                )

    async def _record_event(
        self,
        workflow_id: UUID,
        task_id: UUID | None,
        event_type: str,
        payload: dict,
    ) -> None:
        if self._execution_events is None:
            return
        await self._execution_events.add(
            ExecutionEvent(
                workflow_id=workflow_id,
                task_id=task_id,
                event_type=event_type,
                payload=payload,
            )
        )

    async def _record_event_for_task_id(
        self,
        task_id: UUID,
        event_type: str,
        payload: dict,
    ) -> None:
        if self._execution_events is None:
            return
        task = await self._tasks.get(task_id)
        await self._record_event(task.workflow_id, task_id, event_type, payload)

    async def _commit_successful_workflow(self, workflow: Workflow, tasks: list[Task]) -> None:
        if self._git is None:
            return
        changed_files: list[str] = []
        for task in tasks:
            if task.output is None:
                continue
            coder_output = task.output.get("coder")
            if not coder_output:
                continue
            changed_files.extend(coder_output.get("changed_files", []))
        deduplicated = list(dict.fromkeys(changed_files))
        if not deduplicated:
            return
        await self._git.commit(f"Complete workflow: {workflow.user_task}", deduplicated)
        await self._record_event(workflow.id, None, "git.committed", {"paths": deduplicated})
