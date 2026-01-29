"""Authorization checks."""

from dataclasses import dataclass
from typing import List


@dataclass
class AuthorizationResult:
    """Result of an authorization check."""
    authorized: bool
    http_status_code: int = 200
    error: str = ""


class AuthorizationChecker:
    """Checks user permissions and resource access."""

    def can_access_resource(self, user_id: str, resource_type: str, resource_owner: str) -> bool:
        """Return True if the user owns the requested resource."""
        return user_id == resource_owner

    def can_access_admin_route(self, user_id: str, user_role: str) -> bool:
        """Return True if the user has the admin role."""
        return user_role == "admin"

    def can_access_coop(self, user_coops: List[str], requested_coop: str) -> bool:
        """Return True if the requested coop is in the user's assigned coops."""
        return requested_coop in user_coops

    def check_permission(self, user_id: str, user_role: str, required_permission: str) -> AuthorizationResult:
        """Check whether the user has the required permission."""
        # Admin permissions require admin role
        if required_permission.startswith("admin:"):
            if user_role != "admin":
                return AuthorizationResult(
                    authorized=False,
                    http_status_code=403,
                    error=f"Permission denied: {required_permission} requires admin role",
                )
        return AuthorizationResult(authorized=True)
