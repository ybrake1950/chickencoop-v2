"""
TDD Tests: Environment Variable Handling

These tests define the expected behavior for environment variable management.
Implement src/config/environment.py to make these tests pass.

Run: pytest tdd/phase1_foundation/config/test_environment.py -v
"""

import os
import pytest


# =============================================================================
# Test: Environment Variable Reading
# =============================================================================

class TestEnvironmentVariables:
    """Tests for reading environment variables with defaults."""

    def test_get_env_returns_value_when_set(self, monkeypatch):
        """Should return environment variable value when set."""
        from src.config.environment import get_env

        monkeypatch.setenv("TEST_VAR", "test_value")

        result = get_env("TEST_VAR")

        assert result == "test_value"

    def test_get_env_returns_default_when_not_set(self, clean_env):
        """Should return default when variable not set."""
        from src.config.environment import get_env

        result = get_env("NONEXISTENT_VAR", default="default_value")

        assert result == "default_value"

    def test_get_env_returns_none_when_not_set_no_default(self, clean_env):
        """Should return None when variable not set and no default."""
        from src.config.environment import get_env

        result = get_env("NONEXISTENT_VAR")

        assert result is None

    def test_get_env_required_raises_when_not_set(self, clean_env):
        """Should raise error for required variable that's not set."""
        from src.config.environment import get_env, MissingEnvironmentVariable

        with pytest.raises(MissingEnvironmentVariable):
            get_env("REQUIRED_VAR", required=True)


# =============================================================================
# Test: Typed Environment Variables
# =============================================================================

class TestTypedEnvironmentVariables:
    """Tests for reading typed environment variables."""

    def test_get_env_int_returns_integer(self, monkeypatch):
        """Should return integer value."""
        from src.config.environment import get_env_int

        monkeypatch.setenv("INT_VAR", "42")

        result = get_env_int("INT_VAR")

        assert result == 42
        assert isinstance(result, int)

    def test_get_env_int_returns_default_when_not_set(self, clean_env):
        """Should return default integer when not set."""
        from src.config.environment import get_env_int

        result = get_env_int("INT_VAR", default=10)

        assert result == 10

    def test_get_env_int_raises_on_invalid_value(self, monkeypatch):
        """Should raise error for non-integer value."""
        from src.config.environment import get_env_int

        monkeypatch.setenv("INT_VAR", "not_an_int")

        with pytest.raises(ValueError):
            get_env_int("INT_VAR")

    def test_get_env_bool_returns_true_for_truthy(self, monkeypatch):
        """Should return True for truthy string values."""
        from src.config.environment import get_env_bool

        for value in ["true", "True", "TRUE", "1", "yes", "Yes"]:
            monkeypatch.setenv("BOOL_VAR", value)
            assert get_env_bool("BOOL_VAR") is True

    def test_get_env_bool_returns_false_for_falsy(self, monkeypatch):
        """Should return False for falsy string values."""
        from src.config.environment import get_env_bool

        for value in ["false", "False", "FALSE", "0", "no", "No"]:
            monkeypatch.setenv("BOOL_VAR", value)
            assert get_env_bool("BOOL_VAR") is False

    def test_get_env_bool_returns_default_when_not_set(self, clean_env):
        """Should return default boolean when not set."""
        from src.config.environment import get_env_bool

        result = get_env_bool("BOOL_VAR", default=True)

        assert result is True

    def test_get_env_float_returns_float(self, monkeypatch):
        """Should return float value."""
        from src.config.environment import get_env_float

        monkeypatch.setenv("FLOAT_VAR", "3.14")

        result = get_env_float("FLOAT_VAR")

        assert result == 3.14
        assert isinstance(result, float)


# =============================================================================
# Test: Coop ID Resolution
# =============================================================================

class TestCoopIdResolution:
    """Tests for COOP_ID environment variable handling."""

    def test_get_coop_id_returns_value(self, monkeypatch):
        """Should return COOP_ID when set."""
        from src.config.environment import get_coop_id

        monkeypatch.setenv("COOP_ID", "coop1")

        result = get_coop_id()

        assert result == "coop1"

    def test_get_coop_id_returns_default_when_not_set(self, clean_env):
        """Should return default coop ID when not set."""
        from src.config.environment import get_coop_id

        result = get_coop_id()

        assert result == "default"

    def test_get_coop_id_normalizes_to_lowercase(self, monkeypatch):
        """Should normalize coop ID to lowercase."""
        from src.config.environment import get_coop_id

        monkeypatch.setenv("COOP_ID", "COOP1")

        result = get_coop_id()

        assert result == "coop1"


# =============================================================================
# Test: Testing Mode Detection
# =============================================================================

class TestTestingModeDetection:
    """Tests for detecting test environment."""

    def test_is_testing_returns_true_when_set(self, monkeypatch):
        """Should return True when TESTING is set to true."""
        from src.config.environment import is_testing

        monkeypatch.setenv("TESTING", "true")

        assert is_testing() is True

    def test_is_testing_returns_false_when_not_set(self, clean_env):
        """Should return False when TESTING is not set."""
        from src.config.environment import is_testing

        assert is_testing() is False

    def test_is_production_returns_true_when_not_testing(self, clean_env):
        """Should return True for production when not testing."""
        from src.config.environment import is_production

        assert is_production() is True

    def test_is_production_returns_false_when_testing(self, monkeypatch):
        """Should return False when in testing mode."""
        from src.config.environment import is_production

        monkeypatch.setenv("TESTING", "true")

        assert is_production() is False


# =============================================================================
# Test: Secret Key Management
# =============================================================================

class TestSecretKeyManagement:
    """Tests for SECRET_KEY handling."""

    def test_get_secret_key_returns_value(self, monkeypatch):
        """Should return SECRET_KEY when set."""
        from src.config.environment import get_secret_key

        monkeypatch.setenv("SECRET_KEY", "my-secret-key")

        result = get_secret_key()

        assert result == "my-secret-key"

    def test_get_secret_key_raises_in_production_when_not_set(self, clean_env):
        """Should raise error in production when SECRET_KEY not set."""
        from src.config.environment import get_secret_key, MissingEnvironmentVariable

        with pytest.raises(MissingEnvironmentVariable):
            get_secret_key()

    def test_get_secret_key_returns_default_in_testing(self, monkeypatch):
        """Should return test default in testing mode."""
        from src.config.environment import get_secret_key

        monkeypatch.setenv("TESTING", "true")

        result = get_secret_key()

        assert result is not None
        assert len(result) > 0


# =============================================================================
# Test: AWS Region Configuration
# =============================================================================

class TestAWSRegionConfiguration:
    """Tests for AWS region environment handling."""

    def test_get_aws_region_returns_value(self, monkeypatch):
        """Should return AWS_REGION when set."""
        from src.config.environment import get_aws_region

        monkeypatch.setenv("AWS_REGION", "us-west-2")

        result = get_aws_region()

        assert result == "us-west-2"

    def test_get_aws_region_returns_default(self, clean_env):
        """Should return default region when not set."""
        from src.config.environment import get_aws_region

        result = get_aws_region()

        assert result == "us-east-1"

    def test_get_aws_region_from_default_region(self, monkeypatch, clean_env):
        """Should check AWS_DEFAULT_REGION as fallback."""
        from src.config.environment import get_aws_region

        monkeypatch.setenv("AWS_DEFAULT_REGION", "eu-west-1")

        result = get_aws_region()

        assert result == "eu-west-1"
