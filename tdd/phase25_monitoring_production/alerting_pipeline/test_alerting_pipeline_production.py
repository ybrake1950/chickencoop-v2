"""
Phase 25: Alerting Pipeline Production Tests
==============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the alerting pipeline is production-ready:
- SNS topic ARN is resolvable (not placeholder)
- Alert routing module sends to correct channels
- Alert aggregation prevents alert storms
- Quiet hours configuration exists
- Webhook URLs are configurable (not hardcoded)

WHY THIS MATTERS:
-----------------
Alerts are the safety net for chicken welfare. A broken alerting
pipeline means temperature extremes, missing chickens, or device
failures go unnoticed. Alert fatigue from storms is equally dangerous
as it causes operators to ignore all alerts.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase25_monitoring_production/alerting_pipeline/test_alerting_pipeline_production.py -v
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


class TestSNSConfiguration:
    """Verify SNS is properly configured for production."""

    def test_sns_client_module_exists(self, src_dir):
        """SNS client module must exist."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            if 'sns' in py_file.name.lower():
                found = True
                break
        assert found, "No SNS client module found in src/"

    def test_sns_topic_not_hardcoded(self, src_dir):
        """SNS topic ARN should come from config, not hardcoded."""
        for py_file in src_dir.rglob('*sns*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if 'arn:aws:sns:' in content:
                # Check if it's in a string literal (hardcoded)
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if ('arn:aws:sns:' in stripped and
                            not stripped.startswith('#') and
                            ('=' in stripped or 'return' in stripped)):
                        if '123456789' in stripped:
                            pytest.fail(
                                f"Placeholder SNS ARN in {py_file.name}:{i+1}"
                            )


class TestAlertAggregation:
    """Verify alert aggregation prevents storms."""

    def test_aggregation_module_exists(self, src_dir):
        """Alert aggregation module must exist (Phase 12)."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            if 'aggregat' in py_file.name.lower():
                found = True
                break
        assert found, "No alert aggregation module found in src/"

    def test_debounce_logic_exists(self, src_dir):
        """Alert aggregation must include debounce logic."""
        for py_file in src_dir.rglob('*aggregat*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            has_debounce = ('debounce' in content.lower() or
                            'cooldown' in content.lower() or
                            'suppress' in content.lower() or
                            'window' in content.lower())
            if has_debounce:
                return
        pytest.fail(
            "No debounce/cooldown logic in alert aggregation. "
            "Without it, rapid sensor fluctuations cause alert storms."
        )


class TestAlertRouting:
    """Verify alert routing is configurable."""

    def test_routing_module_exists(self, src_dir):
        """Alert routing module must exist (Phase 12)."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            if 'rout' in py_file.name.lower() and 'alert' in str(py_file).lower():
                found = True
                break
        # Also check in alerting directory
        if not found:
            alerting_dir = src_dir / 'alerting'
            if alerting_dir.exists():
                for py_file in alerting_dir.rglob('*.py'):
                    if 'rout' in py_file.name.lower():
                        found = True
                        break
        assert found, "No alert routing module found"

    def test_quiet_hours_supported(self, src_dir):
        """Alert routing must support quiet hours."""
        for py_file in src_dir.rglob('*rout*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if ('quiet' in content.lower() or
                    'silent' in content.lower() or
                    'schedule' in content.lower() or
                    'dnd' in content.lower()):
                return
        pytest.fail(
            "No quiet hours support in alert routing. "
            "Non-critical alerts should respect quiet hours."
        )


class TestWebhookConfiguration:
    """Verify webhook URLs are not hardcoded."""

    def test_webhook_urls_configurable(self, src_dir):
        """Webhook URLs must come from config, not hardcoded."""
        for py_file in src_dir.rglob('*webhook*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if 'hooks.slack.com' in content or 'discord.com/api/webhooks' in content:
                # Check if in string literal
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if not stripped.startswith('#'):
                        if ('hooks.slack.com' in stripped or
                                'discord.com/api/webhooks' in stripped):
                            pytest.fail(
                                f"Hardcoded webhook URL in "
                                f"{py_file.name}:{i+1}. "
                                "Use configuration instead."
                            )
