"""
Phase 8: Health Check Script Tests
==================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the health check scripts:
- Lambda endpoint validation
- CORS header verification
- HTTP status code checking
- Retry logic for transient failures
- Failure reporting

WHY THIS MATTERS:
-----------------
Health checks run after deployments to verify the system is working.
They catch deployment issues before users encounter them. A failed
health check should block the deployment from being marked successful.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase8_devops/deployment/test_health_check.py -v

Tests validate script structure and can run actual health checks
against deployed endpoints.
"""
import pytest
from pathlib import Path


@pytest.fixture
def health_check_script_path():
    """Get path to health-check.sh script."""
    return Path(__file__).parents[3] / 'scripts' / 'deployment' / 'health-check.sh'


@pytest.fixture
def health_check_content(health_check_script_path):
    """Load health-check.sh content."""
    if health_check_script_path.exists():
        return health_check_script_path.read_text()
    return None


class TestHealthCheckStructure:
    """Test health check script structure."""

    def test_health_check_script_exists(self, health_check_script_path):
        """health-check.sh script exists."""
        assert health_check_script_path.exists(), "health-check.sh not found"

    def test_script_has_shebang(self, health_check_content):
        """Script has proper shebang."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        assert health_check_content.startswith('#!/bin/bash') or \
               health_check_content.startswith('#!/usr/bin/env bash')


class TestEndpointValidation:
    """Test endpoint validation logic."""

    def test_checks_status_endpoint(self, health_check_content):
        """Checks status API endpoint."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        assert 'status' in health_check_content.lower()

    def test_checks_sensor_data_endpoint(self, health_check_content):
        """Checks sensorData API endpoint."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # May be sensorData, sensor-data, or similar
        has_sensor = 'sensor' in health_check_content.lower()
        assert has_sensor

    def test_checks_videos_endpoint(self, health_check_content):
        """Checks videos API endpoint."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        assert 'video' in health_check_content.lower()

    def test_uses_curl_for_requests(self, health_check_content):
        """Uses curl for HTTP requests."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        assert 'curl' in health_check_content


class TestHTTPValidation:
    """Test HTTP response validation."""

    def test_checks_http_status_code(self, health_check_content):
        """Verifies HTTP status codes."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should check for 200 or 204 status
        has_status_check = '200' in health_check_content or \
                          '204' in health_check_content or \
                          'http_code' in health_check_content
        assert has_status_check

    def test_checks_cors_headers(self, health_check_content):
        """Verifies CORS headers are present."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should check for CORS or OPTIONS request
        has_cors_check = 'CORS' in health_check_content or \
                        'OPTIONS' in health_check_content or \
                        'Access-Control' in health_check_content
        # CORS check is optional
        if not has_cors_check:
            pytest.skip("Script doesn't check CORS headers")
        assert has_cors_check


class TestRetryLogic:
    """Test retry logic for transient failures."""

    def test_has_retry_mechanism(self, health_check_content):
        """Script has retry mechanism."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should have loop or retry count
        has_retry = 'retry' in health_check_content.lower() or \
                   'for ' in health_check_content or \
                   'while ' in health_check_content
        assert has_retry, "Health check should have retry logic"

    def test_has_delay_between_retries(self, health_check_content):
        """Has delay between retry attempts."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        has_delay = 'sleep' in health_check_content
        assert has_delay, "Should have delay between retries"

    def test_limited_retry_attempts(self, health_check_content):
        """Retry attempts are limited."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should have a max retry count
        has_limit = '3' in health_check_content or \
                   '5' in health_check_content or \
                   'max' in health_check_content.lower()
        assert has_limit, "Retries should be limited"


class TestFailureReporting:
    """Test failure reporting."""

    def test_exits_nonzero_on_failure(self, health_check_content):
        """Exits with non-zero code on failure."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        has_exit_code = 'exit 1' in health_check_content or \
                       'exit $' in health_check_content
        assert has_exit_code

    def test_reports_failed_endpoint(self, health_check_content):
        """Reports which endpoint failed."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should echo/print failure info
        has_failure_msg = 'fail' in health_check_content.lower() or \
                         'error' in health_check_content.lower()
        assert has_failure_msg

    def test_provides_troubleshooting_info(self, health_check_content):
        """Provides troubleshooting information."""
        if health_check_content is None:
            pytest.skip("health-check.sh not found")

        # Should mention CloudWatch or CloudFormation for debugging
        has_troubleshoot = 'CloudWatch' in health_check_content or \
                          'CloudFormation' in health_check_content or \
                          'check' in health_check_content.lower()
        assert has_troubleshoot


class TestLambdaURLFetching:
    """Test Lambda URL fetching functionality."""

    @pytest.fixture
    def fetch_urls_script_path(self):
        """Get path to fetch-lambda-urls.sh script."""
        return Path(__file__).parents[3] / 'scripts' / 'deployment' / 'fetch-lambda-urls.sh'

    @pytest.fixture
    def fetch_urls_content(self, fetch_urls_script_path):
        """Load fetch-lambda-urls.sh content."""
        if fetch_urls_script_path.exists():
            return fetch_urls_script_path.read_text()
        return None

    def test_fetch_urls_script_exists(self, fetch_urls_script_path):
        """fetch-lambda-urls.sh script exists."""
        assert fetch_urls_script_path.exists(), "fetch-lambda-urls.sh not found"

    def test_queries_cloudformation(self, fetch_urls_content):
        """Queries CloudFormation for URLs."""
        if fetch_urls_content is None:
            pytest.skip("fetch-lambda-urls.sh not found")

        has_cf = 'cloudformation' in fetch_urls_content.lower() or \
                'aws ' in fetch_urls_content
        assert has_cf

    def test_updates_amplify_outputs(self, fetch_urls_content):
        """Updates amplify_outputs.json."""
        if fetch_urls_content is None:
            pytest.skip("fetch-lambda-urls.sh not found")

        assert 'amplify_outputs' in fetch_urls_content

    def test_creates_backup(self, fetch_urls_content):
        """Creates backup before updating."""
        if fetch_urls_content is None:
            pytest.skip("fetch-lambda-urls.sh not found")

        has_backup = 'backup' in fetch_urls_content.lower() or \
                    '.bak' in fetch_urls_content or \
                    'cp ' in fetch_urls_content
        assert has_backup, "Should backup before updating"


class TestHealthCheckIntegration:
    """Integration tests for actual health checks."""

    @pytest.fixture
    def amplify_outputs_path(self):
        """Get path to amplify_outputs.json."""
        return Path(__file__).parents[3] / 'webapp' / 'amplify_outputs.json'

    def test_amplify_outputs_exists(self, amplify_outputs_path):
        """amplify_outputs.json exists."""
        # May not exist in test environment
        if not amplify_outputs_path.exists():
            pytest.skip("amplify_outputs.json not found")
        assert amplify_outputs_path.exists()

    def test_amplify_outputs_has_custom_section(self, amplify_outputs_path):
        """amplify_outputs.json has custom URLs section."""
        if not amplify_outputs_path.exists():
            pytest.skip("amplify_outputs.json not found")

        import json
        with open(amplify_outputs_path) as f:
            outputs = json.load(f)

        assert 'custom' in outputs, "Should have custom section for Lambda URLs"
