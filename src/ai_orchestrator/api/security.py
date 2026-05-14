from __future__ import annotations

import hmac


class ApiAuthError(PermissionError):
    """Raised when API authentication fails."""


def verify_bearer_token(*, configured_token: str | None, authorization: str | None) -> None:
    if not configured_token:
        return
    prefix = "Bearer "
    if authorization is None or not authorization.startswith(prefix):
        raise ApiAuthError("Missing bearer token.")
    supplied = authorization.removeprefix(prefix)
    if not hmac.compare_digest(configured_token, supplied):
        raise ApiAuthError("Invalid bearer token.")
