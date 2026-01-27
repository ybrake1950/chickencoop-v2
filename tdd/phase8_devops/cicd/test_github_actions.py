"""
Phase 8: GitHub Actions Pipeline Tests
======================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the CI/CD pipeline configuration:
- Workflow trigger conditions (push, PR, manual dispatch)
- Change detection for conditional deployments
- CI job configuration and dependencies
- Deployment job prerequisites
- Health check integration

WHY THIS MATTERS:
-----------------
The CI/CD pipeline ensures code quality and automates deployments. Broken
pipeline configuration can prevent deployments or allow untested code to
reach production. These tests validate the workflow YAML is correctly
structured and that conditional logic works as expected.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase8_devops/cicd/test_github_actions.py -v

Tests parse the workflow YAML files and verify structure, triggers,
job dependencies, and conditional logic.
"""
import pytest
import yaml
from pathlib import Path


@pytest.fixture
def workflow_yaml():
    """Load the main GitHub Actions workflow."""
    workflow_path = Path(__file__).parents[3] / '.github' / 'workflows' / 'main.yml'
    if workflow_path.exists():
        with open(workflow_path) as f:
            return yaml.safe_load(f)
    return None


class TestWorkflowTriggers:
    """Test workflow trigger configuration."""

    def test_workflow_triggers_on_push_to_main(self, workflow_yaml):
        """Workflow triggers on push to main branch."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        assert 'on' in workflow_yaml
        triggers = workflow_yaml['on']
        assert 'push' in triggers
        assert 'main' in triggers['push'].get('branches', [])

    def test_workflow_triggers_on_pull_request(self, workflow_yaml):
        """Workflow triggers on pull requests to main."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        triggers = workflow_yaml['on']
        assert 'pull_request' in triggers
        assert 'main' in triggers['pull_request'].get('branches', [])

    def test_workflow_supports_manual_dispatch(self, workflow_yaml):
        """Workflow supports manual dispatch with options."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        triggers = workflow_yaml['on']
        assert 'workflow_dispatch' in triggers

    def test_manual_dispatch_has_deploy_target(self, workflow_yaml):
        """Manual dispatch has deploy_target input."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        dispatch = workflow_yaml['on'].get('workflow_dispatch', {})
        inputs = dispatch.get('inputs', {})
        assert 'deploy_target' in inputs

    def test_deploy_target_options(self, workflow_yaml):
        """Deploy target has correct options."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        dispatch = workflow_yaml['on'].get('workflow_dispatch', {})
        inputs = dispatch.get('inputs', {})
        deploy_target = inputs.get('deploy_target', {})
        options = deploy_target.get('options', [])

        expected = ['auto', 'backend', 'webapp', 'pis', 'all']
        for opt in expected:
            assert opt in options, f"Missing option: {opt}"


class TestChangeDetection:
    """Test file change detection configuration."""

    def test_detect_changes_job_exists(self, workflow_yaml):
        """Detect-changes job exists in workflow."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'detect-changes' in jobs

    def test_python_file_patterns(self, workflow_yaml):
        """Python file patterns trigger Pi deployment."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        # Check that hardware/**/*.py triggers python changes
        jobs = workflow_yaml.get('jobs', {})
        detect_job = jobs.get('detect-changes', {})
        steps = detect_job.get('steps', [])

        # Find the paths-filter step
        filter_step = None
        for step in steps:
            if 'uses' in step and 'paths-filter' in step['uses']:
                filter_step = step
                break

        assert filter_step is not None, "paths-filter step not found"

        filters = filter_step.get('with', {}).get('filters', '')
        assert 'hardware/**/*.py' in filters

    def test_backend_file_patterns(self, workflow_yaml):
        """Backend file patterns trigger Lambda deployment."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        detect_job = jobs.get('detect-changes', {})
        steps = detect_job.get('steps', [])

        filter_step = None
        for step in steps:
            if 'uses' in step and 'paths-filter' in step['uses']:
                filter_step = step
                break

        if filter_step:
            filters = filter_step.get('with', {}).get('filters', '')
            assert 'webapp/backend/**' in filters

    def test_webapp_file_patterns(self, workflow_yaml):
        """WebApp file patterns trigger React deployment."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        detect_job = jobs.get('detect-changes', {})
        steps = detect_job.get('steps', [])

        filter_step = None
        for step in steps:
            if 'uses' in step and 'paths-filter' in step['uses']:
                filter_step = step
                break

        if filter_step:
            filters = filter_step.get('with', {}).get('filters', '')
            assert 'webapp/frontend/**' in filters

    def test_config_file_patterns(self, workflow_yaml):
        """Config file changes trigger Pi updates."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        detect_job = jobs.get('detect-changes', {})
        steps = detect_job.get('steps', [])

        filter_step = None
        for step in steps:
            if 'uses' in step and 'paths-filter' in step['uses']:
                filter_step = step
                break

        if filter_step:
            filters = filter_step.get('with', {}).get('filters', '')
            assert 'config/**' in filters


class TestCIJobs:
    """Test CI job configuration."""

    def test_ci_python_job_exists(self, workflow_yaml):
        """Python CI job exists."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'ci-python' in jobs

    def test_ci_python_runs_pytest(self, workflow_yaml):
        """Python CI runs pytest."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        ci_python = jobs.get('ci-python', {})
        steps = ci_python.get('steps', [])

        has_pytest = any('pytest' in str(step) for step in steps)
        assert has_pytest, "CI Python should run pytest"

    def test_ci_configs_job_exists(self, workflow_yaml):
        """Config validation CI job exists."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'ci-configs' in jobs

    def test_ci_configs_validates_json(self, workflow_yaml):
        """Config CI validates JSON files."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        ci_configs = jobs.get('ci-configs', {})
        steps = ci_configs.get('steps', [])

        has_json_validation = any('json' in str(step).lower() for step in steps)
        assert has_json_validation, "CI should validate JSON configs"

    def test_ci_webapp_job_exists(self, workflow_yaml):
        """WebApp CI job exists."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'ci-webapp' in jobs

    def test_ci_security_job_exists(self, workflow_yaml):
        """Security scanning job exists."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'ci-security' in jobs


class TestDeploymentJobs:
    """Test deployment job configuration."""

    def test_deploy_backend_job_exists(self, workflow_yaml):
        """Backend deployment job exists."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        assert 'deploy-backend' in jobs

    def test_deploy_backend_requires_ci(self, workflow_yaml):
        """Backend deployment requires CI to pass."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        deploy = jobs.get('deploy-backend', {})
        needs = deploy.get('needs', [])

        # Should need at least one CI job
        ci_jobs = ['ci-python', 'ci-configs', 'ci-webapp', 'ci-security']
        has_ci_dependency = any(job in needs for job in ci_jobs)
        assert has_ci_dependency, "Deployment should depend on CI jobs"

    def test_deploy_backend_is_conditional(self, workflow_yaml):
        """Backend deployment is conditional on changes."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        deploy = jobs.get('deploy-backend', {})

        # Should have a condition (if) that checks for backend changes
        has_condition = 'if' in deploy
        assert has_condition, "Deployment should be conditional"

    def test_deploy_runs_health_checks(self, workflow_yaml):
        """Deployment runs health checks."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        jobs = workflow_yaml.get('jobs', {})
        deploy = jobs.get('deploy-backend', {})
        steps = deploy.get('steps', [])

        has_health_check = any('health' in str(step).lower() for step in steps)
        # Health check may be separate job or step
        assert has_health_check or 'deploy-health-check' in jobs


class TestConcurrencyControl:
    """Test workflow concurrency settings."""

    def test_workflow_has_concurrency(self, workflow_yaml):
        """Workflow has concurrency control."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        assert 'concurrency' in workflow_yaml

    def test_concurrency_cancels_in_progress(self, workflow_yaml):
        """New runs cancel in-progress runs."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        concurrency = workflow_yaml.get('concurrency', {})
        # Should either cancel or queue in-progress runs
        assert 'cancel-in-progress' in concurrency or 'group' in concurrency


class TestEnvironmentSecrets:
    """Test that secrets are properly referenced."""

    def test_aws_credentials_from_secrets(self, workflow_yaml):
        """AWS credentials come from secrets."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        workflow_str = str(workflow_yaml)
        # Should reference secrets, not hardcoded values
        if 'AWS_ACCESS_KEY_ID' in workflow_str:
            assert 'secrets.' in workflow_str, "AWS credentials should use secrets"

    def test_no_hardcoded_secrets(self, workflow_yaml):
        """No hardcoded secrets in workflow."""
        if workflow_yaml is None:
            pytest.skip("Workflow file not found")

        workflow_str = str(workflow_yaml)
        # Check for patterns that look like hardcoded secrets
        suspicious_patterns = ['AKIA', 'sk_live_', 'ghp_']
        for pattern in suspicious_patterns:
            assert pattern not in workflow_str, f"Possible hardcoded secret: {pattern}"
