"""
Security Audit Logging Module
==============================

Provides audit logging for security-relevant events including
authentication, configuration changes, data access, and security events.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class AuditEventType(Enum):
    """Types of audit events."""

    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILURE = "LOGIN_FAILURE"
    LOGOUT = "LOGOUT"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    CONFIG_CHANGE = "CONFIG_CHANGE"
    DATA_ACCESS = "DATA_ACCESS"
    API_CALL = "API_CALL"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INVALID_TOKEN = "INVALID_TOKEN"
    AUTHORIZATION_FAILURE = "AUTHORIZATION_FAILURE"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"


# Log levels associated with event types
_EVENT_LOG_LEVELS: Dict[AuditEventType, str] = {
    AuditEventType.LOGIN_SUCCESS: "INFO",
    AuditEventType.LOGIN_FAILURE: "WARNING",
    AuditEventType.LOGOUT: "INFO",
    AuditEventType.PASSWORD_CHANGE: "INFO",
    AuditEventType.CONFIG_CHANGE: "INFO",
    AuditEventType.DATA_ACCESS: "INFO",
    AuditEventType.API_CALL: "INFO",
    AuditEventType.RATE_LIMIT_EXCEEDED: "WARNING",
    AuditEventType.INVALID_TOKEN: "WARNING",
    AuditEventType.AUTHORIZATION_FAILURE: "WARNING",
    AuditEventType.SUSPICIOUS_ACTIVITY: "WARNING",
    AuditEventType.VALIDATION_FAILURE: "WARNING",
}

# Fields that must never appear in logs
_SENSITIVE_FIELDS = {
    "password",
    "new_password",
    "old_password",
    "secret",
    "token",
    "api_key",
}

# Fields that should be redacted
_PII_FIELDS = {"email", "phone", "ssn"}


def _compute_integrity_hash(data: dict) -> str:
    """Compute a SHA-256 hash of the log entry for tamper detection."""
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class AuditLogEntry:
    """A single audit log entry."""

    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    log_level: str = "INFO"
    integrity_hash: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert the audit log entry to a dictionary."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "correlation_id": self.correlation_id,
            "details": self.details,
            "log_level": self.log_level,
            "integrity_hash": self.integrity_hash,
        }


# Alias for import compatibility
AuditEvent = AuditLogEntry


class AuditLogger:
    """Audit logger that writes structured JSON log entries."""

    def __init__(
        self,
        log_path: Path,
        enable_cloudwatch: bool = False,
        cloudwatch_client: Any = None,
    ):
        self.log_path = Path(log_path)
        self.cloudwatch_enabled = enable_cloudwatch
        self._cloudwatch_client = cloudwatch_client
        self._entries: List[AuditLogEntry] = []

    # -----------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------

    def _filter_sensitive(self, kwargs: dict) -> dict:
        """Remove sensitive fields and redact PII from arbitrary kwargs."""
        filtered = {}
        for k, v in kwargs.items():
            if k in _SENSITIVE_FIELDS:
                continue
            if k in _PII_FIELDS:
                filtered[k] = "REDACTED"
            else:
                filtered[k] = v
        return filtered

    def _append(self, entry: AuditLogEntry) -> None:
        """Persist an entry to the in-memory list and log file, optionally ship to CloudWatch."""
        # Compute integrity hash over the entry data (excluding the hash itself)
        data_for_hash = entry.to_dict()
        data_for_hash.pop("integrity_hash", None)
        entry.integrity_hash = _compute_integrity_hash(data_for_hash)

        self._entries.append(entry)

        # Append to log file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict(), default=str) + "\n")

        # Ship to CloudWatch if enabled
        if self.cloudwatch_enabled and self._cloudwatch_client:
            self._cloudwatch_client.put_log_events(
                logGroupName="/chickencoop/audit",
                logStreamName="audit",
                logEvents=[
                    {
                        "timestamp": int(entry.timestamp.timestamp() * 1000),
                        "message": json.dumps(entry.to_dict(), default=str),
                    }
                ],
            )

    def _make_entry(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLogEntry:
        return AuditLogEntry(
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            details=details or {},
            log_level=_EVENT_LOG_LEVELS.get(event_type, "INFO"),
        )

    # -----------------------------------------------------------------
    # Authentication logging
    # -----------------------------------------------------------------

    def log_login_success(
        self,
        user_id: str,
        ip_address: str,
        user_agent: str,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Record a successful login event."""
        entry = self._make_entry(
            AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
        )
        self._append(entry)

    def log_login_failure(
        self,
        username: str,
        ip_address: str,
        reason: str,
        **kwargs: Any,
    ) -> None:
        """Record a failed login attempt with the reason for failure."""
        filtered = self._filter_sensitive(kwargs)
        details = {"username": username, "reason": reason, **filtered}
        entry = self._make_entry(
            AuditEventType.LOGIN_FAILURE,
            ip_address=ip_address,
            details=details,
        )
        self._append(entry)

    def log_logout(
        self,
        user_id: str,
        session_id: str,
    ) -> None:
        """Record a user logout event."""
        entry = self._make_entry(
            AuditEventType.LOGOUT,
            user_id=user_id,
            details={"session_id": session_id},
        )
        self._append(entry)

    def log_password_change(
        self,
        user_id: str,
        ip_address: str,
    ) -> None:
        """Record a password change event."""
        entry = self._make_entry(
            AuditEventType.PASSWORD_CHANGE,
            user_id=user_id,
            ip_address=ip_address,
        )
        self._append(entry)

    # -----------------------------------------------------------------
    # Configuration change logging
    # -----------------------------------------------------------------

    def log_config_change(
        self,
        user_id: str,
        setting_name: str,
        old_value: str,
        new_value: str,
        category: Optional[str] = None,
    ) -> None:
        """Record a configuration change with old and new values."""
        details: Dict[str, Any] = {
            "setting_name": setting_name,
            "old_value": old_value,
            "new_value": new_value,
        }
        if category is not None:
            details["category"] = category
        entry = self._make_entry(
            AuditEventType.CONFIG_CHANGE,
            user_id=user_id,
            details=details,
        )
        self._append(entry)

    # -----------------------------------------------------------------
    # Data access logging
    # -----------------------------------------------------------------

    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        record_count: Optional[int] = None,
        sensitive: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        """Record a data access event for auditing purposes."""
        filtered = self._filter_sensitive(kwargs)
        details: Dict[str, Any] = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action": action,
            **filtered,
        }
        if record_count is not None:
            details["record_count"] = record_count
        if sensitive is not None:
            details["sensitive"] = sensitive
        entry = self._make_entry(
            AuditEventType.DATA_ACCESS,
            user_id=user_id,
            details=details,
        )
        self._append(entry)

    def log_api_call(
        self,
        user_id: str,
        endpoint: str,
        method: str,
        ip_address: str,
        response_code: int,
    ) -> None:
        """Record an API call with endpoint, method, and response code."""
        entry = self._make_entry(
            AuditEventType.API_CALL,
            user_id=user_id,
            ip_address=ip_address,
            details={
                "endpoint": endpoint,
                "method": method,
                "response_code": response_code,
            },
        )
        self._append(entry)

    # -----------------------------------------------------------------
    # Security event logging
    # -----------------------------------------------------------------

    def log_security_event(
        self,
        event_type: AuditEventType,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a security event such as rate limiting or authorization failure."""
        combined_details: Dict[str, Any] = {}
        if endpoint:
            combined_details["endpoint"] = endpoint
        if details:
            combined_details.update(details)
        entry = self._make_entry(
            event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=combined_details,
        )
        self._append(entry)

    # -----------------------------------------------------------------
    # Query / retrieval
    # -----------------------------------------------------------------

    def get_recent_entries(self, count: int = 10) -> List[AuditLogEntry]:
        """Return the most recent *count* entries."""
        return self._entries[-count:]

    def get_raw_log_line(self, index: int = -1) -> str:
        """Return a raw JSON log line from the file by index."""
        lines = self.log_path.read_text(encoding="utf-8").strip().splitlines()
        return lines[index]

    # -----------------------------------------------------------------
    # Integrity verification
    # -----------------------------------------------------------------

    def verify_integrity(self, entry: AuditLogEntry) -> bool:
        """Verify the integrity hash of an entry."""
        data = entry.to_dict()
        stored_hash = data.pop("integrity_hash", None)
        if stored_hash is None:
            return False
        return _compute_integrity_hash(data) == stored_hash
