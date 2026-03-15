"""Unit tests for the JWT security / auth layer.

``get_current_user_from_request`` is the single entry point that validates
every incoming request.  We test it with mocked HTTP requests and mocked
JWKS / token-decode logic so no Keycloak server is needed.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.security import decode_token, get_current_user_from_request


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_request(authorization: str | None) -> MagicMock:
    """Build a minimal fake FastAPI Request with a controllable header."""
    request = MagicMock()
    headers: dict[str, str] = {}
    if authorization is not None:
        headers["Authorization"] = authorization
    request.headers = headers
    return request


_VALID_PAYLOAD = {
    "sub": "test-user-id",
    "preferred_username": "testuser",
    "email": "test@example.com",
    "iss": "http://keycloak/realms/master",
    "exp": 9999999999,
}


# ---------------------------------------------------------------------------
# get_current_user_from_request
# ---------------------------------------------------------------------------

class TestGetCurrentUserFromRequest:
    async def test_missing_header_raises_401(self):
        request = _make_request(None)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(request)
        assert exc_info.value.status_code == 401

    async def test_empty_authorization_raises_401(self):
        request = _make_request("")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(request)
        assert exc_info.value.status_code == 401

    async def test_non_bearer_scheme_raises_401(self):
        request = _make_request("Basic dXNlcjpwYXNz")
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user_from_request(request)
        assert exc_info.value.status_code == 401

    async def test_valid_bearer_token_returns_payload(self):
        request = _make_request("Bearer valid.jwt.token")
        with patch(
            "app.core.security.decode_token",
            new=AsyncMock(return_value=_VALID_PAYLOAD),
        ):
            result = await get_current_user_from_request(request)
        assert result["sub"] == "test-user-id"
        assert result["preferred_username"] == "testuser"

    async def test_invalid_token_raises_401(self):
        from fastapi import HTTPException

        request = _make_request("Bearer bad.token")
        with patch(
            "app.core.security.decode_token",
            new=AsyncMock(side_effect=HTTPException(status_code=401, detail="Invalid token")),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user_from_request(request)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------

class TestDecodeToken:
    async def test_invalid_token_raises_401(self):
        """Verify decode_token raises HTTPException(401) on bad JWT."""
        with patch(
            "app.core.security._get_jwks",
            new=AsyncMock(return_value={"keys": []}),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await decode_token("this.is.not.a.valid.jwt")
        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    async def test_valid_token_returns_claims(self):
        """Verify decode_token returns claims on a good token."""
        mock_jwks = {"keys": [{"kid": "k1"}]}
        with patch(
            "app.core.security._get_jwks",
            new=AsyncMock(return_value=mock_jwks),
        ):
            with patch("app.core.security.jwt.decode", return_value=_VALID_PAYLOAD):
                result = await decode_token("header.payload.signature")
        assert result["sub"] == "test-user-id"

    async def test_jwks_fetch_failure_raises(self):
        """Network errors propagate as 5xx from httpx, not swallowed."""
        import httpx

        with patch(
            "app.core.security._get_jwks",
            new=AsyncMock(side_effect=httpx.ConnectError("unreachable")),
        ):
            with pytest.raises(httpx.ConnectError):
                await decode_token("any.jwt.token")
