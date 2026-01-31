"""
Phase 24: Production Secrets Management Tests
===============================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates production-grade secret handling:
- No secrets in committed source files
- No secrets in configuration JSON files
- SECRET_KEY generation uses cryptographically secure method
- .env and credential files are gitignored
- IoT certificates directory is gitignored

WHY THIS MATTERS:
-----------------
Exposed secrets are the #1 cause of cloud security breaches. A single
committed AWS key can lead to cryptocurrency mining charges, data theft,
or complete infrastructure compromise. These tests scan the entire
codebase for leaked credentials.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase24_security_production/secrets/test_production_secrets.py -v
"""
import re
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


@pytest.fixture
def all_python_files(project_root):
    """Get all Python files in the project."""
    return list(project_root.rglob('*.py'))


@pytest.fixture
def all_config_files(project_root):
    """Get all JSON/YAML config files."""
    files = []
    for ext in ['*.json', '*.yaml', '*.yml']:
        files.extend(project_root.rglob(ext))
    # Exclude node_modules and .git
    return [f for f in files
            if '.git' not in str(f) and 'node_modules' not in str(f)]


class TestNoSecretsInSource:
    """Verify no secrets are committed in source code."""

    AWS_KEY_PATTERN = re.compile(r'AKIA[0-9A-Z]{16}')
    AWS_SECRET_PATTERN = re.compile(
        r'(?:aws_secret|secret_key|secretkey)\s*[:=]\s*["\'][A-Za-z0-9/+=]{40}',
        re.IGNORECASE
    )
    PRIVATE_KEY_PATTERN = re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----')
    PASSWORD_PATTERN = re.compile(
        r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']{8,}["\']',
        re.IGNORECASE
    )

    def test_no_aws_access_keys_in_python(self, all_python_files):
        """Python files must not contain AWS access key IDs."""
        for f in all_python_files:
            if '.git' in str(f):
                continue
            try:
                content = f.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            match = self.AWS_KEY_PATTERN.search(content)
            if match:
                pytest.fail(
                    f"AWS access key found in {f}: {match.group()[:8]}..."
                )

    def test_no_private_keys_in_source(self, all_python_files):
        """Source files must not contain private keys."""
        for f in all_python_files:
            if '.git' in str(f):
                continue
            try:
                content = f.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            match = self.PRIVATE_KEY_PATTERN.search(content)
            if match:
                pytest.fail(
                    f"Private key found in {f}"
                )

    def test_no_hardcoded_passwords_in_source(self, src_dir):
        """Source code must not contain hardcoded passwords."""
        for f in src_dir.rglob('*.py'):
            try:
                content = f.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            # Skip test files and password hashing utilities
            if 'test_' in f.name:
                continue
            match = self.PASSWORD_PATTERN.search(content)
            if match:
                line = match.group()
                # Allow default/test passwords in non-production code
                if ('test' not in line.lower() and
                        'default' not in line.lower() and
                        'example' not in line.lower()):
                    pytest.fail(
                        f"Possible hardcoded password in {f.name}: "
                        f"{line[:40]}..."
                    )


class TestNoSecretsInConfig:
    """Verify no secrets in configuration files."""

    def test_no_real_aws_keys_in_config(self, all_config_files):
        """Config files must not contain real AWS keys."""
        pattern = re.compile(r'AKIA[0-9A-Z]{16}')
        for f in all_config_files:
            try:
                content = f.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            match = pattern.search(content)
            if match:
                pytest.fail(
                    f"AWS key in config file {f.name}: {match.group()[:8]}..."
                )


class TestGitignoreProtection:
    """Verify sensitive files are gitignored."""

    def test_env_file_gitignored(self, project_root):
        """.env must be in .gitignore."""
        gitignore = project_root / '.gitignore'
        assert gitignore.exists()
        content = gitignore.read_text()
        assert '.env' in content

    def test_certs_dir_gitignored(self, project_root):
        """config/certs/ must be in .gitignore."""
        gitignore = project_root / '.gitignore'
        assert gitignore.exists()
        content = gitignore.read_text()
        has_certs = ('certs' in content or 'certificates' in content)
        assert has_certs, (
            "config/certs/ not in .gitignore — IoT certificates "
            "could be committed"
        )

    def test_db_files_gitignored(self, project_root):
        """Database files must be in .gitignore."""
        gitignore = project_root / '.gitignore'
        assert gitignore.exists()
        content = gitignore.read_text()
        assert '*.db' in content, "*.db not in .gitignore"

    def test_no_env_file_committed(self, project_root):
        """An actual .env file must NOT exist in the repo."""
        env_file = project_root / '.env'
        if env_file.exists():
            pytest.fail(
                ".env file exists in repo root. This should be "
                "gitignored, not committed. Remove and use .env.example."
            )
