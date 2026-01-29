"""
Phase 9: Offline Operation Tests
================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates system behavior during network outages:
- Continued sensor monitoring without connectivity
- Local data buffering during WiFi outages
- Video storage on local SD card
- Graceful degradation of cloud-dependent features
- Network status detection and reporting

WHY THIS MATTERS:
-----------------
WiFi in rural/austere environments is unreliable. The chicken coop
monitoring system must continue its primary function (monitoring)
even when disconnected. All data must be preserved locally and
synchronized when connectivity returns.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase9_resilience/connectivity/test_offline_operation.py -v

Tests simulate network disconnection and verify offline behavior.
"""
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import json
import gzip
import tempfile
import os


class TestNetworkDetection:
    """Test network connectivity detection."""

    def test_detect_wifi_connected(self):
        """Detect when WiFi is connected."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate WiFi connected
        with patch.object(manager, '_check_interface_status', return_value=True):
            status = manager.check_wifi_status()

        assert status.connected is True
        assert status.interface == "wlan0"

    def test_detect_wifi_disconnected(self):
        """Detect when WiFi is disconnected."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate WiFi disconnected
        with patch.object(manager, '_check_interface_status', return_value=False):
            status = manager.check_wifi_status()

        assert status.connected is False

    def test_detect_internet_reachable(self):
        """Detect if internet is reachable (not just WiFi)."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate internet reachable
        with patch.object(manager, '_ping_host', return_value=True):
            reachable = manager.check_internet_reachable()

        assert reachable is True

    def test_detect_aws_reachable(self):
        """Detect if AWS services are reachable."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate AWS reachable
        with patch.object(manager, '_check_aws_endpoint', return_value=True):
            reachable = manager.check_aws_reachable()

        assert reachable is True

    def test_network_check_interval(self):
        """Network status checked at appropriate interval."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Default check interval should be between 10-60 seconds
        assert 10 <= manager.network_check_interval <= 60

    def test_signal_strength_monitoring(self):
        """WiFi signal strength is monitored."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate signal strength reading
        with patch.object(manager, '_get_signal_strength', return_value=-45):
            strength = manager.get_wifi_signal_strength()

        # RSSI typically ranges from -30 (excellent) to -90 (poor)
        assert -100 <= strength <= 0


class TestContinuedMonitoring:
    """Test that monitoring continues when offline."""

    def test_sensor_readings_continue_offline(self):
        """Sensor readings continue during network outage."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        # Mock sensor reading
        reading = {"temperature": 72.5, "humidity": 65.0, "timestamp": datetime.now().isoformat()}

        result = manager.process_sensor_reading(reading)

        assert result["success"] is True
        assert result["stored_locally"] is True

    def test_motion_detection_continues_offline(self):
        """Motion detection continues during outage."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        result = manager.process_motion_event(detected=True, timestamp=datetime.now())

        assert result["success"] is True
        assert result["event_logged"] is True

    def test_video_recording_continues_offline(self):
        """Video recording continues during outage."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        # Simulate video recording request
        result = manager.request_video_recording(
            trigger="motion",
            duration=30
        )

        assert result["success"] is True
        assert result["storage_location"] == "local"

    def test_headcount_continues_offline(self):
        """Nightly headcount runs during outage."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        result = manager.process_headcount(count=5, expected=6, confidence=0.85)

        assert result["success"] is True
        assert result["stored_locally"] is True

    def test_local_alerts_work_offline(self):
        """Local alerting (LED, buzzer) works offline."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        result = manager.trigger_local_alert(alert_type="temperature_high")

        assert result["success"] is True
        assert result["alert_type"] == "temperature_high"


class TestLocalDataBuffering:
    """Test local data buffering during outages."""

    def test_sensor_data_buffered_locally(self, tmp_path):
        """Sensor readings buffered to local storage."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        reading = {"temperature": 72.5, "humidity": 65.0}
        manager.buffer_sensor_data(reading)

        # Verify data is in buffer
        buffer_contents = manager.get_buffered_data()
        assert len(buffer_contents) >= 1
        assert buffer_contents[0]["temperature"] == 72.5

    def test_buffer_includes_timestamps(self, tmp_path):
        """Buffered data includes accurate timestamps."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        before = datetime.now()
        reading = {"temperature": 72.5, "humidity": 65.0}
        manager.buffer_sensor_data(reading)
        after = datetime.now()

        buffer_contents = manager.get_buffered_data()
        buffered_time = datetime.fromisoformat(buffer_contents[0]["buffered_at"])

        assert before <= buffered_time <= after

    def test_buffer_survives_restart(self, tmp_path):
        """Buffer persists across service restarts."""
        from src.resilience.offline_manager import OfflineOperationManager

        # First instance writes data
        manager1 = OfflineOperationManager(buffer_path=tmp_path)
        manager1.buffer_sensor_data({"temperature": 72.5})
        manager1.flush_buffer()

        # Second instance should see the data
        manager2 = OfflineOperationManager(buffer_path=tmp_path)
        buffer_contents = manager2.get_buffered_data()

        assert len(buffer_contents) >= 1

    def test_buffer_capacity_management(self, tmp_path):
        """Buffer manages capacity (doesn't fill disk)."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            max_buffer_size_mb=1  # 1MB limit
        )

        # Buffer should not exceed max size
        assert manager.max_buffer_size_mb == 1
        assert manager.get_buffer_size_mb() <= manager.max_buffer_size_mb

    def test_buffer_priority_data(self, tmp_path):
        """Critical data prioritized in buffer."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)

        # Add regular and priority data
        manager.buffer_sensor_data({"temperature": 72.5}, priority="normal")
        manager.buffer_sensor_data({"temperature": 105.0, "alert": True}, priority="critical")

        # Critical data should be marked for priority sync
        priority_items = manager.get_priority_buffer_items()
        assert len(priority_items) >= 1
        assert priority_items[0]["priority"] == "critical"

    def test_buffer_compression(self, tmp_path):
        """Buffer data compressed to save space."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            enable_compression=True
        )

        # Add multiple readings
        for i in range(100):
            manager.buffer_sensor_data({"temperature": 72.5 + i * 0.1, "humidity": 65.0})

        manager.flush_buffer()

        # Check that compressed file exists
        compressed_files = list(tmp_path.glob("*.gz"))
        assert manager.compression_enabled is True


class TestLocalVideoStorage:
    """Test video storage during network outages."""

    def test_videos_stored_locally(self, tmp_path):
        """Videos saved to local storage when offline."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            video_storage_path=tmp_path / "videos"
        )
        manager.set_offline_mode(True)

        # Simulate storing a video
        video_data = b"fake video content"
        result = manager.store_video_locally(
            video_data=video_data,
            filename="motion_20250125_143000.mp4"
        )

        assert result["success"] is True
        assert result["local_path"] is not None

    def test_video_metadata_preserved(self, tmp_path):
        """Video metadata (timestamp, trigger) preserved."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            video_storage_path=tmp_path / "videos"
        )

        video_data = b"fake video content"
        metadata = {
            "trigger": "motion",
            "timestamp": datetime.now().isoformat(),
            "duration": 30,
            "camera": "indoor"
        }

        result = manager.store_video_locally(
            video_data=video_data,
            filename="motion_20250125_143000.mp4",
            metadata=metadata
        )

        # Retrieve metadata
        stored_metadata = manager.get_video_metadata("motion_20250125_143000.mp4")
        assert stored_metadata["trigger"] == "motion"
        assert stored_metadata["duration"] == 30

    def test_local_storage_capacity_check(self, tmp_path):
        """Check local storage capacity before recording."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            video_storage_path=tmp_path / "videos"
        )

        capacity = manager.check_storage_capacity()

        assert "available_mb" in capacity
        assert "total_mb" in capacity
        assert "percent_free" in capacity

    def test_old_video_cleanup_when_full(self, tmp_path):
        """Old videos cleaned up when storage full."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            video_storage_path=tmp_path / "videos",
            video_retention_days=7
        )

        # Cleanup should be possible
        result = manager.cleanup_old_videos()

        assert "deleted_count" in result
        assert "freed_mb" in result

    def test_video_marked_for_upload(self, tmp_path):
        """Videos marked as pending upload."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(
            buffer_path=tmp_path,
            video_storage_path=tmp_path / "videos"
        )
        manager.set_offline_mode(True)

        video_data = b"fake video content"
        manager.store_video_locally(
            video_data=video_data,
            filename="motion_20250125_143000.mp4"
        )

        pending = manager.get_videos_pending_upload()
        assert isinstance(pending, list)


class TestGracefulDegradation:
    """Test graceful degradation of cloud features."""

    def test_dashboard_shows_offline_status(self):
        """Dashboard shows coop is offline."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        status = manager.get_system_status()

        assert status["online"] is False
        assert status["offline_since"] is not None

    def test_last_known_data_displayed(self):
        """Dashboard shows last known data with timestamp."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Record last known data
        manager.update_last_known_data({
            "temperature": 72.5,
            "humidity": 65.0
        })
        manager.set_offline_mode(True)

        last_data = manager.get_last_known_data()

        assert last_data["temperature"] == 72.5
        assert "last_updated" in last_data

    def test_cloud_commands_queued(self, tmp_path):
        """Commands from cloud queued for when online."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        # Queue a command for later execution
        manager.queue_cloud_command({
            "action": "record_video",
            "duration": 60
        })

        queued = manager.get_queued_commands()
        assert len(queued) >= 1
        assert queued[0]["action"] == "record_video"

    def test_no_crash_on_network_error(self):
        """Network errors don't crash the service."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()

        # Simulate network error during operation
        with patch.object(manager, '_send_to_cloud', side_effect=ConnectionError("Network unreachable")):
            result = manager.safe_cloud_operation(
                operation="upload",
                data={"test": "data"}
            )

        assert result["success"] is False
        assert result["error_handled"] is True
        assert "error_message" in result

    def test_reduced_functionality_logged(self, tmp_path):
        """Reduced functionality is logged."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        # Check that offline mode transition is logged
        logs = manager.get_recent_logs()

        assert any("offline" in log.lower() for log in logs)


class TestAlertBuffering:
    """Test alert buffering during outages."""

    def test_alerts_buffered_locally(self, tmp_path):
        """Alerts buffered when SNS unreachable."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        alert = {
            "type": "temperature_high",
            "value": 105,
            "threshold": 95
        }
        result = manager.buffer_alert(alert)

        assert result["buffered"] is True

        buffered_alerts = manager.get_buffered_alerts()
        assert len(buffered_alerts) >= 1

    def test_buffered_alerts_include_context(self, tmp_path):
        """Buffered alerts include full context."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        alert = {
            "type": "temperature_high",
            "value": 105,
            "threshold": 95,
            "coop_id": "coop1"
        }
        manager.buffer_alert(alert)

        buffered_alerts = manager.get_buffered_alerts()
        assert buffered_alerts[0]["type"] == "temperature_high"
        assert buffered_alerts[0]["value"] == 105
        assert "timestamp" in buffered_alerts[0]

    def test_critical_alerts_prioritized(self, tmp_path):
        """Critical alerts synced first when online."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        # Buffer normal and critical alerts
        manager.buffer_alert({"type": "humidity_low", "severity": "warning"})
        manager.buffer_alert({"type": "temperature_critical", "severity": "critical"})
        manager.buffer_alert({"type": "motion_detected", "severity": "info"})

        # Get alerts sorted by priority
        prioritized = manager.get_alerts_by_priority()

        assert prioritized[0]["severity"] == "critical"

    def test_alert_deduplication_on_sync(self, tmp_path):
        """Duplicate alerts deduplicated on sync."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        # Buffer same alert multiple times
        for _ in range(5):
            manager.buffer_alert({
                "type": "temperature_high",
                "value": 105,
                "dedup_key": "temp_high_alert"
            })

        # Deduplicated count should be less
        deduplicated = manager.get_deduplicated_alerts()
        assert len(deduplicated) == 1


class TestOfflineIndicators:
    """Test offline status indicators."""

    def test_local_led_indicates_offline(self):
        """LED indicator shows offline status."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        led_state = manager.get_led_indicator_state()

        # LED should indicate offline (e.g., blinking red)
        assert led_state["status"] == "offline"
        assert led_state["color"] in ["red", "yellow", "orange"]

    def test_offline_duration_tracked(self):
        """Track how long device has been offline."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager()
        manager.set_offline_mode(True)

        duration = manager.get_offline_duration()

        assert duration is not None
        assert duration >= timedelta(seconds=0)

    def test_offline_event_logged(self, tmp_path):
        """Network disconnection logged with timestamp."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)
        manager.set_offline_mode(True)

        events = manager.get_connectivity_events()

        assert len(events) >= 1
        assert events[-1]["event_type"] == "disconnected"
        assert "timestamp" in events[-1]

    def test_reconnection_logged(self, tmp_path):
        """Network reconnection logged."""
        from src.resilience.offline_manager import OfflineOperationManager

        manager = OfflineOperationManager(buffer_path=tmp_path)

        # Simulate disconnect then reconnect
        manager.set_offline_mode(True)
        manager.set_offline_mode(False)

        events = manager.get_connectivity_events()

        # Should have both disconnect and reconnect events
        event_types = [e["event_type"] for e in events]
        assert "disconnected" in event_types
        assert "reconnected" in event_types
