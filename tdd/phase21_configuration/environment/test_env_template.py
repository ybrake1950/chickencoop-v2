"""
Phase 21: Environment Template Tests
======================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the .env.example template:
- .env.example exists with documented variables
- All required environment variables are listed
- Default values are provided where appropriate
- Sensitive values use placeholder markers
- .env is in .gitignore

WHY THIS MATTERS:
-----------------
Without a documented environment template, operators deploying to new
Raspberry Pis won't know which variables to configure. Missing variables
cause silent failures or crashes. The template is the single source of
truth for required configuration.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase21_configuration/environment/test_env_template.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def env_example_path(project_root):
    """Get path to .env.example."""
    return project_root / '.env.example'


@pytest.fixture
def gitignore_path(project_root):
    """Get path to .gitignore."""
    return project_root / '.gitignore'


class TestEnvTemplateExists:
    """Verify .env.example exists and is well-formed."""

    def test_env_example_exists(self, env_example_path):
        """.env.example must exist to guide operator setup."""
        assert env_example_path.exists(), (
            ".env.example not found. Operators need a template showing "
            "which environment variables to configure per device."
        )

    def test_env_example_not_empty(self, env_example_path):
        """.env.example must contain variable declarations."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        content = env_example_path.read_text().strip()
        lines = [l for l in content.splitlines()
                 if l.strip() and not l.strip().startswith('#')]
        assert len(lines) >= 3, ".env.example has too few variable declarations"


class TestRequiredVariablesDeclared:
    """Verify all required variables are in the template."""

    def _get_template_vars(self, env_example_path):
        """Parse variable names from .env.example."""
        if not env_example_path.exists():
            return set()
        content = env_example_path.read_text()
        vars_found = set()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                var_name = line.split('=')[0].strip()
                vars_found.add(var_name)
        return vars_found

    def test_coop_id_declared(self, env_example_path):
        """COOP_ID must be in .env.example."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        vars_found = self._get_template_vars(env_example_path)
        assert 'COOP_ID' in vars_found, "COOP_ID missing from .env.example"

    def test_secret_key_declared(self, env_example_path):
        """SECRET_KEY must be in .env.example."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        vars_found = self._get_template_vars(env_example_path)
        assert 'SECRET_KEY' in vars_found, "SECRET_KEY missing from .env.example"

    def test_testing_declared(self, env_example_path):
        """TESTING must be in .env.example."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        vars_found = self._get_template_vars(env_example_path)
        assert 'TESTING' in vars_found, "TESTING missing from .env.example"

    def test_aws_region_declared(self, env_example_path):
        """AWS_REGION must be in .env.example."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        vars_found = self._get_template_vars(env_example_path)
        assert 'AWS_REGION' in vars_found, "AWS_REGION missing from .env.example"

    def test_log_level_declared(self, env_example_path):
        """LOG_LEVEL must be in .env.example."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        vars_found = self._get_template_vars(env_example_path)
        assert 'LOG_LEVEL' in vars_found, "LOG_LEVEL missing from .env.example"


class TestSensitiveValuesProtected:
    """Verify sensitive values use placeholders, not real secrets."""

    def test_secret_key_uses_placeholder(self, env_example_path):
        """SECRET_KEY must NOT contain an actual key in the template."""
        if not env_example_path.exists():
            pytest.skip(".env.example does not exist yet")
        content = env_example_path.read_text()
        for line in content.splitlines():
            if line.strip().startswith('SECRET_KEY='):
                value = line.split('=', 1)[1].strip()
                assert '<' in value or 'change' in value.lower() or value == '', (
                    "SECRET_KEY in .env.example should use a placeholder "
                    "like <generate-secure-key>, not an actual secret"
                )

    def test_env_in_gitignore(self, gitignore_path):
        """.env must be listed in .gitignore to prevent secret leaks."""
        assert gitignore_path.exists(), ".gitignore not found"
        content = gitignore_path.read_text()
        assert '.env' in content, (
            ".env not in .gitignore — secrets could be committed"
        )
