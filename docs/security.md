# Security

## Tool Permissions

Tool execution is policy mediated. A sandbox command is valid only when the executable is allowed by the active `SandboxPolicy`.

## Sandbox Isolation

Default sandbox posture:

- no secrets mounted
- network disabled
- readonly root filesystem
- memory limit
- CPU limit
- command timeout
- explicit allowlist for commands
- explicit workspace mount required

## Approval Gates

Production deployments should require approval before:

- opening external pull requests
- pushing branches
- enabling sandbox network access
- running privileged tools
- accessing private dependency registries

The application layer includes `ApprovalService`, `ApprovalGate`, and repository adapters so sensitive actions can be represented as explicit pending/approved/rejected records instead of hidden control flow.

Pull request creation is blocked by `PullRequestService` until the referenced approval gate is approved.

Agent-requested tools are mediated by `ToolExecutionService`; disallowed tools fail before sandbox execution, and sandbox execution still enforces command allowlists and workspace mount requirements.

## Reviewer Checks

Reviewer agents must check:

- architecture consistency
- typing
- style
- security
- performance
- hallucinated APIs
- broken imports
- test coverage
