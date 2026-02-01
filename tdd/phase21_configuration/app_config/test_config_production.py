"""
Phase 21: Application Configuration Validation Tests
=====================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that production configuration uses environment
variable overrides for sensitive AWS values, not hard-coded JSON:
- Environment variables override aws_config.json values at load time
- IOT_ENDPOINT env var overrides iot.endpoint in JSON
- SNS_TOPIC_ARN env var overrides sns.topic_arn in JSON
- S3_BUCKET env var overrides s3.bucket in JSON
- config.json has sensible production defaults
- Configuration loader supports environment variable overrides

WHY THIS MATTERS:
-----------------
Hard-coded AWS identifiers in committed JSON files expose account IDs,
resource names, and endpoints in git history. Environment variable
overrides keep secrets out of the repository and allow per-device
configuration on deployed Raspberry Pis.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase21_configuration/app_config/test_config_production.py -v
"""
import json
import os
from pathlib import Path
from unittest.mock import patch

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


class TestAwsConfigEnvOverrides:
    """Verify AWS config values are loaded from environment variables."""

    def test_iot_endpoint_from_env(self, aws_config_path):
        """IOT_ENDPOINT env var must override the JSON value."""
        from src.config.loader import load_aws_config_with_overrides

        fake_endpoint = "abc123-ats.iot.us-east-1.amazonaws.com"
        with patch.dict(os.environ, {"IOT_ENDPOINT": fake_endpoint}):
            config = load_aws_config_with_overrides(aws_config_path)
        assert config['iot']['endpoint'] == fake_endpoint, (
            "IOT_ENDPOINT env var did not override iot.endpoint in aws_config.json. "
            "Ensure load_aws_config_with_overrides applies IOT_ENDPOINT."
        )

    def test_sns_topic_arn_from_env(self, aws_config_path):
        """SNS_TOPIC_ARN env var must override the JSON value."""
        from src.config.loader import load_aws_config_with_overrides

        fake_arn = "arn:aws:sns:us-east-1:999888777666:prod-alerts"
        with patch.dict(os.environ, {"SNS_TOPIC_ARN": fake_arn}):
            config = load_aws_config_with_overrides(aws_config_path)
        assert config['sns']['topic_arn'] == fake_arn, (
            "SNS_TOPIC_ARN env var did not override sns.topic_arn in aws_config.json. "
            "Ensure load_aws_config_with_overrides applies SNS_TOPIC_ARN."
        )

    def test_s3_bucket_from_env(self, aws_config_path):
        """S3_BUCKET env var must override the JSON value."""
        from src.config.loader import load_aws_config_with_overrides

        fake_bucket = "my-prod-chickencoop-media"
        with patch.dict(os.environ, {"S3_BUCKET": fake_bucket}):
            config = load_aws_config_with_overrides(aws_config_path)
        assert config['s3']['bucket'] == fake_bucket, (
            "S3_BUCKET env var did not override s3.bucket in aws_config.json. "
            "Ensure load_aws_config_with_overrides applies S3_BUCKET."
        )

    def test_aws_config_supports_env_override(self, config_dir):
        """Config loader should support environment variable overrides."""
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
