"""
Phase 9: Local Storage Management Tests
=======================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates local storage management for offline operation:
- SD card space monitoring and management
- Data retention policies during extended outages
- Priority-based storage allocation
- Storage health monitoring
- Automatic cleanup policies

WHY THIS MATTERS:
-----------------
During extended network outages, the Raspberry Pi must manage limited
SD card storage wisely. Without proper management, the disk could fill
up and cause the system to fail. Smart storage management ensures:
1. Critical data is never lost
2. System continues operating even with limited space
3. Oldest/least important data is cleaned first

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase9_resilience/storage/test_local_storage.py -v

Tests verify storage management behavior under constrained conditions.
"""
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import tempfile
import os

from src.resilience.local_storage import LocalStorageManager, StorageCategory


class TestStorageMonitoring:
    """Test storage space monitoring."""

    def test_storage_usage_tracked(self, tmp_path):
        """Current storage usage is tracked."""
        manager = LocalStorageManager(storage_path=tmp_path)
        usage = manager.get_storage_usage()

        assert 'total_bytes' in usage
        assert 'used_bytes' in usage
        assert 'free_bytes' in usage
        assert 'percent_used' in usage
        assert usage['total_bytes'] > 0

    def test_storage_threshold_warning(self, tmp_path):
        """Warning logged when storage exceeds threshold."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            warning_threshold=0.80
        )

        # Simulate 85% usage
        with patch.object(manager, 'get_storage_usage') as mock_usage:
            mock_usage.return_value = {
                'total_bytes': 1000000,
                'used_bytes': 850000,
                'free_bytes': 150000,
                'percent_used': 0.85
            }

            status = manager.check_storage_status()
            assert status['warning'] is True
            assert status['critical'] is False

    def test_storage_critical_alert(self, tmp_path):
        """Critical alert when storage nearly full."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            critical_threshold=0.95
        )

        # Simulate 97% usage
        with patch.object(manager, 'get_storage_usage') as mock_usage:
            mock_usage.return_value = {
                'total_bytes': 1000000,
                'used_bytes': 970000,
                'free_bytes': 30000,
                'percent_used': 0.97
            }

            status = manager.check_storage_status()
            assert status['critical'] is True

    def test_storage_check_interval(self, tmp_path):
        """Storage checked at appropriate interval."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            check_interval_seconds=300  # 5 minutes
        )

        assert manager.check_interval_seconds == 300

    def test_storage_by_category(self, tmp_path):
        """Storage usage tracked by category."""
        # Create category directories
        (tmp_path / "videos").mkdir()
        (tmp_path / "sensor_data").mkdir()
        (tmp_path / "logs").mkdir()

        # Create test files
        (tmp_path / "videos" / "test.mp4").write_bytes(b'x' * 1000)
        (tmp_path / "sensor_data" / "data.csv").write_bytes(b'x' * 500)
        (tmp_path / "logs" / "app.log").write_bytes(b'x' * 200)

        manager = LocalStorageManager(storage_path=tmp_path)
        usage_by_category = manager.get_usage_by_category()

        assert StorageCategory.VIDEOS in usage_by_category
        assert StorageCategory.SENSOR_DATA in usage_by_category
        assert StorageCategory.LOGS in usage_by_category
        assert usage_by_category[StorageCategory.VIDEOS] >= 1000


class TestStorageAllocation:
    """Test storage allocation by priority."""

    def test_reserved_space_for_system(self, tmp_path):
        """Reserve space for system operations."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            reserved_system_bytes=104857600  # 100MB
        )

        assert manager.reserved_system_bytes == 104857600

    def test_video_storage_limit(self, tmp_path):
        """Videos have maximum storage allocation."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            allocations={StorageCategory.VIDEOS: 0.60}  # 60%
        )

        assert manager.get_allocation(StorageCategory.VIDEOS) == 0.60

    def test_sensor_data_storage_limit(self, tmp_path):
        """Sensor data has maximum storage allocation."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            allocations={StorageCategory.SENSOR_DATA: 0.20}
        )

        assert manager.get_allocation(StorageCategory.SENSOR_DATA) == 0.20

    def test_log_storage_limit(self, tmp_path):
        """Logs have maximum storage allocation."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            allocations={StorageCategory.LOGS: 0.10}
        )

        assert manager.get_allocation(StorageCategory.LOGS) == 0.10

    def test_allocation_configurable(self, tmp_path):
        """Storage allocations are configurable."""
        custom_allocations = {
            StorageCategory.VIDEOS: 0.50,
            StorageCategory.SENSOR_DATA: 0.30,
            StorageCategory.LOGS: 0.15,
            StorageCategory.SYSTEM: 0.05
        }

        manager = LocalStorageManager(
            storage_path=tmp_path,
            allocations=custom_allocations
        )

        assert manager.get_allocation(StorageCategory.VIDEOS) == 0.50
        assert manager.get_allocation(StorageCategory.SENSOR_DATA) == 0.30


class TestAutomaticCleanup:
    """Test automatic cleanup when storage is low."""

    def test_cleanup_triggered_at_threshold(self, tmp_path):
        """Automatic cleanup triggered at threshold."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            cleanup_threshold=0.85
        )

        assert manager.cleanup_threshold == 0.85
        assert manager.should_cleanup(current_usage=0.90) is True
        assert manager.should_cleanup(current_usage=0.80) is False

    def test_oldest_videos_deleted_first(self, tmp_path):
        """Oldest non-retained videos deleted first."""
        videos_dir = tmp_path / "videos"
        videos_dir.mkdir()

        # Create videos with different ages
        old_video = videos_dir / "old_video.mp4"
        new_video = videos_dir / "new_video.mp4"

        old_video.write_bytes(b'x' * 1000)
        new_video.write_bytes(b'x' * 1000)

        # Set modification times
        old_time = (datetime.now() - timedelta(days=7)).timestamp()
        os.utime(old_video, (old_time, old_time))

        manager = LocalStorageManager(storage_path=tmp_path)
        deleted = manager.cleanup_old_files(
            category=StorageCategory.VIDEOS,
            max_age_days=5,
            protected_files=[]
        )

        assert str(old_video) in deleted
        assert str(new_video) not in deleted
        assert not old_video.exists()
        assert new_video.exists()

    def test_retained_videos_protected(self, tmp_path):
        """Retained videos never auto-deleted."""
        videos_dir = tmp_path / "videos"
        videos_dir.mkdir()

        retained_video = videos_dir / "important.mp4"
        retained_video.write_bytes(b'x' * 1000)

        # Set old modification time
        old_time = (datetime.now() - timedelta(days=30)).timestamp()
        os.utime(retained_video, (old_time, old_time))

        manager = LocalStorageManager(storage_path=tmp_path)
        deleted = manager.cleanup_old_files(
            category=StorageCategory.VIDEOS,
            max_age_days=7,
            protected_files=[str(retained_video)]
        )

        assert str(retained_video) not in deleted
        assert retained_video.exists()

    def test_synced_data_deleted_before_pending(self, tmp_path):
        """Already-synced data deleted before pending."""
        manager = LocalStorageManager(storage_path=tmp_path)

        synced_files = ["/data/synced1.csv", "/data/synced2.csv"]
        pending_files = ["/data/pending1.csv"]

        # Register pending files
        for f in pending_files:
            manager.mark_pending_sync(f)

        deletion_order = manager.get_deletion_priority(synced_files + pending_files)

        # Synced files should come before pending
        for sf in synced_files:
            for pf in pending_files:
                assert deletion_order.index(sf) < deletion_order.index(pf)

    def test_cleanup_amount_configurable(self, tmp_path):
        """Cleanup removes configurable amount."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            cleanup_target=0.70  # Clean until 70% full
        )

        assert manager.cleanup_target == 0.70

    def test_cleanup_logged(self, tmp_path):
        """Cleanup actions logged."""
        manager = LocalStorageManager(storage_path=tmp_path)

        videos_dir = tmp_path / "videos"
        videos_dir.mkdir()
        test_file = videos_dir / "test.mp4"
        test_file.write_bytes(b'x' * 100)

        # Set old time
        old_time = (datetime.now() - timedelta(days=30)).timestamp()
        os.utime(test_file, (old_time, old_time))

        manager.cleanup_old_files(
            category=StorageCategory.VIDEOS,
            max_age_days=7,
            protected_files=[]
        )

        cleanup_log = manager.get_cleanup_log()
        assert len(cleanup_log) > 0
        assert 'timestamp' in cleanup_log[0]
        assert 'file' in cleanup_log[0]


class TestDataRetention:
    """Test data retention policies."""

    def test_sensor_data_retention_period(self, tmp_path):
        """Sensor data retained for configured period."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            retention_days={StorageCategory.SENSOR_DATA: 7}
        )

        assert manager.get_retention_days(StorageCategory.SENSOR_DATA) == 7

    def test_video_retention_period(self, tmp_path):
        """Videos retained for configured period."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            retention_days={StorageCategory.VIDEOS: 3}
        )

        assert manager.get_retention_days(StorageCategory.VIDEOS) == 3

    def test_alert_history_retained(self, tmp_path):
        """Alert history retained longer than routine data."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            retention_days={
                StorageCategory.SENSOR_DATA: 7,
                StorageCategory.ALERTS: 30
            }
        )

        sensor_retention = manager.get_retention_days(StorageCategory.SENSOR_DATA)
        alert_retention = manager.get_retention_days(StorageCategory.ALERTS)

        assert alert_retention > sensor_retention

    def test_headcount_history_retained(self, tmp_path):
        """Headcount history retained."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            retention_days={StorageCategory.HEADCOUNT: 14}
        )

        assert manager.get_retention_days(StorageCategory.HEADCOUNT) == 14

    def test_retention_extended_when_offline(self, tmp_path):
        """Retention extended during network outage."""
        manager = LocalStorageManager(storage_path=tmp_path)

        normal_retention = manager.get_retention_days(StorageCategory.SENSOR_DATA)

        manager.set_offline_mode(True)
        offline_retention = manager.get_retention_days(StorageCategory.SENSOR_DATA)

        assert offline_retention > normal_retention


class TestPendingDataProtection:
    """Test protection of data pending sync."""

    def test_pending_uploads_tracked(self, tmp_path):
        """Data pending upload is tracked."""
        manager = LocalStorageManager(storage_path=tmp_path)

        manager.mark_pending_sync("/data/file1.csv")
        manager.mark_pending_sync("/data/file2.csv")

        pending = manager.get_pending_files()
        assert "/data/file1.csv" in pending
        assert "/data/file2.csv" in pending

    def test_pending_data_not_deleted(self, tmp_path):
        """Pending data never auto-deleted."""
        manager = LocalStorageManager(storage_path=tmp_path)

        pending_file = "/data/pending.csv"
        manager.mark_pending_sync(pending_file)

        assert manager.is_protected(pending_file) is True

    def test_pending_queue_size_limited(self, tmp_path):
        """Pending queue has size limit."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            max_pending_files=100
        )

        assert manager.max_pending_files == 100

    def test_pending_age_limit(self, tmp_path):
        """Very old pending data eventually pruned."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            max_pending_age_days=30
        )

        assert manager.max_pending_age_days == 30

    def test_pending_priority_preserved(self, tmp_path):
        """High-priority pending data kept longer."""
        manager = LocalStorageManager(storage_path=tmp_path)

        manager.mark_pending_sync("/data/normal.csv", priority="normal")
        manager.mark_pending_sync("/data/high.csv", priority="high")

        pending = manager.get_pending_files()
        high_priority = [f for f in pending if manager.get_pending_priority(f) == "high"]

        assert "/data/high.csv" in high_priority


class TestStorageHealth:
    """Test SD card health monitoring."""

    def test_disk_errors_detected(self, tmp_path):
        """Disk I/O errors detected and logged."""
        manager = LocalStorageManager(storage_path=tmp_path)

        manager.record_io_error("Read error on /dev/mmcblk0")
        errors = manager.get_io_errors()

        assert len(errors) > 0
        assert "Read error" in errors[0]['message']

    def test_read_only_filesystem_detected(self, tmp_path):
        """Read-only filesystem detected."""
        manager = LocalStorageManager(storage_path=tmp_path)

        # By default, tmp_path is writable
        assert manager.is_filesystem_readonly() is False

    def test_storage_health_in_diagnostics(self, tmp_path):
        """Storage health included in diagnostics."""
        manager = LocalStorageManager(storage_path=tmp_path)

        diagnostics = manager.get_diagnostics()

        assert 'storage_health' in diagnostics
        assert 'io_errors' in diagnostics
        assert 'filesystem_status' in diagnostics

    def test_smart_data_if_available(self, tmp_path):
        """SMART data logged if available."""
        manager = LocalStorageManager(storage_path=tmp_path)

        # SMART data may or may not be available
        smart_data = manager.get_smart_data()

        assert smart_data is None or isinstance(smart_data, dict)


class TestTmpfsUsage:
    """Test tmpfs usage for frequently-changing data."""

    def test_motion_frames_in_tmpfs(self, tmp_path):
        """Motion detection frames use tmpfs."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            tmpfs_path="/tmp/chickencoop"
        )

        motion_path = manager.get_motion_frames_path()
        assert "/tmp" in str(motion_path) or "tmpfs" in str(motion_path).lower()

    def test_temp_videos_in_tmpfs(self, tmp_path):
        """Videos recorded to tmpfs then moved."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            tmpfs_path="/tmp/chickencoop"
        )

        temp_video_path = manager.get_temp_video_path()
        assert "/tmp" in str(temp_video_path)

    def test_tmpfs_size_appropriate(self, tmp_path):
        """Tmpfs sized appropriately for RAM."""
        manager = LocalStorageManager(
            storage_path=tmp_path,
            tmpfs_size_mb=256
        )

        assert manager.tmpfs_size_mb == 256

    def test_tmpfs_cleanup_on_boot(self, tmp_path):
        """Tmpfs cleared on boot (automatic)."""
        manager = LocalStorageManager(storage_path=tmp_path)

        # tmpfs is automatically cleared on boot
        # This test verifies the manager knows this
        assert manager.tmpfs_requires_manual_cleanup() is False


class TestExternalStorage:
    """Test external storage support (USB drive)."""

    def test_usb_drive_detected(self, tmp_path):
        """USB drive automatically detected."""
        manager = LocalStorageManager(storage_path=tmp_path)

        # Mock USB detection
        usb_devices = manager.detect_usb_drives()

        # Should return list (empty if no USB)
        assert isinstance(usb_devices, list)

    def test_overflow_to_usb(self, tmp_path):
        """Data overflows to USB when SD full."""
        usb_path = tmp_path / "usb_drive"
        usb_path.mkdir()

        manager = LocalStorageManager(
            storage_path=tmp_path,
            usb_overflow_path=usb_path
        )

        assert manager.usb_overflow_enabled is True
        assert manager.usb_overflow_path == usb_path

    def test_usb_removal_handled(self, tmp_path):
        """USB removal handled gracefully."""
        manager = LocalStorageManager(storage_path=tmp_path)

        # Simulate USB removal
        manager.handle_usb_removal("/media/usb0")

        # Should not raise, should log event
        events = manager.get_storage_events()
        assert any("usb" in str(e).lower() for e in events)

    def test_usb_health_monitored(self, tmp_path):
        """USB drive health monitored."""
        manager = LocalStorageManager(storage_path=tmp_path)

        health = manager.get_usb_health()

        # Returns None if no USB, dict if present
        assert health is None or isinstance(health, dict)
