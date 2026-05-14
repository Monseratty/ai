from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ai_orchestrator.api.deps import get_approval_service
from ai_orchestrator.application.approvals.service import ApprovalService
from ai_orchestrator.domain.enums import ApprovalStatus

router = APIRouter(prefix="/approvals", tags=["approvals"])


class CreateApprovalRequest(BaseModel):
    workflow_id: UUID
    gate_type: str = Field(min_length=1)
    requested_action: dict


class ApprovalResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    gate_type: str
    status: ApprovalStatus
    requested_action: dict
    decided_by: str | None


class ApprovalDecisionRequest(BaseModel):
    decided_by: str = Field(min_length=1)


@router.post("", response_model=ApprovalResponse, status_code=202)
async def request_approval(
    request: CreateApprovalRequest,
    approvals: ApprovalService = Depends(get_approval_service),
) -> ApprovalResponse:
    gate = await approvals.request_approval(
        workflow_id=request.workflow_id,
        gate_type=request.gate_type,
        requested_action=request.requested_action,
    )
    return _approval_response(gate)


@router.get("/workflow/{workflow_id}", response_model=list[ApprovalResponse])
async def list_workflow_approvals(
    workflow_id: UUID,
    approvals: ApprovalService = Depends(get_approval_service),
) -> list[ApprovalResponse]:
    return [_approval_response(gate) for gate in await approvals.list_for_workflow(workflow_id)]


@router.post("/{gate_id}/approve", response_model=ApprovalResponse)
async def approve_gate(
    gate_id: UUID,
    request: ApprovalDecisionRequest,
    approvals: ApprovalService = Depends(get_approval_service),
) -> ApprovalResponse:
    return _approval_response(await approvals.approve(gate_id, request.decided_by))


@router.post("/{gate_id}/reject", response_model=ApprovalResponse)
async def reject_gate(
    gate_id: UUID,
    request: ApprovalDecisionRequest,
    approvals: ApprovalService = Depends(get_approval_service),
) -> ApprovalResponse:
    return _approval_response(await approvals.reject(gate_id, request.decided_by))


def _approval_response(gate) -> ApprovalResponse:
    return ApprovalResponse(
        id=gate.id,
        workflow_id=gate.workflow_id,
        gate_type=gate.gate_type,
        status=gate.status,
        requested_action=gate.requested_action,
        decided_by=gate.decided_by,
    )
