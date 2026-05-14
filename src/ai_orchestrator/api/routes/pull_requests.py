from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ai_orchestrator.api.deps import get_pull_request_service
from ai_orchestrator.application.git.pull_requests import PullRequestService
from ai_orchestrator.interfaces.git import PullRequestState

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


@router.get("/{number}", response_model=PullRequestStatusResponse)
async def get_pull_request_status(
    number: int,
    pull_requests: PullRequestService = Depends(get_pull_request_service),
) -> PullRequestStatusResponse:
    status = await pull_requests.get_pull_request_status(number)
    return PullRequestStatusResponse.model_validate(status)
