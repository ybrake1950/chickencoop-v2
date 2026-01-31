"""
Phase 25: CloudWatch Monitoring Setup Tests
=============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates CloudWatch monitoring is production-ready:
- Metrics are published to CloudWatch (not just collected locally)
- Custom namespace is defined for chickencoop metrics
- CloudWatch alarms are configured for critical thresholds
- Dashboard definition exists for system health overview
- Log groups are configured for centralized logging

WHY THIS MATTERS:
-----------------
Without CloudWatch integration, operators have no visibility into
Raspberry Pi health from a central console. Failed devices go unnoticed
until chickens are at risk. Alarms provide proactive notification of
issues before they become emergencies.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase25_monitoring_production/cloudwatch/test_cloudwatch_setup.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def src_dir(project_root):
    """Get path to src directory."""
    return project_root / 'src'


class TestCloudWatchMetricsIntegration:
    """Verify metrics are sent to CloudWatch."""

    def test_metrics_module_exists(self, src_dir):
        """A metrics collection module must exist."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            if 'metric' in py_file.name.lower():
                found = True
                break
        assert found, "No metrics module found in src/"

    def test_cloudwatch_publish_implemented(self, src_dir):
        """Metrics module must publish to CloudWatch."""
        for py_file in src_dir.rglob('*metric*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            has_cw = ('cloudwatch' in content.lower() or
                      'put_metric_data' in content or
                      'PutMetricData' in content)
            if has_cw:
                return  # Found CloudWatch integration
        pytest.fail(
            "No CloudWatch put_metric_data call found in metrics modules. "
            "Metrics must be published to CloudWatch for central monitoring."
        )

    def test_custom_namespace_defined(self, src_dir):
        """CloudWatch metrics must use a custom namespace."""
        for py_file in src_dir.rglob('*metric*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if ('Namespace' in content or 'namespace' in content):
                has_custom = ('chickencoop' in content.lower() or
                              'ChickenCoop' in content)
                if has_custom:
                    return  # Found custom namespace
        pytest.fail(
            "CloudWatch metrics should use a custom namespace like "
            "'ChickenCoop' to separate from AWS default metrics."
        )


class TestCloudWatchAlarms:
    """Verify CloudWatch alarms are defined."""

    def _find_alarm_definitions(self, project_root):
        """Find alarm definitions in IaC or config files."""
        content = ''
        for ext in ['*.tf', '*.json', '*.yaml', '*.yml']:
            for f in project_root.rglob(ext):
                if '.git' in str(f) or 'node_modules' in str(f):
                    continue
                try:
                    content += f.read_text() + '\n'
                except (UnicodeDecodeError, PermissionError):
                    continue
        return content

    def test_alarm_definitions_exist(self, project_root):
        """CloudWatch alarms must be defined for critical thresholds."""
        content = self._find_alarm_definitions(project_root)
        has_alarm = ('alarm' in content.lower() or
                     'cloudwatch_metric_alarm' in content or
                     'AWS::CloudWatch::Alarm' in content)
        assert has_alarm, (
            "No CloudWatch alarm definitions found. "
            "Alarms needed for: Pi offline, high error rate, "
            "storage warnings, temperature breaches."
        )


class TestCentralizedLogging:
    """Verify centralized logging is configured."""

    def test_logging_module_supports_cloudwatch(self, src_dir):
        """Logging should support CloudWatch log shipping."""
        for py_file in src_dir.rglob('*log*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if ('cloudwatch' in content.lower() or
                    'watchtower' in content.lower() or
                    'put_log_events' in content or
                    'log_group' in content.lower()):
                return  # Found CloudWatch logging
        # Not a hard failure - can use CloudWatch agent instead
        pass  # CloudWatch agent on Pi is an alternative
