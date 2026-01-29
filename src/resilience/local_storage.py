"""Local storage management for offline operation on Raspberry Pi.

This module provides storage monitoring, cleanup, and management functionality
to ensure the device continues operating even with limited SD card space.
"""

import os
import shutil
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class StorageCategory(Enum):
    """Categories for storage allocation and tracking."""
    VIDEOS = "videos"
    SENSOR_DATA = "sensor_data"
    LOGS = "logs"
    SYSTEM = "system"
    ALERTS = "alerts"
    HEADCOUNT = "headcount"


# Mapping of category to directory name
CATEGORY_DIRS = {
    StorageCategory.VIDEOS: "videos",
    StorageCategory.SENSOR_DATA: "sensor_data",
    StorageCategory.LOGS: "logs",
    StorageCategory.SYSTEM: "system",
    StorageCategory.ALERTS: "alerts",
    StorageCategory.HEADCOUNT: "headcount",
}


class LocalStorageManager:
    """Manages local storage for offline operation.

    Handles storage monitoring, cleanup policies, data retention,
    and protection of pending sync data.
    """

    # Default configuration values
    DEFAULT_WARNING_THRESHOLD = 0.80
    DEFAULT_CRITICAL_THRESHOLD = 0.95
    DEFAULT_CLEANUP_THRESHOLD = 0.85
    DEFAULT_CLEANUP_TARGET = 0.70
    DEFAULT_CHECK_INTERVAL = 300  # 5 minutes
    DEFAULT_RESERVED_BYTES = 104857600  # 100MB
    DEFAULT_MAX_PENDING_FILES = 1000
    DEFAULT_MAX_PENDING_AGE_DAYS = 30
    DEFAULT_TMPFS_SIZE_MB = 256
    DEFAULT_OFFLINE_RETENTION_MULTIPLIER = 2

    DEFAULT_ALLOCATIONS = {
        StorageCategory.VIDEOS: 0.60,
        StorageCategory.SENSOR_DATA: 0.20,
        StorageCategory.LOGS: 0.10,
        StorageCategory.SYSTEM: 0.05,
        StorageCategory.ALERTS: 0.03,
        StorageCategory.HEADCOUNT: 0.02,
    }

    DEFAULT_RETENTION_DAYS = {
        StorageCategory.VIDEOS: 3,
        StorageCategory.SENSOR_DATA: 7,
        StorageCategory.LOGS: 7,
        StorageCategory.SYSTEM: 30,
        StorageCategory.ALERTS: 30,
        StorageCategory.HEADCOUNT: 14,
    }

    def __init__(
        self,
        storage_path: Path,
        warning_threshold: float = None,
        critical_threshold: float = None,
        cleanup_threshold: float = None,
        cleanup_target: float = None,
        check_interval_seconds: int = None,
        reserved_system_bytes: int = None,
        allocations: Dict[StorageCategory, float] = None,
        retention_days: Dict[StorageCategory, int] = None,
        max_pending_files: int = None,
        max_pending_age_days: int = None,
        tmpfs_path: str = None,
        tmpfs_size_mb: int = None,
        usb_overflow_path: Path = None,
    ):
        """Initialize the local storage manager.

        Args:
            storage_path: Base path for managed storage.
            warning_threshold: Usage percent to trigger warning (0.0-1.0).
            critical_threshold: Usage percent to trigger critical alert (0.0-1.0).
            cleanup_threshold: Usage percent to trigger cleanup (0.0-1.0).
            cleanup_target: Target usage percent after cleanup (0.0-1.0).
            check_interval_seconds: Interval between storage checks.
            reserved_system_bytes: Bytes reserved for system operations.
            allocations: Storage allocation percentages by category.
            retention_days: Data retention periods by category.
            max_pending_files: Maximum files in pending sync queue.
            max_pending_age_days: Maximum age for pending files.
            tmpfs_path: Path to tmpfs mount for temporary files.
            tmpfs_size_mb: Size of tmpfs in megabytes.
            usb_overflow_path: Path to USB drive for overflow storage.
        """
        self.storage_path = Path(storage_path)
        self.warning_threshold = warning_threshold or self.DEFAULT_WARNING_THRESHOLD
        self.critical_threshold = critical_threshold or self.DEFAULT_CRITICAL_THRESHOLD
        self.cleanup_threshold = cleanup_threshold or self.DEFAULT_CLEANUP_THRESHOLD
        self.cleanup_target = cleanup_target or self.DEFAULT_CLEANUP_TARGET
        self.check_interval_seconds = check_interval_seconds or self.DEFAULT_CHECK_INTERVAL
        self.reserved_system_bytes = reserved_system_bytes or self.DEFAULT_RESERVED_BYTES
        self.max_pending_files = max_pending_files or self.DEFAULT_MAX_PENDING_FILES
        self.max_pending_age_days = max_pending_age_days or self.DEFAULT_MAX_PENDING_AGE_DAYS
        self.tmpfs_path = Path(tmpfs_path) if tmpfs_path else Path("/tmp/chickencoop")
        self.tmpfs_size_mb = tmpfs_size_mb or self.DEFAULT_TMPFS_SIZE_MB

        # Merge provided allocations with defaults
        self._allocations = self.DEFAULT_ALLOCATIONS.copy()
        if allocations:
            self._allocations.update(allocations)

        # Merge provided retention days with defaults
        self._retention_days = self.DEFAULT_RETENTION_DAYS.copy()
        if retention_days:
            self._retention_days.update(retention_days)

        # USB overflow configuration
        self.usb_overflow_path = Path(usb_overflow_path) if usb_overflow_path else None
        self.usb_overflow_enabled = usb_overflow_path is not None

        # Internal state
        self._pending_files: Dict[str, Dict[str, Any]] = {}
        self._cleanup_log: List[Dict[str, Any]] = []
        self._io_errors: List[Dict[str, Any]] = []
        self._storage_events: List[Dict[str, Any]] = []
        self._offline_mode = False

    def get_storage_usage(self) -> Dict[str, Any]:
        """Get current storage usage statistics.

        Returns:
            Dictionary with total_bytes, used_bytes, free_bytes, percent_used.
        """
        stat = shutil.disk_usage(self.storage_path)
        return {
            'total_bytes': stat.total,
            'used_bytes': stat.used,
            'free_bytes': stat.free,
            'percent_used': stat.used / stat.total if stat.total > 0 else 0.0
        }

    def check_storage_status(self) -> Dict[str, Any]:
        """Check storage status against thresholds.

        Returns:
            Dictionary with warning and critical flags.
        """
        usage = self.get_storage_usage()
        percent_used = usage['percent_used']

        return {
            'warning': percent_used >= self.warning_threshold,
            'critical': percent_used >= self.critical_threshold,
            'percent_used': percent_used,
            'free_bytes': usage['free_bytes']
        }

    def get_usage_by_category(self) -> Dict[StorageCategory, int]:
        """Get storage usage broken down by category.

        Returns:
            Dictionary mapping categories to bytes used.
        """
        usage = {}
        for category, dir_name in CATEGORY_DIRS.items():
            category_path = self.storage_path / dir_name
            if category_path.exists():
                total_size = sum(
                    f.stat().st_size for f in category_path.rglob('*') if f.is_file()
                )
                usage[category] = total_size
            else:
                usage[category] = 0
        return usage

    def get_allocation(self, category: StorageCategory) -> float:
        """Get the allocation percentage for a category.

        Args:
            category: The storage category.

        Returns:
            Allocation as a fraction (0.0-1.0).
        """
        return self._allocations.get(category, 0.0)

    def should_cleanup(self, current_usage: float) -> bool:
        """Determine if cleanup should be triggered.

        Args:
            current_usage: Current usage as a fraction (0.0-1.0).

        Returns:
            True if cleanup should be triggered.
        """
        return current_usage >= self.cleanup_threshold

    def cleanup_old_files(
        self,
        category: StorageCategory,
        max_age_days: int,
        protected_files: List[str]
    ) -> List[str]:
        """Clean up old files in a category.

        Args:
            category: Storage category to clean.
            max_age_days: Maximum age in days for files to keep.
            protected_files: List of file paths that should not be deleted.

        Returns:
            List of deleted file paths.
        """
        deleted = []
        category_path = self.storage_path / CATEGORY_DIRS.get(category, "")

        if not category_path.exists():
            return deleted

        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        protected_set = set(protected_files)

        for file_path in category_path.rglob('*'):
            if not file_path.is_file():
                continue

            if str(file_path) in protected_set:
                continue

            # Check if file is pending sync
            if str(file_path) in self._pending_files:
                continue

            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted.append(str(file_path))
                    self._cleanup_log.append({
                        'timestamp': datetime.now().isoformat(),
                        'file': str(file_path),
                        'category': category.value,
                        'reason': f'exceeded max age of {max_age_days} days'
                    })
                except OSError as e:
                    self.record_io_error(f"Failed to delete {file_path}: {e}")

        return deleted

    def get_cleanup_log(self) -> List[Dict[str, Any]]:
        """Get the cleanup action log.

        Returns:
            List of cleanup log entries.
        """
        return self._cleanup_log.copy()

    def get_deletion_priority(self, files: List[str]) -> List[str]:
        """Get files sorted by deletion priority (synced before pending).

        Args:
            files: List of file paths to sort.

        Returns:
            Sorted list with synced files first, pending files last.
        """
        pending_set = set(self._pending_files.keys())
        synced = [f for f in files if f not in pending_set]
        pending = [f for f in files if f in pending_set]

        # Sort pending by priority (low priority first for deletion)
        pending.sort(
            key=lambda f: 0 if self.get_pending_priority(f) == "normal" else 1
        )

        return synced + pending

    def get_retention_days(self, category: StorageCategory) -> int:
        """Get retention period for a category.

        Args:
            category: Storage category.

        Returns:
            Retention period in days.
        """
        base_retention = self._retention_days.get(
            category,
            self.DEFAULT_RETENTION_DAYS.get(category, 7)
        )

        if self._offline_mode:
            return base_retention * self.DEFAULT_OFFLINE_RETENTION_MULTIPLIER

        return base_retention

    def set_offline_mode(self, offline: bool) -> None:
        """Set offline mode status.

        Args:
            offline: True if device is offline.
        """
        self._offline_mode = offline

    def mark_pending_sync(self, file_path: str, priority: str = "normal") -> None:
        """Mark a file as pending cloud sync.

        Args:
            file_path: Path to the file.
            priority: Priority level ("normal" or "high").
        """
        self._pending_files[file_path] = {
            'added': datetime.now().isoformat(),
            'priority': priority
        }

    def get_pending_files(self) -> List[str]:
        """Get list of files pending sync.

        Returns:
            List of file paths.
        """
        return list(self._pending_files.keys())

    def get_pending_priority(self, file_path: str) -> str:
        """Get priority of a pending file.

        Args:
            file_path: Path to the file.

        Returns:
            Priority level or "normal" if not found.
        """
        if file_path in self._pending_files:
            return self._pending_files[file_path].get('priority', 'normal')
        return 'normal'

    def is_protected(self, file_path: str) -> bool:
        """Check if a file is protected from deletion.

        Args:
            file_path: Path to check.

        Returns:
            True if file is protected.
        """
        return file_path in self._pending_files

    def record_io_error(self, message: str) -> None:
        """Record an I/O error.

        Args:
            message: Error message.
        """
        self._io_errors.append({
            'timestamp': datetime.now().isoformat(),
            'message': message
        })

    def get_io_errors(self) -> List[Dict[str, Any]]:
        """Get recorded I/O errors.

        Returns:
            List of error records.
        """
        return self._io_errors.copy()

    def is_filesystem_readonly(self) -> bool:
        """Check if filesystem is read-only.

        Returns:
            True if filesystem is read-only.
        """
        test_file = self.storage_path / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            return False
        except (OSError, IOError):
            return True

    def get_diagnostics(self) -> Dict[str, Any]:
        """Get storage diagnostics information.

        Returns:
            Dictionary with diagnostic information.
        """
        usage = self.get_storage_usage()
        return {
            'storage_health': 'healthy' if not self._io_errors else 'degraded',
            'io_errors': self._io_errors.copy(),
            'filesystem_status': 'readonly' if self.is_filesystem_readonly() else 'writable',
            'usage': usage,
            'pending_files_count': len(self._pending_files),
            'cleanup_log_count': len(self._cleanup_log)
        }

    def get_smart_data(self) -> Optional[Dict[str, Any]]:
        """Get SMART data if available.

        Returns:
            SMART data dictionary or None if not available.
        """
        # SMART data typically requires root access and smartctl
        # Return None as it's generally not available on SD cards
        return None

    def get_motion_frames_path(self) -> Path:
        """Get path for motion detection frames (in tmpfs).

        Returns:
            Path to motion frames directory.
        """
        return self.tmpfs_path / "motion_frames"

    def get_temp_video_path(self) -> Path:
        """Get path for temporary video recording (in tmpfs).

        Returns:
            Path to temp video directory.
        """
        return self.tmpfs_path / "temp_video"

    def tmpfs_requires_manual_cleanup(self) -> bool:
        """Check if tmpfs requires manual cleanup.

        Returns:
            False - tmpfs is automatically cleared on boot.
        """
        return False

    def detect_usb_drives(self) -> List[Dict[str, Any]]:
        """Detect connected USB drives.

        Returns:
            List of detected USB drive information.
        """
        usb_drives = []
        media_paths = [Path("/media"), Path("/mnt")]

        for media_path in media_paths:
            if media_path.exists():
                for mount in media_path.iterdir():
                    if mount.is_dir():
                        try:
                            stat = shutil.disk_usage(mount)
                            usb_drives.append({
                                'path': str(mount),
                                'total_bytes': stat.total,
                                'free_bytes': stat.free
                            })
                        except (OSError, IOError):
                            pass

        return usb_drives

    def handle_usb_removal(self, usb_path: str) -> None:
        """Handle USB drive removal event.

        Args:
            usb_path: Path of removed USB drive.
        """
        self._storage_events.append({
            'timestamp': datetime.now().isoformat(),
            'event': 'usb_removal',
            'path': usb_path,
            'message': f'USB drive removed: {usb_path}'
        })

    def get_storage_events(self) -> List[Dict[str, Any]]:
        """Get storage-related events.

        Returns:
            List of storage events.
        """
        return self._storage_events.copy()

    def get_usb_health(self) -> Optional[Dict[str, Any]]:
        """Get USB drive health information.

        Returns:
            Health information or None if no USB drive.
        """
        if not self.usb_overflow_path or not self.usb_overflow_path.exists():
            return None

        try:
            stat = shutil.disk_usage(self.usb_overflow_path)
            return {
                'path': str(self.usb_overflow_path),
                'total_bytes': stat.total,
                'free_bytes': stat.free,
                'percent_used': stat.used / stat.total if stat.total > 0 else 0.0,
                'status': 'healthy'
            }
        except (OSError, IOError):
            return {'status': 'error', 'path': str(self.usb_overflow_path)}
