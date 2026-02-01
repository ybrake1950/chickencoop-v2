"""Coverage improvement tests for src/security/auth.py (73% -> 80%+)."""

import time
from unittest.mock import patch

import pytest

from src.security.auth import TokenValidator, AuthenticationMiddleware


class TestTokenRefresh:
    def test_refresh_valid_token(self):
        validator = TokenValidator(secret_key="test-secret")
        token = validator.generate_token("user1")
        new_token = validator.refresh_token(token)
        assert new_token is not None
        assert new_token != token
        result = validator.validate_token(new_token)
        assert result.authenticated is True

    def test_refresh_expired_token_with_valid_signature(self):
        validator = TokenValidator(secret_key="test-secret", token_expiry_seconds=1)
        token = validator.generate_token("user1")
        # Mock time to make token expired
        with patch("src.security.auth.time.time", return_value=time.time() + 10):
            new_token = validator.refresh_token(token)
        assert new_token is not None

    def test_refresh_invalid_signature_returns_none(self):
        validator = TokenValidator(secret_key="test-secret")
        token = validator.generate_token("user1")
        # Tamper with signature
        parts = token.split(".")
        if len(parts) == 2:
            tampered = parts[0] + ".invalidsig"
            result = validator.refresh_token(tampered)
            assert result is None

    def test_refresh_invalid_format_returns_none(self):
        validator = TokenValidator(secret_key="test-secret")
        result = validator.refresh_token("no_dot_token")
        assert result is None

    def test_refresh_corrupted_payload_returns_none(self):
        validator = TokenValidator(secret_key="test-secret")
        result = validator.refresh_token("not_base64!!!.fakesig")
        assert result is None


class TestAuthMiddlewareCoverage:
    def test_is_protected_returns_true(self):
        middleware = AuthenticationMiddleware(
            token_validator=TokenValidator(secret_key="test"),
            protected_paths=["/api/data"],
        )
        assert middleware.is_protected("/api/data") is True

    def test_is_protected_returns_false(self):
        middleware = AuthenticationMiddleware(
            token_validator=TokenValidator(secret_key="test"),
            protected_paths=["/api/data"],
        )
        assert middleware.is_protected("/public") is False
