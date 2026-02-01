"""RBAC roles module for chicken coop application."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Role:
    """A named role with a description."""

    name: str
    description: str
    level: int = 0


@dataclass
class RoleAssignment:
    """Tracks a role assigned to a user."""

    user_id: str
    role_name: str


@dataclass
class UserRole:
    """A user's role entry."""

    user_id: str
    roles: List[str] = field(default_factory=list)


# Predefined roles with hierarchy levels (higher = more permissions)
_DEFAULT_ROLES = [
    Role(name="viewer", description="Can view coop data and status", level=1),
    Role(name="admin", description="Can manage settings and users", level=2),
    Role(name="owner", description="Full control over the coop system", level=3),
]

# Role hierarchy: each role includes all roles at lower levels
_ROLE_HIERARCHY: Dict[str, List[str]] = {
    "owner": ["admin", "viewer"],
    "admin": ["viewer"],
    "viewer": [],
}


class RoleManager:
    """Manages role definitions, assignments, and hierarchy."""

    def __init__(self):
        self._roles: List[Role] = list(_DEFAULT_ROLES)
        self._user_roles: Dict[str, List[str]] = {}
        self._default_role: str = "viewer"

    def get_all_roles(self) -> List[Role]:
        """Return all defined roles."""
        return list(self._roles)

    def assign_role(
        self,
        user_id: str,
        role_name: str,
        assigned_by_role: Optional[str] = None,
    ) -> None:
        """Assign a role to a user.

        If assigned_by_role is provided, it must be admin or owner.
        """
        if assigned_by_role is not None:
            if assigned_by_role not in ("admin", "owner"):
                raise PermissionError("Only admin or owner can assign roles")

        if user_id not in self._user_roles:
            self._user_roles[user_id] = []

        if role_name not in self._user_roles[user_id]:
            self._user_roles[user_id].append(role_name)

    def remove_role(self, user_id: str) -> None:
        """Remove all roles from a user."""
        self._user_roles.pop(user_id, None)

    def get_user_role(self, user_id: str) -> Optional[str]:
        """Return the primary (last assigned) role for a user, or None."""
        roles = self._user_roles.get(user_id)
        if not roles:
            return None
        return roles[-1]

    def get_user_roles(self, user_id: str) -> List[str]:
        """Return all roles assigned to a user."""
        return list(self._user_roles.get(user_id, []))

    def role_includes(self, role_name: str, check_role: str) -> bool:
        """Check if role_name includes (inherits) check_role permissions."""
        if role_name == check_role:
            return True
        included = _ROLE_HIERARCHY.get(role_name, [])
        return check_role in included

    def get_default_role(self) -> str:
        """Return the default role for new users."""
        return self._default_role

    def set_default_role(self, role_name: str) -> None:
        """Set the default role for new users."""
        self._default_role = role_name

    def get_role_for_first_user(self) -> str:
        """Return the role assigned to the first user of the system."""
        return "owner"
