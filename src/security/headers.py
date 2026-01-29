"""Security headers middleware."""

from typing import Dict


class SecurityHeadersMiddleware:
    """Adds security headers to responses."""

    def __init__(self, enable_hsts: bool = False):
        self._enable_hsts = enable_hsts

    def get_security_headers(self, sensitive: bool = False) -> Dict[str, str]:
        """Return a dictionary of security headers to add to responses."""
        headers: Dict[str, str] = {
            "Content-Security-Policy": "default-src 'self'",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }

        if self._enable_hsts:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        if sensitive:
            headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
            headers["Pragma"] = "no-cache"

        return headers
