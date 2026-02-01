"""Detection zones for configurable motion detection areas."""

import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class ZoneType(Enum):
    """Types of detection zones."""

    RECTANGLE = "rectangle"
    POLYGON = "polygon"
    EXCLUSION = "exclusion"


@dataclass
class ZoneConfig:
    """Configuration for a detection zone."""

    sensitivity: float = 0.5


@dataclass
class DetectionZone:
    """A detection zone within a camera view."""

    zone_id: str
    name: str
    zone_type: ZoneType
    coords: Optional[Dict[str, int]] = None
    points: Optional[List[Tuple[int, int]]] = None
    sensitivity: float = 0.5


@dataclass
class MotionResult:
    """Result of a motion check."""

    detected: bool
    excluded: bool = False
    highlight_region: Optional[Dict[str, Any]] = None


@dataclass
class PointResult:
    """Result of a point check against zones."""

    excluded: bool = False


class ZoneManager:
    """Manages detection zones for a camera view."""

    def __init__(self):
        self.zones: List[DetectionZone] = []
        self._zone_map: Dict[str, DetectionZone] = {}

    def create_zone(
        self,
        name: str,
        zone_type: ZoneType,
        coords: Optional[Dict[str, int]] = None,
        points: Optional[List[Tuple[int, int]]] = None,
        sensitivity: float = 0.5,
    ) -> DetectionZone:
        """Create a new detection zone."""
        zone = DetectionZone(
            zone_id=str(uuid.uuid4()),
            name=name,
            zone_type=zone_type,
            coords=coords,
            points=points,
            sensitivity=sensitivity,
        )
        self.zones.append(zone)
        self._zone_map[zone.zone_id] = zone
        return zone

    def check_motion(self, zone_id: str, motion_amount: float) -> MotionResult:
        """Check if motion is detected in a zone based on its sensitivity."""
        zone = self._zone_map[zone_id]

        if zone.zone_type == ZoneType.EXCLUSION:
            return MotionResult(detected=False, excluded=True)

        threshold = (1.0 - zone.sensitivity) ** 2
        detected = motion_amount >= threshold

        highlight_region = None
        if detected and zone.coords:
            highlight_region = dict(zone.coords)

        return MotionResult(detected=detected, highlight_region=highlight_region)

    def check_point(self, x: int, y: int) -> PointResult:
        """Check if a point falls within an exclusion zone."""
        for zone in self.zones:
            if zone.zone_type == ZoneType.EXCLUSION and zone.coords:
                zx = zone.coords["x"]
                zy = zone.coords["y"]
                zw = zone.coords["width"]
                zh = zone.coords["height"]
                if zx <= x <= zx + zw and zy <= y <= zy + zh:
                    return PointResult(excluded=True)
        return PointResult(excluded=False)

    def get_overlay(self, frame_width: int, frame_height: int) -> Dict[str, Any]:
        """Generate overlay data for rendering zones on a camera preview."""
        return {
            "frame_width": frame_width,
            "frame_height": frame_height,
            "zones": [
                {
                    "zone_id": z.zone_id,
                    "name": z.name,
                    "zone_type": z.zone_type.value,
                    "coords": z.coords,
                    "points": z.points,
                }
                for z in self.zones
            ],
        }

    def get_editor_config(self) -> Dict[str, Any]:
        """Get configuration for the zone editor UI."""
        return {
            "editable": True,
            "zones": [
                {
                    "zone_id": z.zone_id,
                    "name": z.name,
                    "zone_type": z.zone_type.value,
                    "coords": z.coords,
                    "points": z.points,
                    "sensitivity": z.sensitivity,
                }
                for z in self.zones
            ],
        }
