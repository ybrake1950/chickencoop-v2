"""
Phase 21: Application Configuration Validation Tests
=====================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that production configuration files contain
real values, not placeholder stubs:
- aws_config.json has a real IoT endpoint (not placeholder)
- aws_config.json has a real SNS topic ARN (not 123456789)
- aws_config.json has a real S3 bucket name
- config.json has sensible production defaults
- Configuration can be overridden by environment variables

WHY THIS MATTERS:
-----------------
Placeholder values in configuration files cause silent runtime failures:
S3 uploads fail, IoT messages drop, SNS alerts never arrive. These
failures are hard to debug on remote Raspberry Pis without the right
configuration in place first.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase21_configuration/app_config/test_config_production.py -v
"""
import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def config_dir(project_root):
    """Get the src/config directory."""
    return project_root / 'src' / 'config'


@pytest.fixture
def aws_config_path(config_dir):
    """Get path to aws_config.json."""
    return config_dir / 'aws_config.json'


@pytest.fixture
def app_config_path(config_dir):
    """Get path to config.json."""
    return config_dir / 'config.json'


@pytest.fixture
def aws_config(aws_config_path):
    """Load AWS config as dict."""
    if not aws_config_path.exists():
        return None
    return json.loads(aws_config_path.read_text())


@pytest.fixture
def app_config(app_config_path):
    """Load app config as dict."""
    if not app_config_path.exists():
        return None
    return json.loads(app_config_path.read_text())


class TestAwsConfigNotPlaceholder:
    """Verify AWS config has real values, not stubs."""

    def test_iot_endpoint_not_placeholder(self, aws_config):
        """IoT endpoint must not be the template placeholder."""
        if aws_config is None:
            pytest.skip("aws_config.json does not exist")
        endpoint = aws_config.get('iot', {}).get('endpoint', '')
        assert 'your-iot-endpoint' not in endpoint, (
            f"IoT endpoint is still a placeholder: {endpoint}. "
            "Replace with real AWS IoT endpoint or load from env var."
        )

    def test_sns_topic_arn_not_placeholder(self, aws_config):
        """SNS topic ARN must not contain placeholder account ID."""
        if aws_config is None:
            pytest.skip("aws_config.json does not exist")
        arn = aws_config.get('sns', {}).get('topic_arn', '')
        assert '123456789' not in arn, (
            f"SNS topic ARN contains placeholder account: {arn}. "
            "Replace with real AWS account ID or load from env var."
        )

    def test_s3_bucket_not_generic(self, aws_config):
        """S3 bucket name should be specific, not generic placeholder."""
        if aws_config is None:
            pytest.skip("aws_config.json does not exist")
        bucket = aws_config.get('s3', {}).get('bucket', '')
        generic_names = ['chickencoop-bucket', 'my-bucket', 'test-bucket', '']
        assert bucket not in generic_names, (
            f"S3 bucket name '{bucket}' looks like a placeholder. "
            "Use the actual provisioned bucket name or load from env var."
        )

    def test_aws_config_supports_env_override(self, config_dir):
        """Config loader should support environment variable overrides."""
        # Verify the loader module supports env var overrides
        loader_path = config_dir / 'loader.py'
        if not loader_path.exists():
            pytest.skip("src/config/loader.py does not exist")
        content = loader_path.read_text()
        has_env = ('os.environ' in content or 'getenv' in content or
                   'environment' in content.lower())
        assert has_env, (
            "Config loader should support environment variable overrides "
            "so production values don't need to be in committed JSON files."
        )


class TestAppConfigDefaults:
    """Verify app config has sensible production defaults."""

    def test_sensor_read_interval_reasonable(self, app_config):
        """Sensor read interval should be 60-600 seconds."""
        if app_config is None:
            pytest.skip("config.json does not exist")
        interval = app_config.get('sensors', {}).get('read_interval', 0)
        assert 60 <= interval <= 600, (
            f"Sensor read_interval={interval}s. "
            "Should be 60-600s for production."
        )

    def test_motion_recording_duration_reasonable(self, app_config):
        """Motion recording should be 10-120 seconds."""
        if app_config is None:
            pytest.skip("config.json does not exist")
        duration = app_config.get('motion', {}).get('recording_duration', 0)
        assert 10 <= duration <= 120, (
            f"Motion recording_duration={duration}s. "
            "Should be 10-120s for production."
        )

    def test_headcount_schedule_time_set(self, app_config):
        """Headcount schedule time must be configured."""
        if app_config is None:
            pytest.skip("config.json does not exist")
        schedule = app_config.get('headcount', {}).get('schedule_time', '')
        assert schedule, "Headcount schedule_time must be configured"
        # Validate HH:MM format
        parts = schedule.split(':')
        assert len(parts) == 2, f"Schedule time '{schedule}' not in HH:MM format"
        hour = int(parts[0])
        assert 0 <= hour <= 23, f"Schedule hour {hour} out of range"
