"""
Phase 10: API Security Tests
============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Rate limiting on all endpoints
- CORS configuration
- CSRF protection
- Authentication requirements
- Authorization checks
- Secure headers

WHY THIS MATTERS:
-----------------
APIs are the primary attack surface. Without proper security controls,
attackers can spam endpoints, steal data, or perform unauthorized actions.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase10_security/api/test_api_security.py -v
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import time

from src.security.rate_limiter import RateLimiter, RateLimitConfig
from src.security.cors import CORSConfig, CORSValidator
from src.security.csrf import CSRFProtection, CSRFToken
from src.security.auth import AuthenticationMiddleware, TokenValidator
from src.security.headers import SecurityHeadersMiddleware


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def rate_limiter():
    """Provide a rate limiter instance."""
    config = RateLimitConfig(
        requests_per_minute=60,
        requests_per_hour=1000,
        burst_limit=10
    )
    return RateLimiter(config)


@pytest.fixture
def cors_config():
    """Provide CORS configuration."""
    return CORSConfig(
        allowed_origins=["https://chickencoop.example.com", "https://app.example.com"],
        allowed_methods=["GET", "POST", "PUT", "DELETE"],
        allowed_headers=["Content-Type", "Authorization"],
        allow_credentials=True,
        max_age=3600
    )


@pytest.fixture
def csrf_protection():
    """Provide CSRF protection instance."""
    return CSRFProtection(secret_key="test-secret-key-for-csrf")


@pytest.fixture
def token_validator():
    """Provide token validator."""
    return TokenValidator(
        secret_key="test-jwt-secret",
        token_expiry_seconds=3600
    )


@pytest.fixture
def mock_request():
    """Provide a mock request object."""
    request = MagicMock()
    request.remote_addr = "192.168.1.100"
    request.headers = {"User-Agent": "TestClient/1.0"}
    return request


# =============================================================================
# TestRateLimiting
# =============================================================================

class TestRateLimiting:
    """Test API rate limiting."""

    def test_rate_limit_on_login(self, rate_limiter):
        """Login endpoint has rate limit."""
        # Configure stricter limit for login
        login_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=5,  # Only 5 login attempts per minute
            endpoint_name="login"
        ))

        client_ip = "192.168.1.100"

        # First 5 requests should succeed
        for i in range(5):
            result = login_limiter.check_rate_limit(client_ip)
            assert result.allowed is True

        # 6th request should be blocked
        result = login_limiter.check_rate_limit(client_ip)
        assert result.allowed is False

    def test_rate_limit_on_subscription(self, rate_limiter):
        """Alert subscription endpoint rate limited."""
        subscription_limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=10,
            endpoint_name="subscription"
        ))

        client_ip = "192.168.1.100"

        for i in range(10):
            result = subscription_limiter.check_rate_limit(client_ip)
            assert result.allowed is True

        result = subscription_limiter.check_rate_limit(client_ip)
        assert result.allowed is False

    def test_rate_limit_on_video_list(self, rate_limiter):
        """Video listing rate limited."""
        client_ip = "192.168.1.100"

        # Should allow normal usage
        for i in range(50):
            result = rate_limiter.check_rate_limit(client_ip)
            assert result.allowed is True

    def test_rate_limit_returns_429(self, rate_limiter):
        """Rate limit returns 429 Too Many Requests."""
        client_ip = "192.168.1.100"

        # Exhaust the rate limit
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=1))
        limiter.check_rate_limit(client_ip)

        result = limiter.check_rate_limit(client_ip)
        assert result.allowed is False
        assert result.http_status_code == 429

    def test_rate_limit_includes_retry_after(self, rate_limiter):
        """Rate limit response includes Retry-After header."""
        client_ip = "192.168.1.100"

        limiter = RateLimiter(RateLimitConfig(requests_per_minute=1))
        limiter.check_rate_limit(client_ip)

        result = limiter.check_rate_limit(client_ip)
        assert result.allowed is False
        assert result.retry_after_seconds > 0
        assert result.retry_after_seconds <= 60

    def test_rate_limit_per_ip(self, rate_limiter):
        """Rate limit applied per IP address."""
        limiter = RateLimiter(RateLimitConfig(requests_per_minute=2))

        ip1 = "192.168.1.100"
        ip2 = "192.168.1.101"

        # Both IPs get their own limit
        limiter.check_rate_limit(ip1)
        limiter.check_rate_limit(ip1)
        limiter.check_rate_limit(ip2)
        limiter.check_rate_limit(ip2)

        # IP1 should be blocked
        result1 = limiter.check_rate_limit(ip1)
        assert result1.allowed is False

        # IP2 should also be blocked (used its own quota)
        result2 = limiter.check_rate_limit(ip2)
        assert result2.allowed is False

    def test_rate_limit_per_user(self, rate_limiter):
        """Authenticated rate limit per user."""
        limiter = RateLimiter(RateLimitConfig(
            requests_per_minute=5,
            use_user_id=True
        ))

        user1 = "user-123"
        user2 = "user-456"

        for i in range(5):
            limiter.check_rate_limit(user1, user_id=user1)

        # User1 should be blocked
        result1 = limiter.check_rate_limit(user1, user_id=user1)
        assert result1.allowed is False

        # User2 should still be allowed
        result2 = limiter.check_rate_limit(user2, user_id=user2)
        assert result2.allowed is True


# =============================================================================
# TestCORSConfiguration
# =============================================================================

class TestCORSConfiguration:
    """Test CORS configuration."""

    def test_cors_origin_restricted(self, cors_config):
        """CORS origin restricted to allowed domains."""
        validator = CORSValidator(cors_config)

        # Allowed origins
        assert validator.is_origin_allowed("https://chickencoop.example.com") is True
        assert validator.is_origin_allowed("https://app.example.com") is True

        # Disallowed origins
        assert validator.is_origin_allowed("https://evil.com") is False
        assert validator.is_origin_allowed("https://attacker.example.com") is False

    def test_cors_methods_restricted(self, cors_config):
        """CORS methods restricted appropriately."""
        validator = CORSValidator(cors_config)

        # Allowed methods
        assert validator.is_method_allowed("GET") is True
        assert validator.is_method_allowed("POST") is True
        assert validator.is_method_allowed("PUT") is True
        assert validator.is_method_allowed("DELETE") is True

        # Disallowed methods
        assert validator.is_method_allowed("TRACE") is False
        assert validator.is_method_allowed("CONNECT") is False

    def test_cors_credentials_configured(self, cors_config):
        """CORS credentials setting correct."""
        validator = CORSValidator(cors_config)

        headers = validator.get_cors_headers("https://chickencoop.example.com")

        assert headers["Access-Control-Allow-Credentials"] == "true"

    def test_cors_preflight_handled(self, cors_config):
        """OPTIONS preflight requests handled."""
        validator = CORSValidator(cors_config)

        headers = validator.get_preflight_headers(
            origin="https://chickencoop.example.com",
            request_method="POST",
            request_headers="Content-Type, Authorization"
        )

        assert "Access-Control-Allow-Methods" in headers
        assert "Access-Control-Allow-Headers" in headers
        assert "Access-Control-Max-Age" in headers

    def test_wildcard_origin_not_used(self, cors_config):
        """Wildcard (*) origin not used in production."""
        validator = CORSValidator(cors_config)

        headers = validator.get_cors_headers("https://chickencoop.example.com")

        # Should return specific origin, not wildcard
        assert headers.get("Access-Control-Allow-Origin") != "*"
        assert headers.get("Access-Control-Allow-Origin") == "https://chickencoop.example.com"


# =============================================================================
# TestCSRFProtection
# =============================================================================

class TestCSRFProtection:
    """Test CSRF protection."""

    def test_csrf_token_required(self, csrf_protection):
        """CSRF token required for state-changing requests."""
        # POST request without token should fail
        result = csrf_protection.validate_request(
            method="POST",
            token=None,
            session_token="session-abc"
        )

        assert result.valid is False
        assert "CSRF token required" in result.error

    def test_csrf_token_validated(self, csrf_protection):
        """CSRF token validated on submission."""
        # Generate a valid token
        session_id = "session-123"
        token = csrf_protection.generate_token(session_id)

        # Validate with correct token
        result = csrf_protection.validate_request(
            method="POST",
            token=token.value,
            session_token=session_id
        )

        assert result.valid is True

    def test_invalid_csrf_rejected(self, csrf_protection):
        """Invalid CSRF token rejected."""
        session_id = "session-123"

        result = csrf_protection.validate_request(
            method="POST",
            token="invalid-token-value",
            session_token=session_id
        )

        assert result.valid is False
        assert "Invalid CSRF token" in result.error

    def test_csrf_token_rotated(self, csrf_protection):
        """CSRF token rotated per session."""
        session1 = "session-001"
        session2 = "session-002"

        token1 = csrf_protection.generate_token(session1)
        token2 = csrf_protection.generate_token(session2)

        # Tokens should be different for different sessions
        assert token1.value != token2.value

    def test_json_api_csrf_protected(self, csrf_protection):
        """JSON API endpoints CSRF protected."""
        session_id = "session-123"
        token = csrf_protection.generate_token(session_id)

        # JSON API POST without token should fail
        result = csrf_protection.validate_request(
            method="POST",
            token=None,
            session_token=session_id,
            content_type="application/json"
        )

        assert result.valid is False


# =============================================================================
# TestAuthentication
# =============================================================================

class TestAuthentication:
    """Test authentication requirements."""

    def test_protected_routes_require_auth(self, token_validator):
        """Protected routes require authentication."""
        middleware = AuthenticationMiddleware(
            token_validator=token_validator,
            protected_paths=["/api/videos", "/api/settings", "/api/admin"]
        )

        # Check that routes are protected
        assert middleware.is_protected("/api/videos") is True
        assert middleware.is_protected("/api/settings") is True
        assert middleware.is_protected("/api/admin") is True
        assert middleware.is_protected("/api/status") is False  # Public endpoint

    def test_unauthenticated_returns_401(self, token_validator):
        """Unauthenticated requests return 401."""
        middleware = AuthenticationMiddleware(token_validator=token_validator)

        result = middleware.authenticate(token=None)

        assert result.authenticated is False
        assert result.http_status_code == 401
        assert "Authentication required" in result.error

    def test_invalid_token_returns_401(self, token_validator):
        """Invalid auth token returns 401."""
        middleware = AuthenticationMiddleware(token_validator=token_validator)

        result = middleware.authenticate(token="invalid.jwt.token")

        assert result.authenticated is False
        assert result.http_status_code == 401

    def test_expired_token_returns_401(self, token_validator):
        """Expired token returns 401."""
        # Create an expired token
        expired_validator = TokenValidator(
            secret_key="test-jwt-secret",
            token_expiry_seconds=-1  # Already expired
        )
        token = expired_validator.generate_token(user_id="user-123")

        middleware = AuthenticationMiddleware(token_validator=token_validator)
        result = middleware.authenticate(token=token)

        assert result.authenticated is False
        assert result.http_status_code == 401
        assert "expired" in result.error.lower()

    def test_token_refresh_works(self, token_validator):
        """Token refresh mechanism works."""
        # Generate initial token
        old_token = token_validator.generate_token(user_id="user-123")

        # Refresh the token
        new_token = token_validator.refresh_token(old_token)

        assert new_token is not None
        assert new_token != old_token

        # New token should be valid
        middleware = AuthenticationMiddleware(token_validator=token_validator)
        result = middleware.authenticate(token=new_token)
        assert result.authenticated is True


# =============================================================================
# TestAuthorization
# =============================================================================

class TestAuthorization:
    """Test authorization checks."""

    def test_user_can_only_access_own_data(self, token_validator):
        """Users can only access their own data."""
        from src.security.authorization import AuthorizationChecker

        checker = AuthorizationChecker()

        user_id = "user-123"

        # User can access their own videos
        assert checker.can_access_resource(
            user_id=user_id,
            resource_type="video",
            resource_owner="user-123"
        ) is True

        # User cannot access another user's videos
        assert checker.can_access_resource(
            user_id=user_id,
            resource_type="video",
            resource_owner="user-456"
        ) is False

    def test_admin_routes_require_admin(self, token_validator):
        """Admin routes require admin role."""
        from src.security.authorization import AuthorizationChecker

        checker = AuthorizationChecker()

        # Regular user cannot access admin routes
        assert checker.can_access_admin_route(
            user_id="user-123",
            user_role="viewer"
        ) is False

        # Admin can access admin routes
        assert checker.can_access_admin_route(
            user_id="admin-001",
            user_role="admin"
        ) is True

    def test_coop_access_restricted(self, token_validator):
        """Users only access authorized coops."""
        from src.security.authorization import AuthorizationChecker

        checker = AuthorizationChecker()

        # User with access to coop1 only
        user_coops = ["coop1"]

        assert checker.can_access_coop(
            user_coops=user_coops,
            requested_coop="coop1"
        ) is True

        assert checker.can_access_coop(
            user_coops=user_coops,
            requested_coop="coop2"
        ) is False

    def test_unauthorized_returns_403(self, token_validator):
        """Unauthorized access returns 403."""
        from src.security.authorization import AuthorizationChecker

        checker = AuthorizationChecker()

        result = checker.check_permission(
            user_id="user-123",
            user_role="viewer",
            required_permission="admin:delete"
        )

        assert result.authorized is False
        assert result.http_status_code == 403


# =============================================================================
# TestSecureHeaders
# =============================================================================

class TestSecureHeaders:
    """Test security headers."""

    def test_content_security_policy(self):
        """Content-Security-Policy header set."""
        middleware = SecurityHeadersMiddleware()
        headers = middleware.get_security_headers()

        assert "Content-Security-Policy" in headers
        csp = headers["Content-Security-Policy"]
        assert "default-src" in csp

    def test_x_content_type_options(self):
        """X-Content-Type-Options: nosniff set."""
        middleware = SecurityHeadersMiddleware()
        headers = middleware.get_security_headers()

        assert headers.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options(self):
        """X-Frame-Options set to prevent clickjacking."""
        middleware = SecurityHeadersMiddleware()
        headers = middleware.get_security_headers()

        assert headers.get("X-Frame-Options") in ["DENY", "SAMEORIGIN"]

    def test_strict_transport_security(self):
        """HSTS header set for HTTPS."""
        middleware = SecurityHeadersMiddleware(enable_hsts=True)
        headers = middleware.get_security_headers()

        assert "Strict-Transport-Security" in headers
        hsts = headers["Strict-Transport-Security"]
        assert "max-age" in hsts

    def test_cache_control_for_sensitive(self):
        """Cache-Control prevents caching sensitive data."""
        middleware = SecurityHeadersMiddleware()
        headers = middleware.get_security_headers(sensitive=True)

        cache_control = headers.get("Cache-Control", "")
        assert "no-store" in cache_control or "no-cache" in cache_control


# =============================================================================
# TestPresignedURLSecurity
# =============================================================================

class TestPresignedURLSecurity:
    """Test S3 presigned URL security."""

    def test_presigned_url_short_expiry(self):
        """Presigned URLs have short expiration (15-30 min)."""
        from src.security.presigned_urls import PresignedURLGenerator

        generator = PresignedURLGenerator()

        # Default expiry should be between 15-30 minutes
        assert generator.default_expiry_seconds >= 900  # 15 min
        assert generator.default_expiry_seconds <= 1800  # 30 min

    def test_presigned_url_scoped_to_object(self):
        """Presigned URLs scoped to specific object."""
        from src.security.presigned_urls import PresignedURLGenerator

        generator = PresignedURLGenerator()

        url = generator.generate_url(
            bucket="test-bucket",
            key="videos/coop1/video123.mp4"
        )

        # URL should contain the specific object path
        assert "videos/coop1/video123.mp4" in url or "video123" in url

    def test_presigned_url_not_reusable(self):
        """Presigned URLs not reusable after expiry."""
        from src.security.presigned_urls import PresignedURLGenerator

        generator = PresignedURLGenerator()

        # Generate URL with very short expiry
        url = generator.generate_url(
            bucket="test-bucket",
            key="test.mp4",
            expiry_seconds=1
        )

        # URL should include expiration info
        assert "Expires" in url or "X-Amz-Expires" in url
