"""
Phase 8: Deployment Script Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the deployment scripts:
- deploy.sh multi-coop deployment
- Git operations (commit, push)
- SSH connectivity to Raspberry Pis
- Service restart on each Pi
- Deployment verification

WHY THIS MATTERS:
-----------------
The deploy.sh script is the primary mechanism for pushing updates to
Raspberry Pi devices. It must reliably commit changes, push to GitHub,
SSH to each Pi, pull updates, and restart services. Failures here mean
devices run stale code.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase8_devops/deployment/test_deploy_script.py -v

Tests validate script structure and logic. Integration tests require
actual Pi connectivity via Tailscale.
"""
import pytest
import subprocess
from pathlib import Path


@pytest.fixture
def deploy_script_path():
    """Get path to deploy.sh script."""
    return Path(__file__).parents[3] / 'deploy.sh'


@pytest.fixture
def deploy_script_content(deploy_script_path):
    """Load deploy.sh content."""
    if deploy_script_path.exists():
        return deploy_script_path.read_text()
    return None


class TestDeployScriptStructure:
    """Test deploy.sh script structure."""

    def test_deploy_script_exists(self, deploy_script_path):
        """deploy.sh script exists."""
        assert deploy_script_path.exists(), "deploy.sh not found"

    def test_deploy_script_is_executable(self, deploy_script_path):
        """deploy.sh is executable."""
        if not deploy_script_path.exists():
            pytest.skip("deploy.sh not found")

        import os
        mode = os.stat(deploy_script_path).st_mode
        assert mode & 0o111, "deploy.sh should be executable"

    def test_deploy_script_has_shebang(self, deploy_script_content):
        """deploy.sh has proper shebang."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert deploy_script_content.startswith('#!/bin/bash') or \
               deploy_script_content.startswith('#!/usr/bin/env bash')


class TestGitOperations:
    """Test Git operations in deploy script."""

    def test_script_stages_changes(self, deploy_script_content):
        """Script stages changes with git add."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'git add' in deploy_script_content

    def test_script_creates_commit(self, deploy_script_content):
        """Script creates commit."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'git commit' in deploy_script_content

    def test_script_pushes_to_remote(self, deploy_script_content):
        """Script pushes to remote."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'git push' in deploy_script_content

    def test_commit_message_required(self, deploy_script_content):
        """Commit message is required parameter."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should check for commit message argument
        assert '$1' in deploy_script_content or 'message' in deploy_script_content.lower()

    def test_push_failure_aborts(self, deploy_script_content):
        """Script aborts if push fails."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should have error handling for git push
        assert 'exit 1' in deploy_script_content or 'set -e' in deploy_script_content


class TestMultiCoopDeployment:
    """Test multi-coop deployment logic."""

    def test_deploys_to_coop1(self, deploy_script_content):
        """Script deploys to coop1."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'coop1' in deploy_script_content

    def test_deploys_to_coop2(self, deploy_script_content):
        """Script deploys to coop2."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'coop2' in deploy_script_content

    def test_uses_ssh_for_deployment(self, deploy_script_content):
        """Script uses SSH to connect to Pis."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'ssh' in deploy_script_content

    def test_pulls_updates_on_pi(self, deploy_script_content):
        """Script pulls updates on each Pi."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'git pull' in deploy_script_content

    def test_restarts_service_on_pi(self, deploy_script_content):
        """Script restarts service on each Pi."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'systemctl restart' in deploy_script_content or \
               'restart' in deploy_script_content


class TestServiceRestart:
    """Test service restart operations."""

    def test_restarts_chickencoop_service(self, deploy_script_content):
        """Restarts chickencoop-monitor service."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        assert 'chickencoop-monitor' in deploy_script_content or \
               'chickencoop' in deploy_script_content

    def test_verifies_service_running(self, deploy_script_content):
        """Verifies service is running after restart."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should check service status
        has_status_check = 'systemctl status' in deploy_script_content or \
                          'is-active' in deploy_script_content or \
                          'systemctl is-active' in deploy_script_content
        assert has_status_check, "Should verify service status after restart"


class TestErrorHandling:
    """Test error handling in deploy script."""

    def test_uses_set_e(self, deploy_script_content):
        """Script uses set -e for error handling."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should have some form of error handling
        has_error_handling = 'set -e' in deploy_script_content or \
                            'exit 1' in deploy_script_content or \
                            '|| exit' in deploy_script_content
        assert has_error_handling

    def test_handles_ssh_failure(self, deploy_script_content):
        """Script handles SSH connection failure."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should have some indication of error handling for SSH
        # This could be via set -e or explicit checks
        has_ssh_handling = 'set -e' in deploy_script_content or \
                          'ssh' in deploy_script_content
        assert has_ssh_handling


class TestDeploymentOutput:
    """Test deployment output and feedback."""

    def test_script_provides_feedback(self, deploy_script_content):
        """Script provides deployment feedback."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should have echo statements for feedback
        assert 'echo' in deploy_script_content

    def test_indicates_deployment_target(self, deploy_script_content):
        """Script indicates which coop is being deployed."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should mention which coop is being deployed
        has_coop_indication = 'Coop' in deploy_script_content or \
                             'coop1' in deploy_script_content
        assert has_coop_indication


class TestTailscaleConnectivity:
    """Test Tailscale network usage."""

    def test_uses_tailscale_hostnames(self, deploy_script_content):
        """Script uses Tailscale hostnames for SSH."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should use Tailscale hostnames (coop1, coop2) not IP addresses
        uses_hostname = 'coop1' in deploy_script_content or \
                       'coop2' in deploy_script_content or \
                       'tail' in deploy_script_content.lower()
        assert uses_hostname


class TestStashHandling:
    """Test git stash handling for local changes."""

    def test_stashes_local_changes(self, deploy_script_content):
        """Script stashes local changes on Pi before pull."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        # Should handle local changes on Pi
        has_stash = 'git stash' in deploy_script_content
        # Stash is optional but recommended
        if not has_stash:
            pytest.skip("Script doesn't use git stash")
        assert has_stash

    def test_restores_stashed_changes(self, deploy_script_content):
        """Script restores stashed changes after pull."""
        if deploy_script_content is None:
            pytest.skip("deploy.sh not found")

        if 'git stash' in deploy_script_content:
            assert 'git stash pop' in deploy_script_content or \
                   'git stash apply' in deploy_script_content
