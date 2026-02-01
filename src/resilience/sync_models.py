"""Data models for the sync subsystem.

Defines enums, dataclasses, and result types used across sync modules.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Dict, List, Optional


class SyncStatus(IntEnum):
    """Sync status states."""

    IDLE = 0
    PENDING = 1
    IN_PROGRESS = 2
    PAUSED = 3
    COMPLETED = 4
    FAILED = 5


class SyncPriority(IntEnum):
    """Sync priority levels (lower value = higher priority)."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class SyncItem:
    """Represents an item in the sync queue."""

    type: str  # 'sensor', 'video', 'alert'
    data: Dict[str, Any]
    priority: SyncPriority = SyncPriority.NORMAL
    timestamp: str = ""
    retry_count: int = 0

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class SyncCheckpoint:
    """Checkpoint for resumable sync operations."""

    items_completed: int = 0
    last_item_id: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


@dataclass
class SyncResult:
    """Result of a sync operation."""

    success: bool = False
    items_synced: int = 0
    items_skipped: int = 0
    duplicates_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    iot_published: int = 0
    thumbnails_generated: int = 0
    errors_logged: int = 0
    alerts_aggregated: int = 0
    throttled: bool = False
    timed_out: bool = False
    summary: str = ""
