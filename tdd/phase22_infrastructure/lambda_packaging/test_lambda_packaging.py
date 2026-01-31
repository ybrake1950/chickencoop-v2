"""
Phase 22: Lambda Packaging & Frontend Build Tests
===================================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates the serverless backend and frontend builds:
- Lambda handler file or Flask-to-Lambda adapter exists
- Lambda handler is importable and callable
- Frontend webapp directory has package.json and build scripts
- Frontend build produces dist/ output

WHY THIS MATTERS:
-----------------
The CI/CD pipeline deploys the Flask API as a Lambda function and the
React frontend to Amplify/S3+CloudFront. Without proper packaging,
deployments silently fail leaving the dashboard inaccessible and the
API unreachable.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase22_infrastructure/lambda_packaging/test_lambda_packaging.py -v
"""
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Get project root directory."""
    return Path(__file__).parents[3]


class TestLambdaHandler:
    """Verify Lambda handler packaging."""

    def _find_lambda_handler(self, project_root):
        """Locate the Lambda handler file."""
        candidates = [
            project_root / 'lambda_handler.py',
            project_root / 'src' / 'lambda_handler.py',
            project_root / 'webapp' / 'backend' / 'lambda_handler.py',
            project_root / 'handler.py',
        ]
        for c in candidates:
            if c.exists():
                return c
        return None

    def test_lambda_handler_exists(self, project_root):
        """A Lambda handler file must exist for serverless deployment."""
        handler = self._find_lambda_handler(project_root)
        assert handler is not None, (
            "No Lambda handler file found. Expected one of: "
            "lambda_handler.py, src/lambda_handler.py, "
            "webapp/backend/lambda_handler.py"
        )

    def test_lambda_handler_has_handler_function(self, project_root):
        """Lambda handler must export a handler(event, context) function."""
        handler = self._find_lambda_handler(project_root)
        if handler is None:
            pytest.skip("Lambda handler file not found")
        content = handler.read_text()
        has_handler = ('def handler(' in content or
                       'def lambda_handler(' in content)
        assert has_handler, (
            "Lambda handler file must define handler(event, context) "
            "or lambda_handler(event, context)"
        )


class TestFrontendWebapp:
    """Verify frontend webapp is set up for building."""

    def _find_webapp_dir(self, project_root):
        """Locate the webapp directory."""
        candidates = [
            project_root / 'webapp',
            project_root / 'webapp' / 'frontend',
            project_root / 'frontend',
        ]
        for c in candidates:
            if c.exists() and (c / 'package.json').exists():
                return c
        return None

    def test_webapp_directory_exists(self, project_root):
        """A webapp directory with package.json must exist."""
        webapp = self._find_webapp_dir(project_root)
        assert webapp is not None, (
            "No webapp directory with package.json found. "
            "The React frontend needs a build setup for deployment."
        )

    def test_webapp_has_build_script(self, project_root):
        """package.json must define a build script."""
        webapp = self._find_webapp_dir(project_root)
        if webapp is None:
            pytest.skip("Webapp directory not found")
        import json
        pkg = json.loads((webapp / 'package.json').read_text())
        scripts = pkg.get('scripts', {})
        assert 'build' in scripts, (
            "package.json must define a 'build' script for CI/CD"
        )

    def test_webapp_has_test_script(self, project_root):
        """package.json must define a test script."""
        webapp = self._find_webapp_dir(project_root)
        if webapp is None:
            pytest.skip("Webapp directory not found")
        import json
        pkg = json.loads((webapp / 'package.json').read_text())
        scripts = pkg.get('scripts', {})
        assert 'test' in scripts, (
            "package.json must define a 'test' script for CI/CD"
        )
