"""RBAC permissions module for chicken coop application."""

import functools
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Permission:
    """A named permission."""
    name: str


# Role-to-permissions mapping
ROLE_PERMISSIONS = {
    "viewer": ["video:view", "settings:read"],
    "admin": ["video:view", "video:delete", "settings:read", "settings:write", "admin:manage"],
    "owner": ["video:view", "video:delete", "settings:read", "settings:write", "admin:manage", "admin:delete"],
}

# All defined permissions
ALL_PERMISSIONS = [
    Permission("video:view"),
    Permission("video:delete"),
    Permission("settings:read"),
    Permission("settings:write"),
    Permission("admin:manage"),
    Permission("admin:delete"),
]


@dataclass
class UserRecord:
    """Tracks per-user data such as assigned coops."""
    user_id: str
    assigned_coops: List[str] = field(default_factory=list)


class PermissionManager:
    """Manages permission definitions and per-user coop assignments."""

    def __init__(self):
        self._users: dict[str, UserRecord] = {}

    def all_permissions(self) -> List[Permission]:
        """Return a list of all defined permissions."""
        return list(ALL_PERMISSIONS)

    def assign_coops(self, user_id: str, coops: List[str]) -> None:
        """Assign a list of coop IDs to a user."""
        if user_id not in self._users:
            self._users[user_id] = UserRecord(user_id=user_id)
        self._users[user_id].assigned_coops = list(coops)

    def get_user(self, user_id: str) -> UserRecord:
        """Return the UserRecord for the given user ID."""
        return self._users[user_id]

    def get_visible_coops(self, user_id: str) -> List[str]:
        """Return the list of coop IDs visible to a user."""
        return list(self._users[user_id].assigned_coops)


class PermissionChecker:
    """Checks permissions for a given role and optional coop assignments."""

    def __init__(self, role: str, user_coops: Optional[List[str]] = None):
        self.role = role
        self.user_coops = user_coops or []

    def has_permission(self, permission_name: str) -> bool:
        """Check whether the current role grants the given permission."""
        role_perms = ROLE_PERMISSIONS.get(self.role, [])
        return permission_name in role_perms

    def can_access_coop(self, coop_id: str) -> bool:
        """Check whether the user can access the specified coop."""
        if self.role == "owner":
            return True
        return coop_id in self.user_coops


def require_permission(permission_name: str, resource_param: Optional[str] = None):
    """Decorator that checks permission before executing the wrapped function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(user, *args, **kwargs):
            role = user.role if hasattr(user, 'role') else user.get('role')
            checker = PermissionChecker(role=role)
            if not checker.has_permission(permission_name):
                raise PermissionError(f"Missing permission: {permission_name}")
            return func(user, *args, **kwargs)
        return wrapper
    return decorator
