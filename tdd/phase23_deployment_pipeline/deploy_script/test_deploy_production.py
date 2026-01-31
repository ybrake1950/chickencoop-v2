"""
Phase 23: Production Deploy Script Tests
==========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates deploy.sh is production-ready:
- Uses correct remote path (chickencoop-v2)
- Runs pip install on each Pi
- Activates virtual environment
- Performs pre-deployment health check
- Has rollback capability on failure
- Logs deployment actions

WHY THIS MATTERS:
-----------------
deploy.sh is the primary mechanism for pushing code to Raspberry Pis.
A broken deploy script means stale code running on devices, missed
updates, and potential data loss if a bad deploy can't be rolled back.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase23_deployment_pipeline/deploy_script/test_deploy_production.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def deploy_script_path(project_root):
    """Get path to deploy.sh."""
    return project_root / 'deploy.sh'


@pytest.fixture
def deploy_content(deploy_script_path):
    """Load deploy.sh content."""
    if deploy_script_path.exists():
        return deploy_script_path.read_text()
    return None


class TestDeployScriptPaths:
    """Verify deploy.sh uses correct paths."""

    def test_deploy_script_exists(self, deploy_script_path):
        """deploy.sh must exist."""
        assert deploy_script_path.exists(), "deploy.sh not found at project root"

    def test_uses_correct_remote_path(self, deploy_content):
        """deploy.sh must use chickencoop-v2 remote path."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        if 'chickencoop' in deploy_content:
            # Check it's not using old path without -v2
            lines_with_path = [l for l in deploy_content.splitlines()
                               if 'chickencoop' in l and 'ssh' in l.lower()]
            for line in lines_with_path:
                if 'chickencoop' in line and 'chickencoop-v2' not in line:
                    # Allow if it's a variable reference
                    if '$' not in line and '{' not in line:
                        pytest.fail(
                            f"deploy.sh uses old path in: {line.strip()}"
                        )


class TestDeployDependencyInstall:
    """Verify deploy runs dependency installation."""

    def test_installs_requirements(self, deploy_content):
        """deploy.sh must run pip install on each Pi."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_pip = ('pip install' in deploy_content or
                   'pip3 install' in deploy_content or
                   'requirements' in deploy_content)
        assert has_pip, (
            "deploy.sh must install requirements on each Pi. "
            "Add: pip install -r requirements.txt"
        )

    def test_activates_virtual_environment(self, deploy_content):
        """deploy.sh should activate venv before pip install."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_venv = ('venv' in deploy_content or
                    'virtualenv' in deploy_content or
                    'activate' in deploy_content)
        assert has_venv, (
            "deploy.sh should activate virtual environment on each Pi"
        )


class TestDeployRollback:
    """Verify deploy has rollback capability."""

    def test_has_error_handling(self, deploy_content):
        """deploy.sh must handle errors (set -e or explicit checks)."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_error = ('set -e' in deploy_content or
                     '|| ' in deploy_content or
                     'if [' in deploy_content or
                     'trap' in deploy_content)
        assert has_error, (
            "deploy.sh must handle errors. Use 'set -e' or explicit checks."
        )

    def test_has_rollback_mechanism(self, deploy_content):
        """deploy.sh should support rollback on failure."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_rollback = ('rollback' in deploy_content.lower() or
                        'revert' in deploy_content.lower() or
                        'git checkout' in deploy_content or
                        'git stash' in deploy_content or
                        'previous' in deploy_content.lower())
        assert has_rollback, (
            "deploy.sh should have rollback capability for failed deploys"
        )


class TestDeployLogging:
    """Verify deploy logs its actions."""

    def test_has_logging(self, deploy_content):
        """deploy.sh should log deployment progress."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_log = ('echo' in deploy_content or
                   'log' in deploy_content.lower() or
                   'printf' in deploy_content)
        assert has_log, (
            "deploy.sh should log deployment progress for debugging"
        )

    def test_verifies_service_after_deploy(self, deploy_content):
        """deploy.sh must verify service is running after restart."""
        if deploy_content is None:
            pytest.skip("deploy.sh does not exist")
        has_verify = ('systemctl status' in deploy_content or
                      'is-active' in deploy_content or
                      'health' in deploy_content.lower() or
                      'verify' in deploy_content.lower())
        assert has_verify, (
            "deploy.sh must verify service is running after deployment"
        )
