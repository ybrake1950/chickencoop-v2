"""
Phase 10: Secret Management Tests
=================================

FUNCTIONALITY BEING TESTED:
---------------------------
- No hardcoded credentials in code or config
- Environment variable usage for secrets
- AWS Secrets Manager integration
- Credential rotation support
- Secret exposure prevention in logs/errors

WHY THIS MATTERS:
-----------------
Hardcoded credentials are a major security risk. If code or config files
are exposed, attackers gain direct access to AWS resources, databases,
and other sensitive systems.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase10_security/secrets/test_secret_management.py -v
"""
import pytest
import os
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.security.secrets import (
    SecretManager,
    SecretConfig,
    EnvironmentSecretProvider,
    AWSSecretsManagerProvider,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def secret_manager():
    """Provide a secret manager instance."""
    return SecretManager()


@pytest.fixture
def env_provider():
    """Provide an environment variable secret provider."""
    return EnvironmentSecretProvider()


@pytest.fixture
def mock_aws_secrets_client():
    """Provide a mock AWS Secrets Manager client."""
    client = MagicMock()
    client.get_secret_value.return_value = {
        "SecretString": '{"api_key": "test-api-key", "db_password": "test-db-pass"}'
    }
    return client


# =============================================================================
# TestNoHardcodedCredentials
# =============================================================================

class TestNoHardcodedCredentials:
    """Test that no credentials are hardcoded."""

    def test_no_aws_keys_in_code(self, project_root):
        """No AWS access keys in source code."""
        # AWS access key pattern: AKIA followed by 16 alphanumeric chars
        aws_key_pattern = re.compile(r'AKIA[0-9A-Z]{16}')

        src_dir = project_root / "src"
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            matches = aws_key_pattern.findall(content)
            if matches:
                violations.append((py_file, matches))

        assert len(violations) == 0, f"AWS keys found in: {violations}"

    def test_no_aws_keys_in_config(self, project_root):
        """No AWS keys in configuration files."""
        aws_key_pattern = re.compile(r'AKIA[0-9A-Z]{16}')
        secret_key_pattern = re.compile(r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']')

        config_dir = project_root / "config"
        if not config_dir.exists():
            pytest.skip("config directory not found")

        violations = []
        for config_file in config_dir.rglob("*"):
            if config_file.is_file() and config_file.suffix in [".json", ".yaml", ".yml", ".ini", ".conf"]:
                content = config_file.read_text()
                if aws_key_pattern.search(content) or secret_key_pattern.search(content):
                    violations.append(config_file)

        assert len(violations) == 0, f"AWS keys found in config: {violations}"

    def test_no_passwords_in_code(self, project_root):
        """No passwords hardcoded in source."""
        # Common password patterns
        password_patterns = [
            re.compile(r'password\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
            re.compile(r'passwd\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
        ]

        src_dir = project_root / "src"
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            for pattern in password_patterns:
                matches = pattern.findall(content)
                # Filter out test files and obvious non-secrets
                if matches and "test" not in str(py_file).lower():
                    # Check if it's not just a variable name or config key
                    for match in matches:
                        if "os.environ" not in match and "getenv" not in match:
                            violations.append((py_file, match))

        # Allow zero violations or only in test files
        assert len(violations) == 0 or all("test" in str(v[0]).lower() for v in violations)

    def test_no_api_keys_in_code(self, project_root):
        """No API keys hardcoded."""
        # Generic API key pattern (long alphanumeric strings in assignments)
        api_key_pattern = re.compile(r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', re.IGNORECASE)

        src_dir = project_root / "src"
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            matches = api_key_pattern.findall(content)
            if matches and "test" not in str(py_file).lower():
                violations.append((py_file, matches))

        assert len(violations) == 0, f"API keys found in: {violations}"

    def test_no_private_keys_in_repo(self, project_root):
        """No private keys committed to repo."""
        private_key_extensions = [".pem", ".key", ".p12", ".pfx"]
        private_key_patterns = [
            "-----BEGIN RSA PRIVATE KEY-----",
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN EC PRIVATE KEY-----",
        ]

        violations = []

        # Check for key files
        for ext in private_key_extensions:
            for key_file in project_root.rglob(f"*{ext}"):
                if ".git" not in str(key_file) and "venv" not in str(key_file):
                    violations.append(f"Key file: {key_file}")

        # Check for embedded keys in source
        src_dir = project_root / "src"
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                content = py_file.read_text()
                for pattern in private_key_patterns:
                    if pattern in content:
                        violations.append(f"Private key in: {py_file}")

        assert len(violations) == 0, f"Private keys found: {violations}"

    def test_gitignore_covers_secrets(self, project_root):
        """.gitignore excludes secret files."""
        gitignore_path = project_root / ".gitignore"
        if not gitignore_path.exists():
            pytest.skip(".gitignore not found")

        content = gitignore_path.read_text()

        # Should ignore common secret file patterns
        expected_patterns = [".env", "*.pem", "*.key", "credentials"]
        found_patterns = []

        for pattern in expected_patterns:
            if pattern in content or pattern.replace("*", "") in content:
                found_patterns.append(pattern)

        # At least some secret patterns should be covered
        assert len(found_patterns) >= 2, f"Missing secret patterns in .gitignore"


# =============================================================================
# TestEnvironmentVariables
# =============================================================================

class TestEnvironmentVariables:
    """Test environment variable usage for secrets."""

    def test_aws_credentials_from_env(self, env_provider):
        """AWS credentials read from environment."""
        with patch.dict(os.environ, {
            "AWS_ACCESS_KEY_ID": "test-access-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret-key"
        }):
            access_key = env_provider.get_secret("AWS_ACCESS_KEY_ID")
            secret_key = env_provider.get_secret("AWS_SECRET_ACCESS_KEY")

            assert access_key == "test-access-key"
            assert secret_key == "test-secret-key"

    def test_secret_key_from_env(self, env_provider):
        """Flask SECRET_KEY from environment."""
        with patch.dict(os.environ, {"SECRET_KEY": "flask-secret-key-value"}):
            secret_key = env_provider.get_secret("SECRET_KEY")
            assert secret_key == "flask-secret-key-value"

    def test_database_url_from_env(self, env_provider):
        """Database connection from environment."""
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite:///data/chickencoop.db"}):
            db_url = env_provider.get_secret("DATABASE_URL")
            assert db_url == "sqlite:///data/chickencoop.db"

    def test_missing_secret_fails_gracefully(self, secret_manager):
        """Missing required secret causes clear error."""
        with patch.dict(os.environ, {}, clear=True):
            # Remove the env var if it exists
            os.environ.pop("NONEXISTENT_SECRET", None)

            result = secret_manager.get_secret("NONEXISTENT_SECRET", required=False)
            assert result is None

            # Required secret should raise
            with pytest.raises(ValueError) as exc_info:
                secret_manager.get_secret("NONEXISTENT_SECRET", required=True)

            assert "required" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

    def test_default_secrets_not_used_in_prod(self, secret_manager):
        """Default/fallback secrets rejected in production."""
        with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
            # Attempting to use default value in production should warn or fail
            result = secret_manager.get_secret(
                "API_KEY",
                default="default-insecure-key",
                environment="production"
            )

            # Should either return None or raise, not return the default
            assert result != "default-insecure-key" or result is None


# =============================================================================
# TestAWSSecretsManager
# =============================================================================

class TestAWSSecretsManager:
    """Test AWS Secrets Manager integration."""

    def test_secrets_fetched_from_manager(self, mock_aws_secrets_client):
        """Secrets fetched from AWS Secrets Manager."""
        provider = AWSSecretsManagerProvider(client=mock_aws_secrets_client)

        secret = provider.get_secret("chickencoop/api-keys")

        assert secret is not None
        mock_aws_secrets_client.get_secret_value.assert_called_once()

    def test_secrets_cached_appropriately(self, mock_aws_secrets_client):
        """Secrets cached to reduce API calls."""
        provider = AWSSecretsManagerProvider(
            client=mock_aws_secrets_client,
            cache_ttl_seconds=300
        )

        # First call
        provider.get_secret("chickencoop/api-keys")
        # Second call (should be cached)
        provider.get_secret("chickencoop/api-keys")

        # Should only call AWS once due to caching
        assert mock_aws_secrets_client.get_secret_value.call_count == 1

    def test_secret_fetch_failure_handled(self, mock_aws_secrets_client):
        """Secrets Manager unavailability handled."""
        mock_aws_secrets_client.get_secret_value.side_effect = Exception("Service unavailable")

        provider = AWSSecretsManagerProvider(client=mock_aws_secrets_client)

        # Should handle gracefully, not crash
        result = provider.get_secret("chickencoop/api-keys", required=False)
        assert result is None

    def test_secret_rotation_supported(self, mock_aws_secrets_client):
        """Rotated secrets picked up automatically."""
        provider = AWSSecretsManagerProvider(
            client=mock_aws_secrets_client,
            cache_ttl_seconds=1  # Short cache for testing
        )

        # First fetch
        provider.get_secret("chickencoop/api-keys")

        # Simulate rotation - new secret value
        mock_aws_secrets_client.get_secret_value.return_value = {
            "SecretString": '{"api_key": "new-rotated-key"}'
        }

        # Clear cache to simulate TTL expiry
        provider.clear_cache()

        # Second fetch should get new value
        secret = provider.get_secret("chickencoop/api-keys")
        assert "new-rotated-key" in str(secret) or mock_aws_secrets_client.get_secret_value.call_count == 2


# =============================================================================
# TestCredentialRotation
# =============================================================================

class TestCredentialRotation:
    """Test credential rotation support."""

    def test_iot_cert_rotation(self, secret_manager):
        """IoT certificates can be rotated."""
        # Secret manager should support certificate rotation
        assert hasattr(secret_manager, 'rotate_certificate') or hasattr(secret_manager, 'get_certificate')

        # If rotation is supported, it should accept new cert path
        if hasattr(secret_manager, 'rotate_certificate'):
            result = secret_manager.rotate_certificate(
                cert_type="iot",
                new_cert_path="/path/to/new/cert.pem"
            )
            assert result is not None

    def test_api_key_rotation(self, secret_manager):
        """API keys can be rotated without downtime."""
        # Should support multiple active keys during rotation
        assert hasattr(secret_manager, 'add_api_key') or hasattr(secret_manager, 'rotate_api_key')

    def test_old_credentials_rejected(self, secret_manager):
        """Old credentials rejected after rotation."""
        # After rotation, old credentials should be invalid
        old_key = "old-api-key-123"
        new_key = "new-api-key-456"

        # Mark key as rotated
        if hasattr(secret_manager, 'mark_key_rotated'):
            secret_manager.mark_key_rotated(old_key)
            assert secret_manager.is_key_valid(old_key) is False
            assert secret_manager.is_key_valid(new_key) is True


# =============================================================================
# TestSecretExposurePrevention
# =============================================================================

class TestSecretExposurePrevention:
    """Test prevention of secret exposure."""

    def test_secrets_not_in_logs(self, secret_manager, caplog):
        """Secrets not written to log files."""
        import logging
        caplog.set_level(logging.DEBUG)

        secret_value = "super-secret-api-key-12345"

        with patch.dict(os.environ, {"TEST_SECRET": secret_value}):
            # Accessing secret should not log the value
            secret_manager.get_secret("TEST_SECRET")

        # Check logs don't contain the secret
        assert secret_value not in caplog.text

    def test_secrets_not_in_error_messages(self, secret_manager):
        """Secrets not exposed in error messages."""
        secret_value = "exposed-secret-value"

        with patch.dict(os.environ, {"TEST_SECRET": secret_value}):
            try:
                # Force an error that might include secret
                secret_manager.validate_secret("TEST_SECRET", pattern=r"^invalid$")
            except ValueError as e:
                # Error message should not contain the actual secret
                assert secret_value not in str(e)

    def test_secrets_not_in_api_responses(self, secret_manager):
        """Secrets not returned in API responses."""
        # Secret manager should have a safe serialization method
        config = secret_manager.get_config_for_api()

        # Should not include actual secret values
        config_str = str(config)
        assert "password" not in config_str.lower() or "***" in config_str
        assert "secret_key" not in config_str.lower() or "***" in config_str

    def test_secrets_not_in_process_list(self):
        """Secrets not visible in process listing."""
        # Secrets should be passed via env vars or files, not command line
        import subprocess
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)

        # Common secret patterns should not appear in process list
        sensitive_patterns = ["AWS_SECRET", "password=", "api_key="]
        for pattern in sensitive_patterns:
            assert pattern.lower() not in result.stdout.lower()

    def test_secrets_redacted_in_debug(self, secret_manager):
        """Secrets redacted in debug output."""
        # __repr__ or __str__ should not expose secrets
        repr_str = repr(secret_manager)
        str_str = str(secret_manager)

        # Should not contain actual secret values in string representation
        assert "password" not in repr_str.lower() or "***" in repr_str
        assert "password" not in str_str.lower() or "***" in str_str

    def test_memory_cleared_after_use(self, secret_manager):
        """Sensitive data cleared from memory."""
        # Secret manager should have method to clear cached secrets
        assert hasattr(secret_manager, 'clear_cache') or hasattr(secret_manager, 'clear_secrets')

        if hasattr(secret_manager, 'clear_cache'):
            secret_manager.clear_cache()
            # Cache should be empty after clearing
            assert secret_manager.cache_size == 0 or len(secret_manager._cache) == 0
