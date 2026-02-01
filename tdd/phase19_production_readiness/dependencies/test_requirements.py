"""
Phase 19: Production Dependencies Tests
========================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates that production dependencies are properly
declared, pinned, and installable:
- requirements.txt exists with all runtime dependencies
- All versions are pinned for reproducibility
- All imports in src/ are covered by declared dependencies
- No conflicting dependency versions
- requirements-dev.txt extends (not duplicates) production deps

WHY THIS MATTERS:
-----------------
Missing or unpinned dependencies cause deployment failures. Every import
in src/ must map to a declared dependency. Unpinned versions lead to
"works on my machine" issues across Raspberry Pis.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase19_production_readiness/dependencies/test_requirements.py -v
"""
import ast
import os
import re
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def requirements_path(project_root):
    """Get path to requirements.txt."""
    return project_root / 'requirements.txt'


@pytest.fixture
def requirements_dev_path(project_root):
    """Get path to requirements-dev.txt."""
    return project_root / 'requirements-dev.txt'


@pytest.fixture
def src_dir(project_root):
    """Get path to src directory."""
    return project_root / 'src'


class TestRequirementsFileExists:
    """Verify requirements.txt exists and is valid."""

    def test_requirements_txt_exists(self, requirements_path):
        """requirements.txt must exist for production deployment."""
        assert requirements_path.exists(), (
            "requirements.txt not found. Production dependencies must be "
            "declared in requirements.txt at the project root."
        )

    def test_requirements_txt_not_empty(self, requirements_path):
        """requirements.txt must contain dependency declarations."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        content = requirements_path.read_text().strip()
        lines = [l for l in content.splitlines()
                 if l.strip() and not l.strip().startswith('#')]
        assert len(lines) > 0, "requirements.txt is empty"

    def test_requirements_dev_txt_exists(self, requirements_dev_path):
        """requirements-dev.txt must exist for testing dependencies."""
        assert requirements_dev_path.exists()


class TestDependencyPinning:
    """Verify all dependencies have pinned versions."""

    def test_all_versions_pinned(self, requirements_path):
        """Every dependency must have a pinned version (==)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        content = requirements_path.read_text()
        lines = [l.strip() for l in content.splitlines()
                 if l.strip() and not l.strip().startswith('#')
                 and not l.strip().startswith('-')]
        unpinned = []
        for line in lines:
            if '==' not in line:
                unpinned.append(line)
        assert len(unpinned) == 0, (
            f"Unpinned dependencies found: {unpinned}. "
            "All production deps must use == for reproducibility."
        )

    def test_no_duplicate_packages(self, requirements_path):
        """No package should be declared more than once."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        content = requirements_path.read_text()
        lines = [l.strip() for l in content.splitlines()
                 if l.strip() and not l.strip().startswith('#')
                 and not l.strip().startswith('-')]
        packages = []
        for line in lines:
            pkg = re.split(r'[=<>!~]', line)[0].strip().lower()
            packages.append(pkg)
        duplicates = [p for p in packages if packages.count(p) > 1]
        assert len(duplicates) == 0, f"Duplicate packages: {set(duplicates)}"


class TestRequiredDependenciesDeclared:
    """Verify all runtime imports are covered by requirements.txt."""

    KNOWN_STDLIB = {
        'abc', 'ast', 'base64', 'collections', 'contextlib', 'csv',
        'dataclasses', 'datetime', 'enum', 'functools', 'gzip', 'hashlib',
        'hmac', 'io', 'json', 'logging', 'math', 'os', 'pathlib',
        'random', 're', 'secrets', 'shlex', 'shutil', 'signal', 'sqlite3',
        'statistics', 'subprocess', 'sys', 'threading', 'time', 'typing',
        'unittest', 'urllib', 'uuid', 'warnings', 'importlib',
        'configparser', 'socket', 'struct', 'tempfile', 'traceback',
    }

    IMPORT_TO_PACKAGE = {
        'flask': 'flask',
        'boto3': 'boto3',
        'botocore': 'botocore',
        'requests': 'requests',
        'numpy': 'numpy',
        'np': 'numpy',
        'cv2': 'opencv-python-headless',
        'psutil': 'psutil',
        'board': 'adafruit-blinka',
        'busio': 'adafruit-blinka',
        'adafruit_ahtx0': 'adafruit-circuitpython-ahtx0',
        'smbus2': 'smbus2',
        'picamera2': 'picamera2',
    }

    def _get_src_imports(self, src_dir):
        """Scan all .py files in src/ for third-party imports."""
        third_party = set()
        for py_file in src_dir.rglob('*.py'):
            try:
                tree = ast.parse(py_file.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split('.')[0]
                        if top not in self.KNOWN_STDLIB and top != 'src':
                            third_party.add(top)
                elif isinstance(node, ast.ImportFrom):
                    if node.level and node.level > 0:
                        continue  # skip relative imports
                    if node.module:
                        top = node.module.split('.')[0]
                        if top not in self.KNOWN_STDLIB and top != 'src':
                            third_party.add(top)
        return third_party

    def _get_declared_packages(self, requirements_path):
        """Parse package names from requirements.txt."""
        if not requirements_path.exists():
            return set()
        content = requirements_path.read_text()
        packages = set()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                pkg = re.split(r'[=<>!~\[]', line)[0].strip().lower()
                packages.add(pkg)
        return packages

    def test_flask_declared(self, requirements_path):
        """Flask must be in requirements.txt (API layer)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        assert 'flask' in pkgs, "flask missing from requirements.txt"

    def test_boto3_declared(self, requirements_path):
        """boto3 must be in requirements.txt (AWS integration)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        assert 'boto3' in pkgs, "boto3 missing from requirements.txt"

    def test_requests_declared(self, requirements_path):
        """requests must be in requirements.txt (webhooks)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        assert 'requests' in pkgs, "requests missing from requirements.txt"

    def test_numpy_declared(self, requirements_path):
        """numpy must be in requirements.txt (motion detection)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        assert 'numpy' in pkgs, "numpy missing from requirements.txt"

    def test_opencv_declared(self, requirements_path):
        """opencv-python-headless must be in requirements.txt (camera/CV)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        has_cv = ('opencv-python-headless' in pkgs or
                  'opencv-python' in pkgs)
        assert has_cv, "opencv-python-headless missing from requirements.txt"

    def test_psutil_declared(self, requirements_path):
        """psutil must be in requirements.txt (system metrics)."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        pkgs = self._get_declared_packages(requirements_path)
        assert 'psutil' in pkgs, "psutil missing from requirements.txt"

    def test_all_src_imports_covered(self, requirements_path, src_dir):
        """Every third-party import in src/ must be in requirements.txt."""
        if not requirements_path.exists():
            pytest.skip("requirements.txt does not exist yet")
        imports = self._get_src_imports(src_dir)
        declared = self._get_declared_packages(requirements_path)
        # Map import names to package names
        missing = []
        for imp in imports:
            pkg_name = self.IMPORT_TO_PACKAGE.get(imp, imp).lower()
            if pkg_name not in declared:
                missing.append(f"{imp} (package: {pkg_name})")
        assert len(missing) == 0, (
            f"Imports not covered by requirements.txt: {missing}"
        )
