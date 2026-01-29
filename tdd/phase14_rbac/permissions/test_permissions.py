"""
Phase 14: Permissions Tests
===========================

FUNCTIONALITY BEING TESTED:
---------------------------
- Permission definitions
- Permission checks on resources
- Per-coop access control
- Permission decorator

WHY THIS MATTERS:
-----------------
Fine-grained permissions control what actions users can perform.
Per-coop permissions enable multi-tenant scenarios where different
users manage different coops.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase14_rbac/permissions/test_permissions.py -v
"""
import pytest
from unittest.mock import MagicMock

from src.rbac.permissions import PermissionManager, Permission, PermissionChecker, require_permission


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def permission_manager():
    """Provide a permission manager."""
    return PermissionManager()

@pytest.fixture
def viewer_checker():
    """Provide a permission checker for viewer role."""
    return PermissionChecker(role="viewer")

@pytest.fixture
def admin_checker():
    """Provide a permission checker for admin role."""
    return PermissionChecker(role="admin")


# =============================================================================
# TestPermissionDefinitions
# =============================================================================

class TestPermissionDefinitions:
    """Test permission definitions."""

    def test_video_view_permission(self, permission_manager):
        """video:view permission exists."""
        perms = permission_manager.all_permissions()
        assert any(p.name == "video:view" for p in perms)

    def test_video_delete_permission(self, permission_manager):
        """video:delete permission exists."""
        perms = permission_manager.all_permissions()
        assert any(p.name == "video:delete" for p in perms)

    def test_settings_read_permission(self, permission_manager):
        """settings:read permission exists."""
        perms = permission_manager.all_permissions()
        assert any(p.name == "settings:read" for p in perms)

    def test_settings_write_permission(self, permission_manager):
        """settings:write permission exists."""
        perms = permission_manager.all_permissions()
        assert any(p.name == "settings:write" for p in perms)

    def test_admin_permission(self, permission_manager):
        """admin:* permission exists."""
        perms = permission_manager.all_permissions()
        assert any("admin" in p.name for p in perms)


# =============================================================================
# TestPermissionChecks
# =============================================================================

class TestPermissionChecks:
    """Test permission checks."""

    def test_viewer_can_view_videos(self, viewer_checker):
        """Viewer can view videos."""
        assert viewer_checker.has_permission("video:view") is True

    def test_viewer_cannot_delete_videos(self, viewer_checker):
        """Viewer cannot delete videos."""
        assert viewer_checker.has_permission("video:delete") is False

    def test_admin_can_change_settings(self, admin_checker):
        """Admin can change settings."""
        assert admin_checker.has_permission("settings:write") is True

    def test_viewer_cannot_change_settings(self, viewer_checker):
        """Viewer cannot change settings."""
        assert viewer_checker.has_permission("settings:write") is False


# =============================================================================
# TestCoopPermissions
# =============================================================================

class TestCoopPermissions:
    """Test per-coop permissions."""

    def test_user_assigned_to_coop(self, permission_manager):
        """User can be assigned to specific coops."""
        permission_manager.assign_coops("user-1", ["coop1"])
        user = permission_manager.get_user("user-1")
        assert "coop1" in user.assigned_coops

    def test_user_only_sees_assigned_coops(self, permission_manager):
        """User only sees coops they're assigned to."""
        permission_manager.assign_coops("user-1", ["coop1"])
        visible = permission_manager.get_visible_coops("user-1")
        assert "coop1" in visible
        assert "coop2" not in visible

    def test_cross_coop_access_denied(self, permission_manager):
        """Access to unassigned coop denied."""
        permission_manager.assign_coops("user-1", ["coop1"])
        checker = PermissionChecker(role="viewer", user_coops=["coop1"])
        assert checker.can_access_coop("coop2") is False

    def test_owner_sees_all_coops(self, permission_manager):
        """Owner sees all coops."""
        checker = PermissionChecker(role="owner")
        assert checker.can_access_coop("coop1") is True
        assert checker.can_access_coop("coop2") is True


# =============================================================================
# TestPermissionDecorator
# =============================================================================

class TestPermissionDecorator:
    """Test permission decorator."""

    def test_require_permission_decorator(self):
        """@require_permission decorator works."""
        @require_permission("video:view")
        def view_videos(user):
            return "videos"

        admin_user = MagicMock(role="admin")
        result = view_videos(admin_user)
        assert result == "videos"

    def test_missing_permission_returns_403(self):
        """Missing permission returns 403."""
        @require_permission("admin:delete")
        def delete_data(user):
            return "deleted"

        viewer_user = MagicMock(role="viewer")
        with pytest.raises(PermissionError):
            delete_data(viewer_user)

    def test_permission_with_resource_id(self):
        """Permission check includes resource ID."""
        @require_permission("video:view", resource_param="video_id")
        def view_video(user, video_id):
            return f"video-{video_id}"

        admin_user = MagicMock(role="admin")
        result = view_video(admin_user, video_id="123")
        assert result == "video-123"

    def test_permission_checked_before_handler(self):
        """Permission checked before handler executes."""
        handler = MagicMock(return_value="result")

        @require_permission("admin:delete")
        def protected_handler(user):
            return handler()

        viewer_user = MagicMock(role="viewer")
        with pytest.raises(PermissionError):
            protected_handler(viewer_user)

        handler.assert_not_called()
