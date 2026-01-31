"""
Phase 19: Package Structure Tests
==================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates Python package structure:
- All src/ subdirectories have __init__.py files
- pyproject.toml or setup.py exists with proper metadata
- Package version is defined
- Python version requirement is declared
- Entry points are configured

WHY THIS MATTERS:
-----------------
Missing __init__.py files prevent Python from recognizing directories as
packages, causing ImportError at runtime. A pyproject.toml provides
standardized packaging metadata, version management, and installability.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase19_production_readiness/packaging/test_package_structure.py -v
"""
import os
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


class TestInitFiles:
    """Verify all packages have __init__.py."""

    def _get_python_dirs(self, src_dir):
        """Find all directories under src/ that contain .py files."""
        py_dirs = set()
        for py_file in src_dir.rglob('*.py'):
            if py_file.name != '__init__.py':
                py_dirs.add(py_file.parent)
        return py_dirs

    def test_src_has_init(self, src_dir):
        """src/ must have __init__.py."""
        assert (src_dir / '__init__.py').exists(), (
            "src/__init__.py missing — required for package imports"
        )

    def test_all_subdirs_have_init(self, src_dir):
        """Every src/ subdirectory with .py files must have __init__.py."""
        py_dirs = self._get_python_dirs(src_dir)
        missing = []
        for d in py_dirs:
            if not (d / '__init__.py').exists():
                rel = d.relative_to(src_dir.parent)
                missing.append(str(rel))
        assert len(missing) == 0, (
            f"Directories missing __init__.py: {sorted(missing)}"
        )

    def test_hardware_init_exists(self, src_dir):
        """src/hardware/__init__.py must exist."""
        hw_dir = src_dir / 'hardware'
        if not hw_dir.exists():
            pytest.skip("src/hardware/ does not exist")
        assert (hw_dir / '__init__.py').exists(), (
            "src/hardware/__init__.py missing"
        )

    def test_hardware_sensors_init_exists(self, src_dir):
        """src/hardware/sensors/__init__.py must exist."""
        sensors_dir = src_dir / 'hardware' / 'sensors'
        if not sensors_dir.exists():
            pytest.skip("src/hardware/sensors/ does not exist")
        assert (sensors_dir / '__init__.py').exists(), (
            "src/hardware/sensors/__init__.py missing"
        )

    def test_hardware_motion_init_exists(self, src_dir):
        """src/hardware/motion/__init__.py must exist."""
        motion_dir = src_dir / 'hardware' / 'motion'
        if not motion_dir.exists():
            pytest.skip("src/hardware/motion/ does not exist")
        assert (motion_dir / '__init__.py').exists(), (
            "src/hardware/motion/__init__.py missing"
        )


class TestProjectPackaging:
    """Verify pyproject.toml or setup.py exists with proper config."""

    def test_pyproject_toml_exists(self, project_root):
        """pyproject.toml or setup.py must exist."""
        has_pyproject = (project_root / 'pyproject.toml').exists()
        has_setup = (project_root / 'setup.py').exists()
        assert has_pyproject or has_setup, (
            "Neither pyproject.toml nor setup.py found. "
            "A packaging file is required for version management and "
            "dependency declaration."
        )

    def test_pyproject_has_project_name(self, project_root):
        """pyproject.toml must declare the project name."""
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.exists():
            pytest.skip("pyproject.toml does not exist yet")
        content = pyproject.read_text()
        assert 'name' in content, "pyproject.toml must declare project name"

    def test_pyproject_has_version(self, project_root):
        """pyproject.toml must declare a version."""
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.exists():
            pytest.skip("pyproject.toml does not exist yet")
        content = pyproject.read_text()
        assert 'version' in content, "pyproject.toml must declare a version"

    def test_pyproject_has_python_requires(self, project_root):
        """pyproject.toml must declare minimum Python version."""
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.exists():
            pytest.skip("pyproject.toml does not exist yet")
        content = pyproject.read_text()
        has_req = ('requires-python' in content or
                   'python_requires' in content)
        assert has_req, (
            "pyproject.toml must declare requires-python >= 3.11"
        )

    def test_pyproject_has_dependencies(self, project_root):
        """pyproject.toml must declare runtime dependencies."""
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.exists():
            pytest.skip("pyproject.toml does not exist yet")
        content = pyproject.read_text()
        assert 'dependencies' in content, (
            "pyproject.toml must declare runtime dependencies"
        )

    def test_pyproject_has_entry_point(self, project_root):
        """pyproject.toml should declare a console entry point."""
        pyproject = project_root / 'pyproject.toml'
        if not pyproject.exists():
            pytest.skip("pyproject.toml does not exist yet")
        content = pyproject.read_text()
        has_entry = ('scripts' in content or
                     'entry-points' in content or
                     'console_scripts' in content)
        assert has_entry, (
            "pyproject.toml should declare console entry point"
        )
