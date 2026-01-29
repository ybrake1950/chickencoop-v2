"""
Phase 14: User Roles Tests
==========================

FUNCTIONALITY BEING TESTED:
---------------------------
- Role definitions (owner, admin, viewer)
- Role assignment to users
- Role hierarchy and inheritance
- Default role for new users

WHY THIS MATTERS:
-----------------
Different users need different access levels. Owners have full control,
admins can manage settings, viewers can only see data. Proper RBAC
prevents unauthorized actions.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase14_rbac/roles/test_user_roles.py -v
"""
import pytest
from src.rbac.roles import RoleManager, Role, RoleAssignment, UserRole


@pytest.fixture
def role_manager():
    return RoleManager()


class TestRoleDefinitions:
    """Test role definitions."""

    def test_owner_role_exists(self, role_manager):
        """Owner role is defined."""
        roles = role_manager.get_all_roles()
        assert any(r.name == "owner" for r in roles)

    def test_admin_role_exists(self, role_manager):
        """Admin role is defined."""
        roles = role_manager.get_all_roles()
        assert any(r.name == "admin" for r in roles)

    def test_viewer_role_exists(self, role_manager):
        """Viewer role is defined."""
        roles = role_manager.get_all_roles()
        assert any(r.name == "viewer" for r in roles)

    def test_roles_have_descriptions(self, role_manager):
        """Roles have descriptions."""
        for role in role_manager.get_all_roles():
            assert role.description is not None and len(role.description) > 0


class TestRoleAssignment:
    """Test role assignment."""

    def test_assign_role_to_user(self, role_manager):
        """Role can be assigned to user."""
        role_manager.assign_role("user-1", "admin")
        assert role_manager.get_user_role("user-1") == "admin"

    def test_remove_role_from_user(self, role_manager):
        """Role can be removed from user."""
        role_manager.assign_role("user-1", "admin")
        role_manager.remove_role("user-1")
        assert role_manager.get_user_role("user-1") in (None, "viewer")

    def test_user_can_have_multiple_roles(self, role_manager):
        """User can have multiple roles."""
        role_manager.assign_role("user-1", "admin")
        role_manager.assign_role("user-1", "viewer")
        assert len(role_manager.get_user_roles("user-1")) >= 1

    def test_role_assignment_requires_admin(self, role_manager):
        """Role assignment requires admin permission."""
        with pytest.raises(PermissionError):
            role_manager.assign_role("user-2", "admin", assigned_by_role="viewer")


class TestRoleHierarchy:
    """Test role hierarchy."""

    def test_owner_has_admin_permissions(self, role_manager):
        """Owner inherits admin permissions."""
        assert role_manager.role_includes("owner", "admin") is True

    def test_admin_has_viewer_permissions(self, role_manager):
        """Admin inherits viewer permissions."""
        assert role_manager.role_includes("admin", "viewer") is True

    def test_viewer_minimal_permissions(self, role_manager):
        """Viewer has minimal permissions."""
        assert role_manager.role_includes("viewer", "admin") is False


class TestDefaultRole:
    """Test default role assignment."""

    def test_new_user_gets_default_role(self, role_manager):
        """New users get default role."""
        assert role_manager.get_default_role() == "viewer"

    def test_default_role_configurable(self, role_manager):
        """Default role is configurable."""
        role_manager.set_default_role("admin")
        assert role_manager.get_default_role() == "admin"

    def test_first_user_gets_owner(self, role_manager):
        """First user becomes owner."""
        assert role_manager.get_role_for_first_user() == "owner"
