from __future__ import annotations

from enum import StrEnum


class WorkflowStatus(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskKind(StrEnum):
    PLANNING = "planning"
    CODING = "coding"
    TESTING = "testing"
    REVIEW = "review"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    FEEDBACK_FIX = "feedback_fix"
    PULL_REQUEST = "pull_request"


class TaskStatus(StrEnum):
    PENDING = "pending"
    BLOCKED = "blocked"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REQUIRES_FIXES = "requires_fixes"
    CANCELLED = "cancelled"


class AgentType(StrEnum):
    PLANNER = "planner"
    CODER = "coder"
    TESTER = "tester"
    REVIEWER = "reviewer"
    DOCUMENTATION = "documentation"


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_FIXES = "request_fixes"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ArtifactKind(StrEnum):
    DIFF = "diff"
    TEST_REPORT = "test_report"
    LOG = "log"
    DOCUMENT = "document"
    PATCH = "patch"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
