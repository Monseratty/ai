from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai_orchestrator.api.deps import get_pull_request_service
from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.interfaces.git import CheckRunConclusion, CheckRunStatus, PullRequestState

router = APIRouter(prefix="/pull-requests", tags=["pull-requests"])


class PullRequestStatusResponse(BaseModel):
    number: int
    url: str
    state: PullRequestState
    is_draft: bool
    is_merged: bool
    head_ref: str
    base_ref: str
    head_sha: str | None = None


class ReportCheckRunRequest(BaseModel):
    name: str = Field(min_length=1)
    head_sha: str = Field(min_length=1)
    status: CheckRunStatus
    conclusion: CheckRunConclusion | None = None
    summary: str = Field(min_length=1)
    details_url: str | None = None


class CheckRunResponse(BaseModel):
    provider_id: str
    url: str


@router.post("/check-runs", response_model=CheckRunResponse, status_code=202)
async def report_check_run(
    request: ReportCheckRunRequest,
    pull_requests: PullRequestService = Depends(get_pull_request_service),
) -> CheckRunResponse:
    result = await pull_requests.report_check_run(
        name=request.name,
        head_sha=request.head_sha,
        status=request.status,
        conclusion=request.conclusion,
        summary=request.summary,
        details_url=request.details_url,
    )
    return CheckRunResponse.model_validate(result)


@router.get("/{number}", response_model=PullRequestStatusResponse)
async def get_pull_request_status(
    number: int,
    pull_requests: PullRequestService = Depends(get_pull_request_service),
) -> PullRequestStatusResponse:
    status = await pull_requests.get_pull_request_status(number)
    return PullRequestStatusResponse.model_validate(status)
