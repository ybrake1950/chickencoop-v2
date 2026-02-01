"""
Input validation for security-sensitive operations.

Provides validators for JSON schemas, coop IDs, sensor configs,
SQL injection, path traversal, and command injection prevention.
"""

import json
import os
import re
import shlex
from dataclasses import dataclass
from typing import Any, Dict, List


class ValidationError(Exception):
    """Raised when input validation fails."""


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    error: str = ""
    is_symlink: bool = False


# --- API request schemas ---

_API_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "/api/video/record": {
        "required": ["action", "duration"],
        "properties": {
            "action": {"type": str},
            "duration": {"type": int},
            "camera": {"type": str},
        },
    },
}

_CONFIG_REQUIRED = [
    "coop_id",
    "temperature_threshold",
    "humidity_threshold",
    "recording_duration",
]
_CONFIG_TYPES = {
    "coop_id": str,
    "temperature_threshold": (int, float),
    "humidity_threshold": (int, float),
    "recording_duration": (int, float),
}


class SchemaValidator:
    """Validate JSON data against schemas."""

    def validate_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate a configuration dictionary against required fields and types."""
        for key in _CONFIG_REQUIRED:
            if key not in config:
                return ValidationResult(
                    valid=False, error=f"Missing required field: {key}"
                )
        for key, expected in _CONFIG_TYPES.items():
            if key in config and not isinstance(config[key], expected):  # type: ignore[arg-type]
                return ValidationResult(valid=False, error=f"Type mismatch for {key}")
        return ValidationResult(valid=True)

    def validate_api_request(
        self, endpoint: str, body: Dict[str, Any], strict: bool = False
    ) -> ValidationResult:
        """Validate an API request body against the schema for the endpoint."""
        schema = _API_SCHEMAS.get(endpoint)
        if schema is None:
            return ValidationResult(valid=True)

        for req in schema.get("required", []):
            if req not in body:
                return ValidationResult(
                    valid=False, error=f"Missing required field: {req}"
                )

        for key, prop in schema.get("properties", {}).items():
            if key in body and not isinstance(body[key], prop["type"]):
                return ValidationResult(
                    valid=False,
                    error=f"Type mismatch for {key}: expected {prop['type'].__name__}",
                )

        if strict:
            allowed = set(schema.get("properties", {}).keys())
            extra = set(body.keys()) - allowed
            if extra:
                return ValidationResult(
                    valid=False,
                    error=f"Extra unknown fields: {', '.join(sorted(extra))}",
                )

        return ValidationResult(valid=True)

    def parse_and_validate(self, raw_json: str) -> Dict[str, Any]:
        """Parse a raw JSON string and return the resulting dictionary."""
        try:
            return json.loads(raw_json)
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValidationError(f"JSON parse error: {exc}") from exc


class CoopIDValidator:
    """Validate coop IDs against an allowlist."""

    def __init__(self, allowed_coops: List[str]):
        self._allowed = [c.lower() for c in allowed_coops]

    def is_valid(self, coop_id: str) -> bool:
        """Return True if the coop ID is in the allowlist and free of injection chars."""
        if not coop_id:
            return False
        if "\x00" in coop_id or "%00" in coop_id:
            return False
        if ".." in coop_id or "/" in coop_id or "\\" in coop_id:
            return False
        if "%2F" in coop_id or "%2f" in coop_id:
            return False
        return coop_id.lower() in self._allowed

    def normalize(self, coop_id: str) -> str:
        """Normalize a coop ID to lowercase."""
        return coop_id.lower()

    def build_s3_key(self, coop_id: str, path: str) -> str:
        """Build a validated S3 key from a coop ID and path."""
        if not self.is_valid(coop_id):
            raise ValidationError(f"Invalid coop_id: {coop_id}")
        return f"{coop_id}/{path}"


class SensorConfigValidator:
    """Validate sensor configuration values."""

    def validate_temperature_threshold(self, value: float) -> bool:
        """Return True if the temperature is within -40 to 140."""
        return -40 <= value <= 140

    def validate_humidity_threshold(self, value: float) -> bool:
        """Return True if the humidity is within 0 to 100."""
        return 0 <= value <= 100

    def validate_sample_interval(self, value: int) -> bool:
        """Return True if the sample interval is at least 5 seconds."""
        return value >= 5

    def validate_camera_resolution(self, value: str) -> bool:
        """Return True if the resolution is a supported value."""
        return value in ("480p", "720p", "1080p")

    def validate_framerate(self, value: int) -> bool:
        """Return True if the framerate is between 1 and 60."""
        return 1 <= value <= 60


_SQL_PATTERNS = [
    re.compile(
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|UNION)\b)", re.IGNORECASE
    ),
    re.compile(r"(--|;|')", re.IGNORECASE),
    re.compile(r"(\bOR\b\s+.*=)", re.IGNORECASE),
]


class SQLInjectionDetector:
    """Detect SQL injection attempts in user-supplied strings."""

    def is_suspicious(self, value: str) -> bool:
        """Return True if the value contains SQL injection patterns."""
        for pattern in _SQL_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def check(self, value: str) -> ValidationResult:
        """Validate a string against SQL injection patterns."""
        if self.is_suspicious(value):
            return ValidationResult(
                valid=False, error="Possible SQL injection detected"
            )
        return ValidationResult(valid=True)


_PATH_TRAVERSAL_PATTERNS = [
    re.compile(r"\.\.[\\/]"),
    re.compile(r"%2[eE]%2[eE]"),
    re.compile(r"\x00"),
    re.compile(r"%00"),
]


class PathTraversalDetector:
    """Detect path traversal attempts in file paths."""

    def is_suspicious(self, path: str) -> bool:
        """Return True if the path contains traversal patterns."""
        for pattern in _PATH_TRAVERSAL_PATTERNS:
            if pattern.search(path):
                return True
        return False

    def check(self, path: str) -> ValidationResult:
        """Validate a path against traversal patterns."""
        if self.is_suspicious(path):
            return ValidationResult(
                valid=False, error="Possible path traversal detected"
            )
        return ValidationResult(valid=True)


_COMMAND_INJECTION_PATTERNS = [
    re.compile(r"[;|&`$<>]"),
    re.compile(r"\$\("),
    re.compile(r"`.*`"),
]


class CommandInjectionDetector:
    """Detect command injection attempts in user-supplied strings."""

    def is_suspicious(self, value: str) -> bool:
        """Return True if the value contains command injection patterns."""
        for pattern in _COMMAND_INJECTION_PATTERNS:
            if pattern.search(value):
                return True
        return False

    def check(self, value: str) -> ValidationResult:
        """Validate a string against command injection patterns."""
        if self.is_suspicious(value):
            return ValidationResult(
                valid=False, error="Possible command injection detected"
            )
        return ValidationResult(valid=True)


_VALID_IOT_ACTIONS = {"record", "headcount", "restart_service"}


class InputValidator:
    """General-purpose input validator."""

    def validate_username(self, username: str) -> ValidationResult:
        """Validate a username against SQL injection patterns and format rules."""
        for pattern in _SQL_PATTERNS:
            if pattern.search(username):
                return ValidationResult(
                    valid=False,
                    error="Invalid characters detected (possible injection)",
                )
        if not re.match(r"^[a-zA-Z0-9_.-]+$", username):
            return ValidationResult(valid=False, error="Invalid username format")
        return ValidationResult(valid=True)

    def validate_search_term(self, term: str) -> ValidationResult:
        """Validate a search term against SQL injection patterns."""
        for pattern in _SQL_PATTERNS:
            if pattern.search(term):
                return ValidationResult(
                    valid=False, error="Invalid search term (possible injection)"
                )
        return ValidationResult(valid=True)

    def escape_for_sqlite(self, value: str) -> str:
        """Escape single quotes for safe use in SQLite queries."""
        return value.replace("'", "''")

    def validate_file_path(
        self, path: str, allow_absolute: bool = True
    ) -> ValidationResult:
        """Validate a file path for null bytes and traversal attempts."""
        if "\x00" in path or "%00" in path:
            return ValidationResult(
                valid=False, error="Invalid path: null byte detected"
            )
        if ".." in path:
            return ValidationResult(
                valid=False, error="Invalid path: traversal detected"
            )
        if not allow_absolute:
            if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
                return ValidationResult(
                    valid=False, error="Invalid path: absolute paths not allowed"
                )
        return ValidationResult(valid=True)

    def validate_file_access(
        self, path: str, allowed_directory: str, follow_symlinks: bool = True
    ) -> ValidationResult:
        """Validate that a file path resolves within the allowed directory."""
        if os.path.islink(path):
            if not follow_symlinks:
                return ValidationResult(
                    valid=False, is_symlink=True, error="Symlink detected"
                )
        real = os.path.realpath(path)
        if not real.startswith(os.path.realpath(allowed_directory)):
            return ValidationResult(valid=False, error="Path outside allowed directory")
        return ValidationResult(valid=True)

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize a filename by removing dangerous characters."""
        sanitized = re.sub(r"[;|`$&<>]", "_", filename)
        sanitized = sanitized.replace("..", "_")
        parts = sanitized.split("/")
        return parts[-1]

    def escape_shell_arg(self, arg: str) -> str:
        """Escape a string for safe use as a shell argument."""
        return shlex.quote(arg)

    def build_safe_command(
        self, base_command: List[str], user_args: List[str]
    ) -> List[str]:
        """Build a command list with sanitized user arguments."""
        safe_args = []
        for arg in user_args:
            cleaned = re.sub(r"[;|&`$<>]", "", arg)
            safe_args.append(cleaned)
        return base_command + safe_args

    def validate_iot_command(self, command: Dict[str, Any]) -> ValidationResult:
        """Validate an IoT command payload for allowed actions and safe values."""
        action = command.get("action", "")
        if not isinstance(action, str) or action not in _VALID_IOT_ACTIONS:
            return ValidationResult(valid=False, error=f"Invalid IoT action: {action}")

        for key, value in command.items():
            if isinstance(value, str):
                dangerous = re.compile(r"[;|&`$<>]")
                if dangerous.search(value):
                    return ValidationResult(
                        valid=False, error=f"Invalid characters in {key}"
                    )

        duration = command.get("duration")
        if duration is not None and not isinstance(duration, (int, float)):
            return ValidationResult(valid=False, error="Duration must be numeric")

        return ValidationResult(valid=True)
