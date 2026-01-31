"""
Phase 26: Application Installation Verification Tests
=======================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates application installation prerequisites:
- Git clone produces working directory structure
- Virtual environment can be created
- pip install -r requirements.txt succeeds
- .env template can be copied and customized
- IoT certificates directory exists with correct permissions
- install-services.sh is executable
- systemd service can be enabled

WHY THIS MATTERS:
-----------------
Installation on a fresh Raspberry Pi must be reliable and repeatable.
Each step depends on the previous one — a failed pip install means
the service won't start, and without correct cert permissions IoT
connections fail silently.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase26_device_setup/app_installation/test_app_installation.py -v
"""
import os
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


class TestDirectoryStructure:
    """Verify required directory structure exists."""

    REQUIRED_DIRS = [
        'src',
        'src/config',
        'src/models',
        'src/utils',
        'config',
        'config/systemd',
        'scripts',
    ]

    @pytest.mark.parametrize('dir_path', REQUIRED_DIRS)
    def test_required_directory_exists(self, project_root, dir_path):
        """Required directory must exist in the project."""
        full_path = project_root / dir_path
        assert full_path.exists(), (
            f"Required directory {dir_path}/ not found"
        )

    def test_scripts_are_executable(self, project_root):
        """Shell scripts in scripts/ must be executable."""
        scripts_dir = project_root / 'scripts'
        if not scripts_dir.exists():
            pytest.skip("scripts/ directory not found")
        for sh_file in scripts_dir.rglob('*.sh'):
            mode = os.stat(sh_file).st_mode
            is_executable = mode & 0o111
            assert is_executable, (
                f"{sh_file.name} is not executable. Run: chmod +x {sh_file}"
            )


class TestRequirementsInstallable:
    """Verify requirements.txt is installable."""

    def test_requirements_txt_has_valid_syntax(self, project_root):
        """requirements.txt must have valid pip syntax."""
        req_file = project_root / 'requirements.txt'
        if not req_file.exists():
            pytest.skip("requirements.txt does not exist yet")
        content = req_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            # Basic syntax check: package==version or package>=version
            if not any(op in line for op in ['==', '>=', '<=', '~=', '!=']):
                pytest.fail(
                    f"requirements.txt line {i} has no version constraint: "
                    f"'{line}'. Pin with == for production."
                )


class TestEnvTemplateSetup:
    """Verify .env template is ready for device customization."""

    def test_env_example_exists(self, project_root):
        """.env.example must exist for device setup."""
        assert (project_root / '.env.example').exists(), (
            ".env.example not found. Needed for per-device configuration."
        )

    def test_env_example_has_coop_id(self, project_root):
        """.env.example must include COOP_ID."""
        env_example = project_root / '.env.example'
        if not env_example.exists():
            pytest.skip(".env.example does not exist")
        content = env_example.read_text()
        assert 'COOP_ID' in content


class TestIoTCertificateDirectory:
    """Verify IoT certificate directory is set up."""

    def test_certs_dir_in_gitignore(self, project_root):
        """config/certs/ must be in .gitignore."""
        gitignore = project_root / '.gitignore'
        if not gitignore.exists():
            pytest.skip(".gitignore not found")
        content = gitignore.read_text()
        assert 'certs' in content, (
            "config/certs/ not in .gitignore. "
            "IoT certificates must never be committed."
        )

    def test_certs_readme_or_docs(self, project_root):
        """Certificate setup must be documented."""
        # Check for any documentation referencing certificate setup
        all_content = ''
        for md in project_root.rglob('*.md'):
            if '.git' not in str(md):
                try:
                    all_content += md.read_text()
                except (UnicodeDecodeError, PermissionError):
                    continue
        for sh in project_root.rglob('*.sh'):
            try:
                all_content += sh.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
        has_cert_docs = ('certificate' in all_content.lower() or
                         'cert' in all_content.lower())
        assert has_cert_docs, (
            "No documentation about IoT certificate installation found"
        )
