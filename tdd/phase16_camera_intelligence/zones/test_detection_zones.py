"""
Phase 16: Detection Zones Tests
===============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Configurable motion detection zones
- Per-zone sensitivity settings
- Zone exclusion areas
- Zone visualization

WHY THIS MATTERS:
-----------------
Not all areas of the camera view are equally important. Users can
define zones where motion matters and exclude areas like trees
that cause false positives.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase16_camera_intelligence/zones/test_detection_zones.py -v
"""
import pytest
from src.camera_intelligence.zones import ZoneManager, DetectionZone, ZoneType, ZoneConfig


@pytest.fixture
def manager():
    return ZoneManager()


class TestZoneDefinition:
    """Test zone definition."""

    def test_create_rectangular_zone(self, manager):
        """Rectangular zones can be created."""
        zone = manager.create_zone(name="Nesting", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 200, "height": 150})
        assert zone.zone_type == ZoneType.RECTANGLE

    def test_create_polygon_zone(self, manager):
        """Polygon zones can be created."""
        zone = manager.create_zone(name="Yard", zone_type=ZoneType.POLYGON,
            points=[(0, 0), (200, 0), (200, 200), (0, 200)])
        assert zone.zone_type == ZoneType.POLYGON

    def test_zone_has_name(self, manager):
        """Zones have names."""
        zone = manager.create_zone(name="Nesting Area", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 100, "height": 100})
        assert zone.name == "Nesting Area"

    def test_multiple_zones_supported(self, manager):
        """Multiple zones supported."""
        for i in range(3):
            manager.create_zone(name=f"Zone {i}", zone_type=ZoneType.RECTANGLE,
                coords={"x": i * 100, "y": 0, "width": 90, "height": 90})
        assert len(manager.zones) == 3


class TestZoneSensitivity:
    """Test per-zone sensitivity."""

    def test_zone_sensitivity_configurable(self, manager):
        """Each zone has configurable sensitivity."""
        zone = manager.create_zone(name="Entry", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 100, "height": 100}, sensitivity=0.8)
        assert zone.sensitivity == 0.8

    def test_high_sensitivity_zone(self, manager):
        """High sensitivity detects small motion."""
        zone = manager.create_zone(name="Entry", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 100, "height": 100}, sensitivity=0.9)
        result = manager.check_motion(zone_id=zone.zone_id, motion_amount=0.05)
        assert result.detected is True

    def test_low_sensitivity_zone(self, manager):
        """Low sensitivity ignores small motion."""
        zone = manager.create_zone(name="BG", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 100, "height": 100}, sensitivity=0.2)
        result = manager.check_motion(zone_id=zone.zone_id, motion_amount=0.05)
        assert result.detected is False


class TestZoneExclusion:
    """Test zone exclusion."""

    def test_exclusion_zone_created(self, manager):
        """Exclusion zones can be created."""
        zone = manager.create_zone(name="Trees", zone_type=ZoneType.EXCLUSION,
            coords={"x": 0, "y": 0, "width": 100, "height": 100})
        assert zone.zone_type == ZoneType.EXCLUSION

    def test_motion_in_exclusion_ignored(self, manager):
        """Motion in exclusion zone ignored."""
        zone = manager.create_zone(name="Trees", zone_type=ZoneType.EXCLUSION,
            coords={"x": 0, "y": 0, "width": 100, "height": 100})
        result = manager.check_motion(zone_id=zone.zone_id, motion_amount=0.8)
        assert result.detected is False

    def test_exclusion_overlaps_detection(self, manager):
        """Exclusion takes priority over detection."""
        manager.create_zone(name="Yard", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 200, "height": 200}, sensitivity=0.9)
        manager.create_zone(name="Trees", zone_type=ZoneType.EXCLUSION,
            coords={"x": 50, "y": 50, "width": 50, "height": 50})
        result = manager.check_point(x=75, y=75)
        assert result.excluded is True


class TestZoneVisualization:
    """Test zone visualization."""

    def test_zones_visible_in_preview(self, manager):
        """Zones visible in camera preview."""
        manager.create_zone(name="Yard", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 200, "height": 200})
        overlay = manager.get_overlay(frame_width=640, frame_height=480)
        assert overlay is not None

    def test_zone_editor_ui(self, manager):
        """Zone editor UI works."""
        manager.create_zone(name="Test", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 100, "height": 100})
        editor = manager.get_editor_config()
        assert editor["editable"] is True and len(editor["zones"]) >= 1

    def test_motion_highlighted_in_zone(self, manager):
        """Motion highlighted within zones."""
        zone = manager.create_zone(name="Yard", zone_type=ZoneType.RECTANGLE,
            coords={"x": 0, "y": 0, "width": 200, "height": 200}, sensitivity=0.5)
        result = manager.check_motion(zone_id=zone.zone_id, motion_amount=0.8)
        assert result.detected is True and result.highlight_region is not None
