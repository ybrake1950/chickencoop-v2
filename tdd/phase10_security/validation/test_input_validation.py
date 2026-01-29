"""
Phase 10: Input Validation Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
- JSON schema validation for all input
- COOP_ID allowlist enforcement
- Sensor configuration bounds checking
- SQL injection prevention
- Path traversal prevention
- Command injection prevention

WHY THIS MATTERS:
-----------------
Invalid or malicious input can crash the system or allow attackers to
execute arbitrary code. All user input, API parameters, and configuration
values must be validated against strict schemas.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase10_security/validation/test_input_validation.py -v
"""
import pytest
from unittest.mock import MagicMock, patch

from src.security.validation import (
    InputValidator,
    SchemaValidator,
    CoopIDValidator,
    SensorConfigValidator,
    SQLInjectionDetector,
    PathTraversalDetector,
    CommandInjectionDetector,
    ValidationError,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def schema_validator():
    """Provide a JSON schema validator."""
    return SchemaValidator()


@pytest.fixture
def coop_validator():
    """Provide a coop ID validator."""
    return CoopIDValidator(allowed_coops=["coop1", "coop2", "test-coop"])


@pytest.fixture
def sensor_validator():
    """Provide a sensor config validator."""
    return SensorConfigValidator()


@pytest.fixture
def input_validator():
    """Provide a general input validator."""
    return InputValidator()


# =============================================================================
# TestJSONSchemaValidation
# =============================================================================

class TestJSONSchemaValidation:
    """Test JSON schema validation for API inputs."""

    def test_config_validated_against_schema(self, schema_validator):
        """Configuration validated against JSON schema."""
        valid_config = {
            "coop_id": "coop1",
            "temperature_threshold": 90,
            "humidity_threshold": 80,
            "recording_duration": 30
        }

        result = schema_validator.validate_config(valid_config)
        assert result.valid is True

    def test_api_request_body_validated(self, schema_validator):
        """API request bodies validated against schema."""
        valid_request = {
            "action": "record",
            "duration": 60,
            "camera": "indoor"
        }

        result = schema_validator.validate_api_request(
            endpoint="/api/video/record",
            body=valid_request
        )
        assert result.valid is True

    def test_invalid_json_rejected(self, schema_validator):
        """Malformed JSON rejected with clear error."""
        invalid_json = "{ invalid json }"

        with pytest.raises(ValidationError) as exc_info:
            schema_validator.parse_and_validate(invalid_json)

        assert "JSON" in str(exc_info.value) or "parse" in str(exc_info.value).lower()

    def test_extra_fields_rejected(self, schema_validator):
        """Unknown fields in JSON rejected."""
        request_with_extra = {
            "action": "record",
            "duration": 60,
            "unknown_field": "malicious_value",
            "another_extra": 123
        }

        result = schema_validator.validate_api_request(
            endpoint="/api/video/record",
            body=request_with_extra,
            strict=True
        )

        assert result.valid is False
        assert "unknown" in result.error.lower() or "extra" in result.error.lower()

    def test_missing_required_fields_rejected(self, schema_validator):
        """Missing required fields cause validation error."""
        incomplete_request = {
            "action": "record"
            # missing required "duration" field
        }

        result = schema_validator.validate_api_request(
            endpoint="/api/video/record",
            body=incomplete_request
        )

        assert result.valid is False
        assert "required" in result.error.lower() or "missing" in result.error.lower()

    def test_type_mismatch_rejected(self, schema_validator):
        """Wrong data types rejected."""
        wrong_type_request = {
            "action": "record",
            "duration": "sixty"  # Should be integer, not string
        }

        result = schema_validator.validate_api_request(
            endpoint="/api/video/record",
            body=wrong_type_request
        )

        assert result.valid is False
        assert "type" in result.error.lower()


# =============================================================================
# TestCoopIDValidation
# =============================================================================

class TestCoopIDValidation:
    """Test COOP_ID allowlist validation."""

    def test_valid_coop_id_accepted(self, coop_validator):
        """Valid coop IDs (coop1, coop2) accepted."""
        assert coop_validator.is_valid("coop1") is True
        assert coop_validator.is_valid("coop2") is True
        assert coop_validator.is_valid("test-coop") is True

    def test_invalid_coop_id_rejected(self, coop_validator):
        """Invalid coop IDs rejected."""
        assert coop_validator.is_valid("coop99") is False
        assert coop_validator.is_valid("unknown") is False
        assert coop_validator.is_valid("") is False

    def test_coop_id_case_normalized(self, coop_validator):
        """Coop ID normalized to lowercase."""
        normalized = coop_validator.normalize("COOP1")
        assert normalized == "coop1"

        normalized = coop_validator.normalize("CoOp2")
        assert normalized == "coop2"

    def test_coop_id_injection_prevented(self, coop_validator):
        """Path injection via coop_id prevented."""
        # These should all be rejected
        malicious_ids = [
            "coop1/../secrets",
            "../../../etc/passwd",
            "coop1/../../..",
            "coop1%2F..%2F..",
            "coop1\x00malicious"
        ]

        for malicious_id in malicious_ids:
            assert coop_validator.is_valid(malicious_id) is False

    def test_coop_id_in_s3_key_validated(self, coop_validator):
        """Coop ID validated when building S3 keys."""
        # Valid coop should produce valid S3 key
        s3_key = coop_validator.build_s3_key("coop1", "videos/test.mp4")
        assert s3_key == "coop1/videos/test.mp4"

        # Invalid coop should raise
        with pytest.raises(ValidationError):
            coop_validator.build_s3_key("../invalid", "videos/test.mp4")


# =============================================================================
# TestSensorConfigValidation
# =============================================================================

class TestSensorConfigValidation:
    """Test sensor configuration bounds."""

    def test_temperature_threshold_bounds(self, sensor_validator):
        """Temperature thresholds within valid range."""
        # Valid range: typically -40°F to 140°F
        assert sensor_validator.validate_temperature_threshold(90) is True
        assert sensor_validator.validate_temperature_threshold(32) is True
        assert sensor_validator.validate_temperature_threshold(100) is True

        # Invalid: too extreme
        assert sensor_validator.validate_temperature_threshold(-100) is False
        assert sensor_validator.validate_temperature_threshold(500) is False

    def test_humidity_threshold_0_to_100(self, sensor_validator):
        """Humidity thresholds between 0-100."""
        assert sensor_validator.validate_humidity_threshold(0) is True
        assert sensor_validator.validate_humidity_threshold(50) is True
        assert sensor_validator.validate_humidity_threshold(100) is True

        # Invalid: outside 0-100
        assert sensor_validator.validate_humidity_threshold(-1) is False
        assert sensor_validator.validate_humidity_threshold(101) is False
        assert sensor_validator.validate_humidity_threshold(150) is False

    def test_sample_interval_minimum(self, sensor_validator):
        """Sample interval has minimum value."""
        # Minimum sample interval (e.g., 5 seconds)
        assert sensor_validator.validate_sample_interval(5) is True
        assert sensor_validator.validate_sample_interval(60) is True
        assert sensor_validator.validate_sample_interval(300) is True

        # Too frequent
        assert sensor_validator.validate_sample_interval(1) is False
        assert sensor_validator.validate_sample_interval(0) is False

    def test_camera_resolution_valid(self, sensor_validator):
        """Camera resolution in allowed values."""
        valid_resolutions = ["720p", "1080p", "480p"]

        for res in valid_resolutions:
            assert sensor_validator.validate_camera_resolution(res) is True

        # Invalid resolutions
        assert sensor_validator.validate_camera_resolution("4K") is False
        assert sensor_validator.validate_camera_resolution("invalid") is False

    def test_framerate_bounds(self, sensor_validator):
        """Framerate within hardware limits."""
        # Valid framerates for Pi camera
        assert sensor_validator.validate_framerate(15) is True
        assert sensor_validator.validate_framerate(30) is True

        # Invalid: too high for Pi
        assert sensor_validator.validate_framerate(120) is False
        assert sensor_validator.validate_framerate(0) is False


# =============================================================================
# TestSQLInjectionPrevention
# =============================================================================

class TestSQLInjectionPrevention:
    """Test SQL injection prevention."""

    def test_parameterized_queries_used(self):
        """All SQL uses parameterized queries."""
        from src.persistence.database import Database

        db = Database(":memory:")

        # Database should use parameterized queries
        assert hasattr(db, 'execute_parameterized') or hasattr(db, 'execute')

        # Check that query method requires parameters
        # This ensures SQL can't be directly interpolated
        assert db.uses_parameterized_queries() is True

    def test_sql_in_username_rejected(self, input_validator):
        """SQL injection in username rejected."""
        malicious_usernames = [
            "admin'; DROP TABLE users;--",
            "admin' OR '1'='1",
            "admin\"; DELETE FROM users; --",
            "' OR 1=1 --",
            "1; SELECT * FROM users"
        ]

        for username in malicious_usernames:
            result = input_validator.validate_username(username)
            assert result.valid is False
            assert "injection" in result.error.lower() or "invalid" in result.error.lower()

    def test_sql_in_search_rejected(self, input_validator):
        """SQL injection in search terms rejected."""
        malicious_searches = [
            "'; DROP TABLE videos;--",
            "1 UNION SELECT password FROM users",
            "' OR '1'='1",
        ]

        for search in malicious_searches:
            result = input_validator.validate_search_term(search)
            assert result.valid is False

    def test_sqlite_special_chars_escaped(self, input_validator):
        """SQLite special characters escaped."""
        input_with_special = "O'Brien's coop"

        escaped = input_validator.escape_for_sqlite(input_with_special)

        # Single quotes should be escaped
        assert "O''Brien" in escaped or "\'" in escaped


# =============================================================================
# TestPathTraversalPrevention
# =============================================================================

class TestPathTraversalPrevention:
    """Test path traversal prevention."""

    def test_dotdot_in_path_rejected(self, input_validator):
        """.. in file paths rejected."""
        malicious_paths = [
            "../../../etc/passwd",
            "videos/../../../secrets",
            "..\\..\\windows\\system32",
            "....//....//etc/passwd",
        ]

        for path in malicious_paths:
            result = input_validator.validate_file_path(path)
            assert result.valid is False
            assert "traversal" in result.error.lower() or "invalid" in result.error.lower()

    def test_absolute_path_rejected(self, input_validator):
        """Absolute paths in user input rejected."""
        absolute_paths = [
            "/etc/passwd",
            "/var/log/syslog",
            "C:\\Windows\\System32",
        ]

        for path in absolute_paths:
            result = input_validator.validate_file_path(path, allow_absolute=False)
            assert result.valid is False

    def test_null_byte_rejected(self, input_validator):
        """Null bytes in paths rejected."""
        paths_with_null = [
            "video.mp4\x00.txt",
            "file\x00malicious",
            "test%00hidden",
        ]

        for path in paths_with_null:
            result = input_validator.validate_file_path(path)
            assert result.valid is False

    def test_symlink_not_followed(self, input_validator, tmp_path):
        """Symlinks not followed for file operations."""
        # Create a symlink pointing outside allowed directory
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()

        secret_file = tmp_path / "secret.txt"
        secret_file.write_text("secret data")

        symlink = allowed_dir / "link"
        symlink.symlink_to(secret_file)

        # Validator should reject symlink access
        result = input_validator.validate_file_access(
            str(symlink),
            allowed_directory=str(allowed_dir),
            follow_symlinks=False
        )

        assert result.valid is False or result.is_symlink is True

    def test_video_filename_sanitized(self, input_validator):
        """Video filenames sanitized."""
        malicious_filenames = [
            "video;rm -rf /.mp4",
            "video|cat /etc/passwd.mp4",
            "../../../video.mp4",
            "video`whoami`.mp4"
        ]

        for filename in malicious_filenames:
            sanitized = input_validator.sanitize_filename(filename)

            # Sanitized name should not contain dangerous chars
            assert ";" not in sanitized
            assert "|" not in sanitized
            assert "`" not in sanitized
            assert ".." not in sanitized


# =============================================================================
# TestCommandInjectionPrevention
# =============================================================================

class TestCommandInjectionPrevention:
    """Test command injection prevention."""

    def test_shell_metacharacters_escaped(self, input_validator):
        """Shell metacharacters escaped in subprocess."""
        dangerous_inputs = [
            "file; rm -rf /",
            "file | cat /etc/passwd",
            "file && echo pwned",
            "file $(whoami)",
            "file `id`",
        ]

        for inp in dangerous_inputs:
            escaped = input_validator.escape_shell_arg(inp)

            # Should be safe to use in shell
            assert ";" not in escaped or escaped.startswith("'")
            assert "|" not in escaped or escaped.startswith("'")
            assert "$" not in escaped or escaped.startswith("'")

    def test_subprocess_uses_list_args(self):
        """Subprocess calls use list arguments, not shell=True."""
        from src.utils.process import run_command

        # Check that the function signature doesn't allow shell=True
        import inspect
        sig = inspect.signature(run_command)

        # If shell parameter exists, its default should be False
        if 'shell' in sig.parameters:
            assert sig.parameters['shell'].default is False

    def test_user_input_not_in_commands(self, input_validator):
        """User input never directly in shell commands."""
        user_input = "test; rm -rf /"

        # Build command safely
        command = input_validator.build_safe_command(
            base_command=["ffmpeg", "-i"],
            user_args=[user_input]
        )

        # Command should be a list, not a string
        assert isinstance(command, list)

        # User input should be escaped or quoted
        assert "; rm -rf /" not in " ".join(command)

    def test_iot_command_payload_validated(self, input_validator):
        """IoT command payloads validated before execution."""
        valid_commands = [
            {"action": "record", "duration": 60},
            {"action": "headcount"},
            {"action": "restart_service", "service": "monitor"}
        ]

        invalid_commands = [
            {"action": "execute", "command": "rm -rf /"},  # Arbitrary command
            {"action": "record; rm -rf /"},  # Injection in action
            {"action": "record", "duration": "60; whoami"},  # Injection in param
        ]

        for cmd in valid_commands:
            result = input_validator.validate_iot_command(cmd)
            assert result.valid is True

        for cmd in invalid_commands:
            result = input_validator.validate_iot_command(cmd)
            assert result.valid is False
