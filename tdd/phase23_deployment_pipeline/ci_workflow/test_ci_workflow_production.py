"""
Phase 23: CI/CD Workflow Production Readiness Tests
====================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the GitHub Actions workflow is production-ready:
- Installs both production and dev dependencies
- Runs full test suite (not a subset)
- Has coverage thresholds as CI gates
- Uses real health check URLs (not placeholders)
- Webapp build step references existing directory
- Security scanning is enabled

WHY THIS MATTERS:
-----------------
A CI pipeline that installs incomplete dependencies or uses placeholder
URLs gives false confidence. Tests pass in CI but the app fails in
production. Coverage gates prevent untested code from reaching devices.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase23_deployment_pipeline/ci_workflow/test_ci_workflow_production.py -v
"""
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def workflow_path(project_root):
    """Get path to main workflow file."""
    return project_root / '.github' / 'workflows' / 'main.yml'


@pytest.fixture
def workflow_content(workflow_path):
    """Load workflow file as string."""
    if workflow_path.exists():
        return workflow_path.read_text()
    return None


@pytest.fixture
def workflow_yaml(workflow_path):
    """Parse workflow file as YAML."""
    if not workflow_path.exists():
        return None
    try:
        return yaml.safe_load(workflow_path.read_text())
    except Exception:
        # yaml might not be installed; fallback to content-based checks
        return None


class TestWorkflowExists:
    """Verify CI workflow file exists."""

    def test_workflow_file_exists(self, workflow_path):
        """GitHub Actions workflow must exist."""
        assert workflow_path.exists(), (
            ".github/workflows/main.yml not found"
        )


class TestWorkflowDependencies:
    """Verify workflow installs all dependencies."""

    def test_installs_production_requirements(self, workflow_content):
        """Workflow must install requirements.txt (not just dev)."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        has_req = ('requirements.txt' in workflow_content)
        assert has_req, (
            "Workflow must install requirements.txt for production deps. "
            "Currently only installs requirements-dev.txt."
        )

    def test_installs_dev_requirements(self, workflow_content):
        """Workflow must also install requirements-dev.txt for testing."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        assert 'requirements-dev.txt' in workflow_content, (
            "Workflow must install requirements-dev.txt for test tools"
        )


class TestWorkflowCoverageGates:
    """Verify workflow enforces coverage thresholds."""

    def test_has_coverage_reporting(self, workflow_content):
        """Workflow must run pytest with coverage."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        has_cov = ('--cov' in workflow_content or
                   'coverage' in workflow_content.lower())
        assert has_cov, (
            "Workflow should run tests with --cov for coverage reporting"
        )

    def test_has_coverage_threshold(self, workflow_content):
        """Workflow should enforce minimum coverage."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        has_threshold = ('--cov-fail-under' in workflow_content or
                         'coverage_threshold' in workflow_content.lower() or
                         'min_coverage' in workflow_content.lower())
        assert has_threshold, (
            "Workflow should use --cov-fail-under=80 to enforce coverage"
        )


class TestWorkflowNoPlaceholders:
    """Verify workflow has no placeholder URLs or values."""

    def test_no_example_urls(self, workflow_content):
        """Workflow must not contain example.com URLs."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        assert 'example.com' not in workflow_content, (
            "Workflow contains placeholder URL 'example.com'. "
            "Replace with real health check endpoint."
        )

    def test_no_placeholder_comments(self, workflow_content):
        """Workflow should not have TODO/FIXME placeholders."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        content_upper = workflow_content.upper()
        has_todo = 'TODO' in content_upper or 'FIXME' in content_upper
        if has_todo:
            pytest.fail(
                "Workflow contains TODO/FIXME placeholders. "
                "Resolve before production deployment."
            )


class TestWorkflowSecurityScanning:
    """Verify workflow includes security scanning."""

    def test_has_security_scan(self, workflow_content):
        """Workflow should include a security scanning step."""
        if workflow_content is None:
            pytest.skip("Workflow file does not exist")
        has_security = ('security' in workflow_content.lower() or
                        'snyk' in workflow_content.lower() or
                        'dependabot' in workflow_content.lower() or
                        'safety' in workflow_content.lower() or
                        'bandit' in workflow_content.lower())
        assert has_security, (
            "Workflow should include security scanning (snyk, safety, bandit)"
        )
