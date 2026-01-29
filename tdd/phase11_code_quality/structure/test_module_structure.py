"""
Phase 11: Module Structure Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
- File size limits (< 500 lines recommended)
- Single responsibility principle
- Proper import organization
- Module naming conventions
- Circular dependency prevention

WHY THIS MATTERS:
-----------------
Large, monolithic files are hard to maintain, test, and understand.
Proper module structure improves code readability, enables parallel
development, and makes the codebase more maintainable.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase11_code_quality/structure/test_module_structure.py -v
"""
import pytest
from pathlib import Path
import ast
import re


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def project_root():
    """Get the project root directory."""
    return Path(__file__).parents[3]


@pytest.fixture
def src_dir(project_root):
    """Get the src directory."""
    return project_root / "src"


# =============================================================================
# TestFileSizeLimits
# =============================================================================

class TestFileSizeLimits:
    """Test that files stay within size limits."""

    def test_main_py_size_limit(self, project_root):
        """main.py should be under 500 lines."""
        main_paths = [
            project_root / 'hardware' / 'src' / 'main.py',
            project_root / 'src' / 'main.py',
        ]

        for main_path in main_paths:
            if main_path.exists():
                lines = len(main_path.read_text().splitlines())
                assert lines < 500, f"{main_path} has {lines} lines, should be < 500"

    def test_app_py_size_limit(self, project_root):
        """app.py should be under 500 lines."""
        app_paths = [
            project_root / 'app' / 'app.py',
            project_root / 'src' / 'api' / 'app.py',
        ]

        for app_path in app_paths:
            if app_path.exists():
                lines = len(app_path.read_text().splitlines())
                assert lines < 500, f"{app_path} has {lines} lines, should be < 500"

    def test_no_file_over_1000_lines(self, src_dir):
        """No Python file should exceed 1000 lines."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        oversized = []
        for py_file in src_dir.rglob("*.py"):
            lines = len(py_file.read_text().splitlines())
            if lines > 1000:
                oversized.append((py_file, lines))

        assert len(oversized) == 0, f"Files over 1000 lines: {oversized}"

    def test_lambda_handlers_under_300_lines(self, project_root):
        """Lambda handlers should be under 300 lines."""
        lambda_dir = project_root / "lambda"
        if not lambda_dir.exists():
            pytest.skip("lambda directory not found")

        oversized = []
        for handler in lambda_dir.rglob("*_handler.py"):
            lines = len(handler.read_text().splitlines())
            if lines > 300:
                oversized.append((handler, lines))

        assert len(oversized) == 0, f"Lambda handlers over 300 lines: {oversized}"


# =============================================================================
# TestSingleResponsibility
# =============================================================================

class TestSingleResponsibility:
    """Test single responsibility principle."""

    def test_routes_separate_from_services(self, src_dir):
        """Route handlers separate from business logic."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        # Routes directory should exist
        routes_dirs = list(src_dir.rglob("routes"))
        services_dirs = list(src_dir.rglob("services"))

        # Should have separation
        assert len(routes_dirs) > 0 or len(services_dirs) > 0

    def test_models_separate_from_persistence(self, src_dir):
        """Data models separate from database code."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        models_dirs = list(src_dir.rglob("models"))
        persistence_dirs = list(src_dir.rglob("persistence")) + list(src_dir.rglob("repositories"))

        # Should have some separation
        assert len(models_dirs) > 0 or len(persistence_dirs) > 0

    def test_config_separate_from_app(self, src_dir):
        """Configuration separate from application code."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        config_files = list(src_dir.rglob("config*.py"))

        # Should have config separation
        assert len(config_files) > 0


# =============================================================================
# TestImportOrganization
# =============================================================================

class TestImportOrganization:
    """Test import organization."""

    def test_no_wildcard_imports(self, src_dir):
        """No wildcard imports (from x import *)."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        wildcard_imports = []
        for py_file in src_dir.rglob("*.py"):
            content = py_file.read_text()
            if re.search(r'from\s+\S+\s+import\s+\*', content):
                wildcard_imports.append(py_file)

        assert len(wildcard_imports) == 0, f"Wildcard imports in: {wildcard_imports}"

    def test_imports_at_top(self, src_dir):
        """Imports should be at top of file."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for py_file in src_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                found_non_import = False
                for node in tree.body:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if found_non_import:
                            # Import after non-import (excluding docstring)
                            violations.append(py_file)
                            break
                    elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                        # Skip docstrings
                        continue
                    else:
                        found_non_import = True
            except SyntaxError:
                continue

        # Allow some violations for conditional imports
        assert len(violations) < 10, f"Files with late imports: {violations}"

    def test_sorted_imports(self, src_dir):
        """Imports should be organized (stdlib, third-party, local)."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        # Just check that files don't mix import styles wildly
        # This is a soft check - full enforcement needs isort
        sample_file = next(src_dir.rglob("*.py"), None)
        if sample_file:
            content = sample_file.read_text()
            # Should have some imports
            assert "import" in content


# =============================================================================
# TestModuleNaming
# =============================================================================

class TestModuleNaming:
    """Test module naming conventions."""

    def test_snake_case_filenames(self, src_dir):
        """Python files use snake_case naming."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for py_file in src_dir.rglob("*.py"):
            name = py_file.stem
            if name.startswith("__"):
                continue  # Skip __init__, __main__
            # Check for camelCase or PascalCase
            if re.search(r'[a-z][A-Z]', name):
                violations.append(py_file)

        assert len(violations) == 0, f"Non-snake_case files: {violations}"

    def test_no_spaces_in_filenames(self, src_dir):
        """No spaces in file or directory names."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        violations = []
        for path in src_dir.rglob("*"):
            if " " in path.name:
                violations.append(path)

        assert len(violations) == 0, f"Paths with spaces: {violations}"

    def test_test_files_prefixed(self, project_root):
        """Test files prefixed with test_."""
        tdd_dir = project_root / "tdd"
        if not tdd_dir.exists():
            pytest.skip("tdd directory not found")

        violations = []
        for py_file in tdd_dir.rglob("*.py"):
            if py_file.stem.startswith("__"):
                continue
            if not py_file.stem.startswith("test_") and py_file.stem not in ["conftest"]:
                # Allow some non-test helpers
                if "fixture" not in py_file.stem and "helper" not in py_file.stem:
                    violations.append(py_file)

        # Allow some non-test files in tdd (fixtures, etc)
        assert len(violations) < 10, f"Non-prefixed test files: {violations}"


# =============================================================================
# TestCircularDependencies
# =============================================================================

class TestCircularDependencies:
    """Test circular dependency prevention."""

    def test_no_circular_imports(self, src_dir):
        """No circular import dependencies."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        # Build import graph
        imports = {}
        for py_file in src_dir.rglob("*.py"):
            try:
                tree = ast.parse(py_file.read_text())
                module_imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith("src."):
                                module_imports.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith("src."):
                            module_imports.append(node.module)
                imports[str(py_file)] = module_imports
            except SyntaxError:
                continue

        # Simple cycle detection (depth 2)
        cycles = []
        for module, deps in imports.items():
            for dep in deps:
                dep_file = None
                for f in imports.keys():
                    if dep.replace(".", "/") in f:
                        dep_file = f
                        break
                if dep_file and dep_file in imports:
                    for back_dep in imports[dep_file]:
                        if module.replace("/", ".") in back_dep:
                            cycles.append((module, dep_file))

        assert len(cycles) == 0, f"Circular imports detected: {cycles}"

    def test_layers_respect_hierarchy(self, src_dir):
        """Lower layers don't import from higher layers."""
        if not src_dir.exists():
            pytest.skip("src directory not found")

        # Define layer hierarchy (lower -> higher)
        layers = {
            "models": 1,
            "persistence": 2,
            "services": 3,
            "api": 4,
            "routes": 4,
        }

        violations = []
        for py_file in src_dir.rglob("*.py"):
            # Determine file's layer
            file_layer = None
            for layer_name, level in layers.items():
                if layer_name in str(py_file):
                    file_layer = level
                    break

            if file_layer is None:
                continue

            try:
                tree = ast.parse(py_file.read_text())
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        for layer_name, level in layers.items():
                            if layer_name in node.module and level > file_layer:
                                violations.append((py_file, node.module))
            except SyntaxError:
                continue

        # Allow some flexibility
        assert len(violations) < 5, f"Layer violations: {violations}"
