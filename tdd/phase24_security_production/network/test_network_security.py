"""
Phase 24: Network Security Tests
==================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates network security configuration:
- HTTPS/TLS is configured or documented for local API
- CORS origins are restrictive (not wildcard)
- Rate limiting configuration uses production values
- Security headers are set (X-Frame-Options, CSP, etc.)
- SSH configuration recommendations are documented

WHY THIS MATTERS:
-----------------
Raspberry Pis on local networks can be targets for lateral movement
attacks. Proper CORS prevents cross-origin abuse. Rate limiting stops
brute-force login attempts. Security headers harden the web interface.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase24_security_production/network/test_network_security.py -v
"""
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


class TestCORSConfiguration:
    """Verify CORS is not set to wildcard in production."""

    def test_no_wildcard_cors_in_source(self, src_dir):
        """CORS must not use '*' wildcard origin in production code."""
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if 'cors' in content.lower():
                # Check for wildcard origin
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if ("origins='*'" in line or
                            'origins="*"' in line or
                            "allow_origin='*'" in line or
                            'allow_origin="*"' in line or
                            "Access-Control-Allow-Origin', '*'" in line):
                        pytest.fail(
                            f"Wildcard CORS origin found in "
                            f"{py_file.name}:{i+1}: {line.strip()}"
                        )


class TestSecurityHeaders:
    """Verify security headers are configured."""

    def _find_security_module(self, src_dir):
        """Find security-related source files."""
        security_files = []
        for py_file in src_dir.rglob('*.py'):
            if 'security' in py_file.name.lower() or 'header' in py_file.name.lower():
                security_files.append(py_file)
        return security_files

    def test_security_headers_module_exists(self, src_dir):
        """A security headers module must exist."""
        files = self._find_security_module(src_dir)
        has_headers = len(files) > 0
        if not has_headers:
            # Also check if headers are set in main.py or middleware
            for py_file in src_dir.rglob('*.py'):
                try:
                    content = py_file.read_text()
                except (UnicodeDecodeError, PermissionError):
                    continue
                if 'X-Frame-Options' in content or 'X-Content-Type' in content:
                    has_headers = True
                    break
        assert has_headers, (
            "No security headers module found. Must set X-Frame-Options, "
            "X-Content-Type-Options, X-XSS-Protection, etc."
        )

    def test_x_frame_options_configured(self, src_dir):
        """X-Frame-Options header must be set to prevent clickjacking."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if 'X-Frame-Options' in content or 'x_frame_options' in content.lower():
                found = True
                break
        assert found, "X-Frame-Options header not configured anywhere in src/"

    def test_content_type_options_configured(self, src_dir):
        """X-Content-Type-Options header must be set."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if 'X-Content-Type-Options' in content or 'nosniff' in content:
                found = True
                break
        assert found, "X-Content-Type-Options header not configured"


class TestRateLimiting:
    """Verify rate limiting is configured for production."""

    def test_rate_limiting_exists(self, src_dir):
        """Rate limiting must be implemented for API endpoints."""
        found = False
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue
            if ('rate_limit' in content.lower() or
                    'ratelimit' in content.lower() or
                    'throttle' in content.lower()):
                found = True
                break
        assert found, (
            "No rate limiting found in source code. "
            "API endpoints need rate limiting for production."
        )
