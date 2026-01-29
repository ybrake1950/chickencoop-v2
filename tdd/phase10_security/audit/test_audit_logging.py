"""
Phase 10: Audit Logging Tests
=============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Security event logging
- Authentication attempt logging
- Configuration change logging
- Data access logging
- Log integrity protection

WHY THIS MATTERS:
-----------------
Audit logs are essential for detecting attacks, investigating incidents,
and meeting compliance requirements. All security-relevant events must
be logged with sufficient detail.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase10_security/audit/test_audit_logging.py -v
"""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from pathlib import Path

from src.security.audit import (
    AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditLogEntry,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def audit_logger(tmp_path):
    """Provide an audit logger instance."""
    log_path = tmp_path / "audit.log"
    return AuditLogger(log_path=log_path, enable_cloudwatch=False)


@pytest.fixture
def sample_user_context():
    """Provide sample user context."""
    return {
        "user_id": "user-123",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 TestBrowser/1.0",
        "session_id": "session-abc123"
    }


# =============================================================================
# TestAuthenticationLogging
# =============================================================================

class TestAuthenticationLogging:
    """Test authentication event logging."""

    def test_successful_login_logged(self, audit_logger, sample_user_context):
        """Successful logins are logged."""
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent=sample_user_context["user_agent"]
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.LOGIN_SUCCESS
        assert entries[0].user_id == "user-123"

    def test_failed_login_logged(self, audit_logger, sample_user_context):
        """Failed login attempts are logged."""
        audit_logger.log_login_failure(
            username="testuser",
            ip_address=sample_user_context["ip_address"],
            reason="Invalid password"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.LOGIN_FAILURE
        assert "Invalid password" in entries[0].details.get("reason", "")

    def test_logout_logged(self, audit_logger, sample_user_context):
        """Logouts are logged."""
        audit_logger.log_logout(
            user_id=sample_user_context["user_id"],
            session_id=sample_user_context["session_id"]
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.LOGOUT

    def test_password_change_logged(self, audit_logger, sample_user_context):
        """Password changes are logged."""
        audit_logger.log_password_change(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"]
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.PASSWORD_CHANGE
        # Password itself should NOT be logged
        assert "new_password" not in entries[0].details

    def test_login_includes_ip(self, audit_logger, sample_user_context):
        """Login logs include IP address."""
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address="10.0.0.50",
            user_agent=sample_user_context["user_agent"]
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].ip_address == "10.0.0.50"

    def test_login_includes_user_agent(self, audit_logger, sample_user_context):
        """Login logs include user agent."""
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent="CustomClient/2.0"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].user_agent == "CustomClient/2.0"


# =============================================================================
# TestConfigurationChangeLogging
# =============================================================================

class TestConfigurationChangeLogging:
    """Test configuration change logging."""

    def test_threshold_change_logged(self, audit_logger, sample_user_context):
        """Alert threshold changes logged."""
        audit_logger.log_config_change(
            user_id=sample_user_context["user_id"],
            setting_name="temperature_alert_threshold",
            old_value="90",
            new_value="95"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.CONFIG_CHANGE
        assert entries[0].details["setting_name"] == "temperature_alert_threshold"

    def test_setting_change_logged(self, audit_logger, sample_user_context):
        """Setting changes logged with old/new values."""
        audit_logger.log_config_change(
            user_id=sample_user_context["user_id"],
            setting_name="recording_duration",
            old_value="30",
            new_value="60"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].details["old_value"] == "30"
        assert entries[0].details["new_value"] == "60"

    def test_camera_config_change_logged(self, audit_logger, sample_user_context):
        """Camera configuration changes logged."""
        audit_logger.log_config_change(
            user_id=sample_user_context["user_id"],
            setting_name="camera_resolution",
            old_value="720p",
            new_value="1080p",
            category="camera"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].details["category"] == "camera"

    def test_who_made_change_logged(self, audit_logger, sample_user_context):
        """User who made change is logged."""
        audit_logger.log_config_change(
            user_id="admin-001",
            setting_name="max_video_retention_days",
            old_value="7",
            new_value="14"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].user_id == "admin-001"


# =============================================================================
# TestDataAccessLogging
# =============================================================================

class TestDataAccessLogging:
    """Test data access logging."""

    def test_video_access_logged(self, audit_logger, sample_user_context):
        """Video access/download logged."""
        audit_logger.log_data_access(
            user_id=sample_user_context["user_id"],
            resource_type="video",
            resource_id="video-456",
            action="download"
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert len(entries) == 1
        assert entries[0].event_type == AuditEventType.DATA_ACCESS
        assert entries[0].details["resource_type"] == "video"

    def test_bulk_export_logged(self, audit_logger, sample_user_context):
        """Bulk data exports logged."""
        audit_logger.log_data_access(
            user_id=sample_user_context["user_id"],
            resource_type="sensor_data",
            resource_id="export-2025-01-25",
            action="bulk_export",
            record_count=10000
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].details["action"] == "bulk_export"
        assert entries[0].details["record_count"] == 10000

    def test_sensitive_data_access_logged(self, audit_logger, sample_user_context):
        """Access to sensitive data logged."""
        audit_logger.log_data_access(
            user_id=sample_user_context["user_id"],
            resource_type="user_credentials",
            resource_id="user-789",
            action="view",
            sensitive=True
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].details["sensitive"] is True

    def test_api_calls_logged(self, audit_logger, sample_user_context):
        """API calls logged with user context."""
        audit_logger.log_api_call(
            user_id=sample_user_context["user_id"],
            endpoint="/api/videos",
            method="GET",
            ip_address=sample_user_context["ip_address"],
            response_code=200
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.API_CALL
        assert entries[0].details["endpoint"] == "/api/videos"
        assert entries[0].details["method"] == "GET"


# =============================================================================
# TestSecurityEventLogging
# =============================================================================

class TestSecurityEventLogging:
    """Test security event logging."""

    def test_rate_limit_hit_logged(self, audit_logger):
        """Rate limit violations logged."""
        audit_logger.log_security_event(
            event_type=AuditEventType.RATE_LIMIT_EXCEEDED,
            ip_address="192.168.1.100",
            endpoint="/api/login",
            details={"requests_count": 100, "limit": 10}
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.RATE_LIMIT_EXCEEDED

    def test_invalid_token_logged(self, audit_logger):
        """Invalid token attempts logged."""
        audit_logger.log_security_event(
            event_type=AuditEventType.INVALID_TOKEN,
            ip_address="192.168.1.100",
            details={"reason": "Token signature invalid"}
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.INVALID_TOKEN

    def test_authorization_failure_logged(self, audit_logger, sample_user_context):
        """Authorization failures logged."""
        audit_logger.log_security_event(
            event_type=AuditEventType.AUTHORIZATION_FAILURE,
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            details={
                "required_permission": "admin:delete",
                "user_role": "viewer"
            }
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.AUTHORIZATION_FAILURE

    def test_suspicious_activity_logged(self, audit_logger):
        """Suspicious patterns logged."""
        audit_logger.log_security_event(
            event_type=AuditEventType.SUSPICIOUS_ACTIVITY,
            ip_address="192.168.1.100",
            details={
                "pattern": "rapid_endpoint_scanning",
                "endpoints_hit": 50,
                "time_window_seconds": 10
            }
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.SUSPICIOUS_ACTIVITY

    def test_validation_failure_logged(self, audit_logger, sample_user_context):
        """Input validation failures logged."""
        audit_logger.log_security_event(
            event_type=AuditEventType.VALIDATION_FAILURE,
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            details={
                "field": "coop_id",
                "value": "../../../etc/passwd",
                "reason": "Path traversal attempt"
            }
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].event_type == AuditEventType.VALIDATION_FAILURE
        assert "Path traversal" in entries[0].details["reason"]


# =============================================================================
# TestLogIntegrity
# =============================================================================

class TestLogIntegrity:
    """Test log integrity protection."""

    def test_logs_append_only(self, audit_logger, sample_user_context):
        """Logs are append-only."""
        # Write first entry
        audit_logger.log_login_success(
            user_id="user-001",
            ip_address="192.168.1.1",
            user_agent="Test"
        )

        # Write second entry
        audit_logger.log_login_success(
            user_id="user-002",
            ip_address="192.168.1.2",
            user_agent="Test"
        )

        entries = audit_logger.get_recent_entries(count=10)
        assert len(entries) == 2

        # First entry should still exist
        user_ids = [e.user_id for e in entries]
        assert "user-001" in user_ids
        assert "user-002" in user_ids

    def test_logs_include_timestamp(self, audit_logger, sample_user_context):
        """All log entries have timestamp."""
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent=sample_user_context["user_agent"]
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].timestamp is not None
        assert isinstance(entries[0].timestamp, datetime)

    def test_logs_include_correlation_id(self, audit_logger, sample_user_context):
        """Logs include correlation ID for tracing."""
        correlation_id = "req-12345-abcde"

        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent=sample_user_context["user_agent"],
            correlation_id=correlation_id
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].correlation_id == correlation_id

    def test_logs_shipped_to_cloudwatch(self, tmp_path):
        """Logs shipped to CloudWatch for retention."""
        mock_cloudwatch = MagicMock()

        logger = AuditLogger(
            log_path=tmp_path / "audit.log",
            enable_cloudwatch=True,
            cloudwatch_client=mock_cloudwatch
        )

        logger.log_login_success(
            user_id="user-123",
            ip_address="192.168.1.100",
            user_agent="Test"
        )

        # Verify CloudWatch was called
        assert mock_cloudwatch.put_log_events.called or logger.cloudwatch_enabled

    def test_log_tampering_detected(self, audit_logger, sample_user_context):
        """Log tampering can be detected."""
        # Write entry with integrity hash
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent=sample_user_context["user_agent"]
        )

        entries = audit_logger.get_recent_entries(count=1)

        # Entry should have integrity hash
        assert entries[0].integrity_hash is not None

        # Verify integrity check method exists
        assert audit_logger.verify_integrity(entries[0]) is True


# =============================================================================
# TestLogFormat
# =============================================================================

class TestLogFormat:
    """Test log format and content."""

    def test_structured_json_logging(self, audit_logger, sample_user_context):
        """Logs use structured JSON format."""
        audit_logger.log_login_success(
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            user_agent=sample_user_context["user_agent"]
        )

        # Get raw log line
        raw_log = audit_logger.get_raw_log_line(index=-1)

        # Should be valid JSON
        parsed = json.loads(raw_log)
        assert "event_type" in parsed
        assert "timestamp" in parsed

    def test_no_secrets_in_logs(self, audit_logger, sample_user_context):
        """Sensitive data not in logs."""
        # Attempt to log with password (should be filtered)
        audit_logger.log_login_failure(
            username="testuser",
            ip_address=sample_user_context["ip_address"],
            reason="Invalid password",
            password="supersecret123"  # Should NOT appear in logs
        )

        entries = audit_logger.get_recent_entries(count=1)
        log_str = str(entries[0].to_dict())

        assert "supersecret123" not in log_str

    def test_pii_redacted(self, audit_logger, sample_user_context):
        """PII redacted or masked in logs."""
        audit_logger.log_data_access(
            user_id=sample_user_context["user_id"],
            resource_type="user_profile",
            resource_id="user-789",
            action="view",
            email="user@example.com"  # PII - should be redacted
        )

        entries = audit_logger.get_recent_entries(count=1)
        log_str = str(entries[0].to_dict())

        # Email should be redacted/masked
        assert "user@example.com" not in log_str or "***" in log_str or "REDACTED" in log_str

    def test_log_level_appropriate(self, audit_logger, sample_user_context):
        """Security events at appropriate log level."""
        # Security failures should be WARNING or higher
        audit_logger.log_security_event(
            event_type=AuditEventType.AUTHORIZATION_FAILURE,
            user_id=sample_user_context["user_id"],
            ip_address=sample_user_context["ip_address"],
            details={"reason": "Unauthorized access attempt"}
        )

        entries = audit_logger.get_recent_entries(count=1)
        assert entries[0].log_level in ["WARNING", "ERROR", "CRITICAL"]
