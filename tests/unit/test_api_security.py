from __future__ import annotations

import pytest

from ai_orchestrator.api.security import ApiAuthError, verify_bearer_token


def test_verify_bearer_token_allows_requests_when_no_token_configured() -> None:
    verify_bearer_token(configured_token=None, authorization=None)


def test_verify_bearer_token_requires_matching_bearer_token_when_configured() -> None:
    verify_bearer_token(configured_token="secret", authorization="Bearer secret")

    with pytest.raises(ApiAuthError):
        verify_bearer_token(configured_token="secret", authorization=None)

    with pytest.raises(ApiAuthError):
        verify_bearer_token(configured_token="secret", authorization="Bearer wrong")
