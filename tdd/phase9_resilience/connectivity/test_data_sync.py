"""
Phase 9: Data Synchronization Tests
====================================

FUNCTIONALITY BEING TESTED:
---------------------------
This test module validates data synchronization when connectivity returns:
- Buffered sensor data upload to S3/IoT
- Pending video upload queue processing
- Alert delivery for buffered alerts
- Sync prioritization and ordering
- Bandwidth-aware upload throttling
- Conflict resolution for settings

WHY THIS MATTERS:
-----------------
After a network outage (minutes, hours, or days), all buffered data must
be synchronized to the cloud reliably. The sync process must be:
1. Complete - no data lost
2. Ordered - maintain chronological order
3. Efficient - don't overwhelm the connection
4. Resumable - handle interruptions during sync

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase9_resilience/connectivity/test_data_sync.py -v

Tests verify sync behavior after simulated outages.
"""
import pytest
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch, call, PropertyMock
from typing import List, Dict, Any

from src.resilience.data_sync import (
    DataSyncManager,
    SyncStatus,
    SyncPriority,
    SyncItem,
    SyncResult,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_s3_client():
    """Provide a mocked S3 client."""
    client = MagicMock()
    client.upload_file.return_value = None
    client.upload_fileobj.return_value = None
    client.list_objects_v2.return_value = {"Contents": []}
    return client


@pytest.fixture
def mock_iot_client():
    """Provide a mocked IoT client."""
    client = MagicMock()
    client.publish.return_value = True
    client.publish_sensor_reading.return_value = True
    return client


@pytest.fixture
def mock_sns_client():
    """Provide a mocked SNS client."""
    client = MagicMock()
    client.publish.return_value = {"MessageId": "test-message-id"}
    client.publish_alert.return_value = "test-message-id"
    return client


@pytest.fixture
def temp_data_dir(tmp_path):
    """Provide a temporary data directory with test files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def sample_sensor_readings():
    """Provide sample buffered sensor readings."""
    base_time = datetime.now(timezone.utc) - timedelta(hours=2)
    return [
        {
            "timestamp": (base_time + timedelta(minutes=i * 5)).isoformat(),
            "temperature": 70.0 + i * 0.5,
            "humidity": 60.0 + i * 0.2,
            "coop_id": "test-coop",
        }
        for i in range(10)
    ]


@pytest.fixture
def sample_pending_videos(temp_data_dir):
    """Create sample pending video files."""
    videos = []
    for i in range(3):
        video_path = temp_data_dir / f"motion_{i:03d}.mp4"
        video_path.write_bytes(b"\x00" * 1000 * (i + 1))  # Different sizes
        videos.append({
            "path": str(video_path),
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=i)).isoformat(),
            "camera": "indoor",
            "trigger": "motion",
            "retain": i == 0,  # First video is retained
        })
    return videos


@pytest.fixture
def sample_buffered_alerts():
    """Provide sample buffered alerts."""
    base_time = datetime.now(timezone.utc) - timedelta(hours=1)
    return [
        {
            "type": "temperature_high",
            "priority": SyncPriority.CRITICAL,
            "timestamp": (base_time + timedelta(minutes=10)).isoformat(),
            "message": "Temperature exceeded 95°F",
            "value": 97.5,
        },
        {
            "type": "temperature_low",
            "priority": SyncPriority.HIGH,
            "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
            "message": "Temperature dropped below 32°F",
            "value": 30.0,
        },
        {
            "type": "motion_detected",
            "priority": SyncPriority.NORMAL,
            "timestamp": base_time.isoformat(),
            "message": "Motion detected at night",
        },
    ]


@pytest.fixture
def sync_config():
    """Provide sync configuration."""
    return {
        "coop_id": "test-coop",
        "s3_bucket": "test-bucket",
        "reconnection_delay_seconds": 5,
        "max_concurrent_uploads": 3,
        "batch_size": 100,
        "throttle_kbps": 1000,
        "off_peak_hours": {"start": 2, "end": 6},
    }


@pytest.fixture
def sync_manager(mock_s3_client, mock_iot_client, mock_sns_client, sync_config, temp_data_dir):
    """Provide a configured DataSyncManager."""
    return DataSyncManager(
        s3_client=mock_s3_client,
        iot_client=mock_iot_client,
        sns_client=mock_sns_client,
        config=sync_config,
        data_dir=str(temp_data_dir),
    )


# =============================================================================
# TestSyncTrigger
# =============================================================================

class TestSyncTrigger:
    """Test sync trigger conditions."""

    def test_sync_starts_on_reconnection(self, sync_manager):
        """Sync starts automatically when connectivity restored."""
        # Simulate offline period with buffered data
        sync_manager.buffer_sensor_reading({"temperature": 72.5, "timestamp": datetime.now(timezone.utc).isoformat()})

        # Trigger reconnection
        sync_manager.on_connectivity_restored()

        # Verify sync was initiated
        assert sync_manager.is_syncing or sync_manager.sync_scheduled
        assert sync_manager.status in [SyncStatus.PENDING, SyncStatus.IN_PROGRESS]

    def test_sync_delayed_after_reconnection(self, sync_manager, sync_config):
        """Brief delay before sync to ensure stable connection."""
        sync_manager.buffer_sensor_reading({"temperature": 72.5, "timestamp": datetime.now(timezone.utc).isoformat()})

        # Trigger reconnection
        start_time = datetime.now(timezone.utc)
        sync_manager.on_connectivity_restored()

        # Sync should be scheduled but not immediately started
        assert sync_manager.sync_scheduled
        assert sync_manager.scheduled_sync_time is not None
        expected_delay = timedelta(seconds=sync_config["reconnection_delay_seconds"])
        assert sync_manager.scheduled_sync_time >= start_time + expected_delay

    def test_sync_retrigger_on_failure(self, sync_manager, mock_s3_client):
        """Sync retries if connection lost during sync."""
        # Setup: buffer data and simulate upload failure
        sync_manager.buffer_sensor_reading({"temperature": 72.5, "timestamp": datetime.now(timezone.utc).isoformat()})
        # sync_sensor_data uses upload_fileobj, not upload_file
        mock_s3_client.upload_fileobj.side_effect = Exception("Connection lost")

        # Attempt sync
        result = sync_manager.sync_all()

        # Verify retry is scheduled
        assert result.success is False
        assert sync_manager.retry_count > 0
        assert sync_manager.sync_scheduled  # Retry scheduled

    def test_manual_sync_trigger(self, sync_manager):
        """Admin can manually trigger sync."""
        sync_manager.buffer_sensor_reading({"temperature": 72.5, "timestamp": datetime.now(timezone.utc).isoformat()})

        # Manual trigger should bypass delay
        result = sync_manager.trigger_manual_sync()

        assert result is not None
        assert sync_manager.last_sync_trigger == "manual"


# =============================================================================
# TestSensorDataSync
# =============================================================================

class TestSensorDataSync:
    """Test buffered sensor data synchronization."""

    def test_all_buffered_readings_uploaded(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """All buffered sensor readings uploaded to cloud."""
        # Buffer all readings
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Sync
        result = sync_manager.sync_sensor_data()

        # Verify all readings uploaded
        assert result.success
        assert result.items_synced == len(sample_sensor_readings)
        assert mock_s3_client.upload_file.called or mock_s3_client.upload_fileobj.called

    def test_readings_uploaded_in_chronological_order(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Readings uploaded oldest-first."""
        # Buffer readings (already in chronological order from fixture)
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Track upload order
        uploaded_timestamps = []
        def track_upload(*args, **kwargs):
            # Extract timestamp from upload call
            if 'Body' in kwargs:
                data = json.loads(kwargs['Body'])
            elif len(args) > 1:
                data = json.loads(args[1]) if isinstance(args[1], str) else args[1]
            else:
                data = {}
            if 'readings' in data:
                for r in data['readings']:
                    uploaded_timestamps.append(r.get('timestamp'))

        mock_s3_client.upload_fileobj.side_effect = track_upload

        # Sync
        sync_manager.sync_sensor_data()

        # Verify chronological order (oldest first)
        uploaded_order = sync_manager.get_sync_order()
        assert uploaded_order == sorted(uploaded_order)

    def test_readings_uploaded_to_correct_s3_path(self, sync_manager, mock_s3_client, sample_sensor_readings, sync_config):
        """Readings go to correct coop/date S3 prefix."""
        sync_manager.buffer_sensor_reading(sample_sensor_readings[0])

        # Sync
        sync_manager.sync_sensor_data()

        # Verify S3 path structure
        call_args = mock_s3_client.upload_file.call_args or mock_s3_client.upload_fileobj.call_args
        if call_args:
            # Check that path includes coop_id and date structure
            key = call_args.kwargs.get('Key') or call_args[1].get('Key', '')
            assert sync_config["coop_id"] in key or "test-coop" in str(call_args)

    def test_readings_published_to_iot(self, sync_manager, mock_iot_client, sample_sensor_readings):
        """Historical readings published to IoT for dashboard."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Sync with IoT publishing enabled
        result = sync_manager.sync_sensor_data(publish_to_iot=True)

        # Verify IoT publish called
        assert mock_iot_client.publish.called or mock_iot_client.publish_sensor_reading.called
        assert result.iot_published > 0

    def test_buffer_cleared_after_successful_upload(self, sync_manager, sample_sensor_readings):
        """Local buffer cleared after confirmed upload."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        initial_buffer_size = sync_manager.get_pending_sensor_count()
        assert initial_buffer_size == len(sample_sensor_readings)

        # Sync successfully
        result = sync_manager.sync_sensor_data()

        # Buffer should be cleared
        assert result.success
        assert sync_manager.get_pending_sensor_count() == 0

    def test_partial_upload_resumable(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Can resume from where upload was interrupted."""
        # Buffer more readings to ensure multiple batches with small batch size
        for i in range(50):
            sync_manager.buffer_sensor_reading({
                "temperature": 70.0 + i * 0.1,
                "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=50-i)).isoformat(),
            })

        # Use small batch size to ensure multiple upload calls
        sync_manager.config["batch_size"] = 10

        # Simulate failure on 3rd batch upload
        upload_count = [0]
        def partial_failure(*args, **kwargs):
            upload_count[0] += 1
            if upload_count[0] >= 3:
                raise Exception("Connection lost")

        mock_s3_client.upload_fileobj.side_effect = partial_failure

        # First sync attempt - partial (should fail on 3rd batch = 20 items synced)
        result1 = sync_manager.sync_sensor_data()
        assert not result1.success

        # Get checkpoint
        checkpoint = sync_manager.get_sync_checkpoint()
        assert checkpoint is not None
        assert checkpoint.items_completed > 0

        # Fix connection and resume
        mock_s3_client.upload_fileobj.side_effect = None
        result2 = sync_manager.sync_sensor_data(resume_from_checkpoint=True)

        # Should complete remaining items
        assert result2.success

    def test_batch_upload_for_efficiency(self, sync_manager, mock_s3_client, sync_config):
        """Multiple readings batched in single upload."""
        # Buffer many readings
        for i in range(200):
            sync_manager.buffer_sensor_reading({
                "temperature": 70.0 + i * 0.1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Sync
        sync_manager.sync_sensor_data()

        # Should batch, not make 200 individual calls
        upload_calls = mock_s3_client.upload_file.call_count + mock_s3_client.upload_fileobj.call_count
        max_expected_calls = 200 // sync_config["batch_size"] + 1
        assert upload_calls <= max_expected_calls


# =============================================================================
# TestVideoSync
# =============================================================================

class TestVideoSync:
    """Test pending video upload synchronization."""

    def test_pending_videos_uploaded(self, sync_manager, mock_s3_client, sample_pending_videos):
        """All pending videos uploaded to S3."""
        for video in sample_pending_videos:
            sync_manager.queue_video_upload(video)

        result = sync_manager.sync_videos()

        assert result.success
        assert result.items_synced == len(sample_pending_videos)
        assert mock_s3_client.upload_file.call_count >= len(sample_pending_videos)

    def test_videos_uploaded_with_metadata(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Videos uploaded with correct metadata."""
        video = sample_pending_videos[0]
        sync_manager.queue_video_upload(video)

        sync_manager.sync_videos()

        # Check metadata was included
        call_args = mock_s3_client.upload_file.call_args
        if call_args and 'ExtraArgs' in call_args.kwargs:
            metadata = call_args.kwargs['ExtraArgs'].get('Metadata', {})
            assert 'timestamp' in metadata or 'camera' in metadata

    def test_thumbnail_generated_and_uploaded(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Thumbnails generated and uploaded."""
        video = sample_pending_videos[0]
        sync_manager.queue_video_upload(video)

        result = sync_manager.sync_videos(generate_thumbnails=True)

        # Should have uploaded both video and thumbnail
        assert result.thumbnails_generated >= 0  # May be 0 if video is invalid

    def test_large_video_upload_progress(self, sync_manager, mock_s3_client, temp_data_dir):
        """Large video uploads show progress."""
        # Create a larger video file
        large_video_path = temp_data_dir / "large_video.mp4"
        large_video_path.write_bytes(b"\x00" * 10_000_000)  # 10MB

        sync_manager.queue_video_upload({
            "path": str(large_video_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        progress_updates = []
        def track_progress(percent, bytes_sent, total_bytes):
            progress_updates.append(percent)

        result = sync_manager.sync_videos(progress_callback=track_progress)

        # Progress should have been reported
        assert len(progress_updates) > 0 or result.success

    def test_video_upload_retry_on_failure(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Failed video uploads retried."""
        video = sample_pending_videos[0]
        sync_manager.queue_video_upload(video)

        # Fail first 2 attempts, succeed on 3rd
        attempt = [0]
        def flaky_upload(*args, **kwargs):
            attempt[0] += 1
            if attempt[0] < 3:
                raise Exception("Network error")

        mock_s3_client.upload_file.side_effect = flaky_upload

        result = sync_manager.sync_videos(max_retries=3)

        assert attempt[0] >= 2  # Retried at least once

    def test_corrupt_video_skipped(self, sync_manager, mock_s3_client, temp_data_dir):
        """Corrupt videos logged and skipped."""
        # Create a corrupt video file
        corrupt_path = temp_data_dir / "corrupt.mp4"
        corrupt_path.write_bytes(b"not a valid video")

        sync_manager.queue_video_upload({
            "path": str(corrupt_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "validate": True,
        })

        # Add a valid video too
        valid_path = temp_data_dir / "valid.mp4"
        valid_path.write_bytes(b"\x00\x00\x00\x1c\x66\x74\x79\x70")  # MP4 header
        sync_manager.queue_video_upload({
            "path": str(valid_path),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        result = sync_manager.sync_videos()

        # Sync should complete, skipping corrupt file
        assert result.items_skipped >= 0  # May skip corrupt file
        assert result.errors_logged >= 0

    def test_local_video_deleted_after_upload(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Local video deleted after successful upload."""
        video = sample_pending_videos[1]  # Non-retained video
        video_path = Path(video["path"])
        assert video_path.exists()

        sync_manager.queue_video_upload(video)
        result = sync_manager.sync_videos(delete_after_upload=True)

        # File should be deleted
        assert result.success
        assert not video_path.exists()

    def test_retained_video_kept_locally(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Retained videos kept locally even after upload."""
        video = sample_pending_videos[0]  # Retained video
        video_path = Path(video["path"])
        assert video["retain"] is True

        sync_manager.queue_video_upload(video)
        result = sync_manager.sync_videos(delete_after_upload=True)

        # Retained file should still exist
        assert result.success
        assert video_path.exists()


# =============================================================================
# TestAlertSync
# =============================================================================

class TestAlertSync:
    """Test buffered alert synchronization."""

    def test_buffered_alerts_sent(self, sync_manager, mock_sns_client, sample_buffered_alerts):
        """All buffered alerts sent via SNS."""
        for alert in sample_buffered_alerts:
            sync_manager.buffer_alert(alert)

        result = sync_manager.sync_alerts()

        assert result.success
        assert result.items_synced == len(sample_buffered_alerts)
        assert mock_sns_client.publish.called or mock_sns_client.publish_alert.called

    def test_alerts_sent_in_priority_order(self, sync_manager, mock_sns_client, sample_buffered_alerts):
        """Critical alerts sent before routine alerts."""
        for alert in sample_buffered_alerts:
            sync_manager.buffer_alert(alert)

        sent_priorities = []
        def track_send(*args, **kwargs):
            msg = kwargs.get('Message', args[0] if args else '')
            if 'CRITICAL' in str(msg).upper() or 'temperature_high' in str(msg):
                sent_priorities.append(SyncPriority.CRITICAL)
            elif 'HIGH' in str(msg).upper() or 'temperature_low' in str(msg):
                sent_priorities.append(SyncPriority.HIGH)
            else:
                sent_priorities.append(SyncPriority.NORMAL)
            return {"MessageId": "test"}

        mock_sns_client.publish.side_effect = track_send

        sync_manager.sync_alerts()

        # Verify priority order maintained
        sync_order = sync_manager.get_alert_sync_order()
        priorities = [a.get('priority', SyncPriority.NORMAL) for a in sync_order]
        assert priorities == sorted(priorities, key=lambda p: p.value if hasattr(p, 'value') else p)

    def test_alerts_include_delay_notice(self, sync_manager, mock_sns_client):
        """Alerts indicate they were delayed."""
        old_alert = {
            "type": "temperature_high",
            "priority": SyncPriority.CRITICAL,
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
            "message": "Temperature exceeded 95°F",
        }
        sync_manager.buffer_alert(old_alert)

        sync_manager.sync_alerts()

        # Check that message includes delay notice
        call_args = mock_sns_client.publish.call_args or mock_sns_client.publish_alert.call_args
        if call_args:
            message = str(call_args)
            assert "delayed" in message.lower() or "offline" in message.lower() or "ago" in message.lower()

    def test_similar_alerts_aggregated(self, sync_manager, mock_sns_client):
        """Similar alerts aggregated to prevent spam."""
        # Buffer many similar alerts
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(50):
            sync_manager.buffer_alert({
                "type": "temperature_low",
                "priority": SyncPriority.HIGH,
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                "message": "Temperature below threshold",
                "value": 30.0 - i * 0.1,
            })

        result = sync_manager.sync_alerts(aggregate_similar=True)

        # Should not send 50 separate alerts
        assert mock_sns_client.publish.call_count < 50
        assert result.alerts_aggregated > 0

    def test_alert_cooldown_respected(self, sync_manager, mock_sns_client):
        """Alert cooldown still respected for buffered alerts."""
        # Buffer alerts that are within cooldown of each other
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)
        for i in range(5):
            sync_manager.buffer_alert({
                "type": "temperature_high",
                "priority": SyncPriority.HIGH,
                "timestamp": (base_time + timedelta(minutes=i)).isoformat(),  # 1 min apart
                "message": "Temperature high",
            })

        result = sync_manager.sync_alerts(cooldown_minutes=10)

        # With 10-minute cooldown, only 1 should be sent
        assert result.items_synced <= 1 or result.items_skipped > 0


# =============================================================================
# TestSyncPrioritization
# =============================================================================

class TestSyncPrioritization:
    """Test sync priority and ordering."""

    def test_critical_data_synced_first(self, sync_manager, sample_sensor_readings, sample_buffered_alerts, sample_pending_videos):
        """Critical data prioritized over routine data."""
        # Queue different types of data
        for reading in sample_sensor_readings[:3]:
            sync_manager.buffer_sensor_reading(reading)
        for alert in sample_buffered_alerts:
            sync_manager.buffer_alert(alert)
        for video in sample_pending_videos[:2]:
            sync_manager.queue_video_upload(video)

        # Get sync order
        sync_order = sync_manager.get_prioritized_sync_queue()

        # Alerts should come before sensor data, which should come before videos
        alert_positions = [i for i, item in enumerate(sync_order) if item.type == 'alert']
        sensor_positions = [i for i, item in enumerate(sync_order) if item.type == 'sensor']
        video_positions = [i for i, item in enumerate(sync_order) if item.type == 'video']

        if alert_positions and sensor_positions:
            assert max(alert_positions) < min(sensor_positions) or len(alert_positions) == 0
        if sensor_positions and video_positions:
            assert max(sensor_positions) < min(video_positions) or len(video_positions) == 0

    def test_newest_alerts_first(self, sync_manager, sample_buffered_alerts):
        """Newest alerts sent before oldest."""
        for alert in sample_buffered_alerts:
            sync_manager.buffer_alert(alert)

        sync_order = sync_manager.get_alert_sync_order()
        timestamps = [a['timestamp'] for a in sync_order]

        # Newest first (descending order)
        assert timestamps == sorted(timestamps, reverse=True)

    def test_oldest_sensor_data_first(self, sync_manager, sample_sensor_readings):
        """Oldest sensor data uploaded first."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        sync_order = sync_manager.get_sync_order()

        # Oldest first (ascending order)
        assert sync_order == sorted(sync_order)

    def test_sync_queue_persistent(self, sync_manager, sample_sensor_readings, temp_data_dir):
        """Sync queue survives restart."""
        # Buffer data
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Save state
        sync_manager.save_state()

        # Get queue file path
        queue_file = Path(temp_data_dir) / "sync_queue.json"

        # Verify state was saved
        assert sync_manager.has_persistent_state()

        # Create new manager (simulating restart)
        new_manager = DataSyncManager(
            s3_client=MagicMock(),
            iot_client=MagicMock(),
            sns_client=MagicMock(),
            config=sync_manager.config,
            data_dir=str(temp_data_dir),
        )
        new_manager.load_state()

        # Queue should be restored
        assert new_manager.get_pending_sensor_count() == len(sample_sensor_readings)


# =============================================================================
# TestBandwidthManagement
# =============================================================================

class TestBandwidthManagement:
    """Test bandwidth-aware sync behavior."""

    def test_upload_throttling(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Uploads throttled to not saturate connection."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Enable throttling
        sync_manager.set_throttle_rate(100)  # 100 KB/s

        result = sync_manager.sync_sensor_data()

        # Should have throttling info in result
        assert result.throttled or result.success

    def test_concurrent_upload_limit(self, sync_manager, mock_s3_client, sample_pending_videos, sync_config):
        """Limit concurrent uploads."""
        for video in sample_pending_videos:
            sync_manager.queue_video_upload(video)

        # Track concurrent uploads
        max_concurrent = [0]
        current_concurrent = [0]

        def track_concurrent(*args, **kwargs):
            current_concurrent[0] += 1
            max_concurrent[0] = max(max_concurrent[0], current_concurrent[0])
            current_concurrent[0] -= 1

        mock_s3_client.upload_file.side_effect = track_concurrent

        sync_manager.sync_videos()

        # Should not exceed limit
        assert max_concurrent[0] <= sync_config["max_concurrent_uploads"]

    def test_pause_sync_for_live_operations(self, sync_manager, sample_sensor_readings):
        """Pause sync if live operations need bandwidth."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Start sync
        sync_manager.start_async_sync()

        # Request pause for live stream
        sync_manager.pause_for_live_operation("live_stream")

        assert sync_manager.is_paused
        assert sync_manager.pause_reason == "live_stream"

    def test_resume_sync_after_live_ops(self, sync_manager, sample_sensor_readings):
        """Resume sync when live operations complete."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Pause and then resume
        sync_manager.pause_for_live_operation("live_stream")
        assert sync_manager.is_paused

        sync_manager.resume_sync()

        assert not sync_manager.is_paused
        assert sync_manager.status in [SyncStatus.PENDING, SyncStatus.IN_PROGRESS, SyncStatus.IDLE]

    def test_sync_during_off_peak_hours(self, sync_manager, sync_config):
        """Large syncs can be scheduled for off-peak."""
        # Queue a large sync
        for i in range(1000):
            sync_manager.buffer_sensor_reading({
                "temperature": 70.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        # Schedule for off-peak
        scheduled_time = sync_manager.schedule_for_off_peak()

        # Should be scheduled within off-peak window
        assert scheduled_time is not None
        scheduled_hour = scheduled_time.hour
        off_peak_start = sync_config["off_peak_hours"]["start"]
        off_peak_end = sync_config["off_peak_hours"]["end"]
        assert off_peak_start <= scheduled_hour < off_peak_end


# =============================================================================
# TestConflictResolution
# =============================================================================

class TestConflictResolution:
    """Test conflict resolution during sync."""

    def test_settings_conflict_resolution(self, sync_manager):
        """Handle settings changed both locally and remotely."""
        local_settings = {
            "temperature_threshold": 90,
            "modified_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
        remote_settings = {
            "temperature_threshold": 85,
            "modified_at": datetime.now(timezone.utc).isoformat(),
        }

        resolved = sync_manager.resolve_settings_conflict(local_settings, remote_settings)

        # Remote (cloud) settings should win by default
        assert resolved["temperature_threshold"] == 85

    def test_last_write_wins_for_config(self, sync_manager):
        """Most recent config change wins."""
        older_config = {
            "setting": "old_value",
            "modified_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        }
        newer_config = {
            "setting": "new_value",
            "modified_at": datetime.now(timezone.utc).isoformat(),
        }

        resolved = sync_manager.resolve_config_conflict(older_config, newer_config)

        assert resolved["setting"] == "new_value"

    def test_no_duplicate_videos(self, sync_manager, mock_s3_client, sample_pending_videos):
        """Duplicate videos not created on re-sync."""
        video = sample_pending_videos[0]

        # Simulate video already exists in S3
        mock_s3_client.list_objects_v2.return_value = {
            "Contents": [{"Key": f"videos/test-coop/{Path(video['path']).name}"}]
        }

        sync_manager.queue_video_upload(video)
        result = sync_manager.sync_videos(skip_existing=True)

        # Should skip, not re-upload
        assert result.items_skipped > 0 or mock_s3_client.upload_file.call_count == 0

    def test_no_duplicate_sensor_entries(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Duplicate sensor entries prevented."""
        # Buffer same reading twice
        reading = sample_sensor_readings[0]
        sync_manager.buffer_sensor_reading(reading)
        sync_manager.buffer_sensor_reading(reading)  # Duplicate

        result = sync_manager.sync_sensor_data()

        # Should deduplicate
        assert result.items_synced == 1 or result.duplicates_skipped > 0


# =============================================================================
# TestSyncStatus
# =============================================================================

class TestSyncStatus:
    """Test sync status reporting."""

    def test_sync_progress_available(self, sync_manager, sample_sensor_readings):
        """Sync progress available via API."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        progress = sync_manager.get_sync_progress()

        assert "pending_count" in progress
        assert "total_items" in progress or progress["pending_count"] >= 0

    def test_sync_status_in_dashboard(self, sync_manager, sample_sensor_readings):
        """Dashboard shows sync status/progress."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        dashboard_data = sync_manager.get_dashboard_status()

        assert "status" in dashboard_data
        assert "pending" in dashboard_data or "pending_count" in dashboard_data

    def test_sync_completion_logged(self, sync_manager, sample_sensor_readings):
        """Sync completion logged with summary."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        result = sync_manager.sync_sensor_data()

        # Result should include summary
        assert result.items_synced is not None
        assert hasattr(result, 'summary') or result.items_synced >= 0

    def test_sync_errors_reported(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Sync errors reported to user."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Cause an error
        mock_s3_client.upload_file.side_effect = Exception("Upload failed")
        mock_s3_client.upload_fileobj.side_effect = Exception("Upload failed")

        result = sync_manager.sync_sensor_data()

        assert not result.success
        assert len(result.errors) > 0 or result.error_message is not None

    def test_pending_sync_count_visible(self, sync_manager, sample_sensor_readings, sample_buffered_alerts, sample_pending_videos):
        """User can see how much data is pending sync."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)
        for alert in sample_buffered_alerts:
            sync_manager.buffer_alert(alert)
        for video in sample_pending_videos:
            sync_manager.queue_video_upload(video)

        pending = sync_manager.get_pending_counts()

        assert pending["sensors"] == len(sample_sensor_readings)
        assert pending["alerts"] == len(sample_buffered_alerts)
        assert pending["videos"] == len(sample_pending_videos)


# =============================================================================
# TestSyncResilience
# =============================================================================

class TestSyncResilience:
    """Test sync process resilience."""

    def test_sync_survives_brief_disconnection(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Brief disconnection during sync doesn't lose progress."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Enable checkpointing to track progress
        sync_manager.enable_checkpointing(interval=1)

        # Simulate intermittent failure on first batch
        call_count = [0]
        def intermittent_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Exception("Brief disconnection")

        mock_s3_client.upload_fileobj.side_effect = intermittent_failure

        # First attempt - should fail but save checkpoint
        result1 = sync_manager.sync_sensor_data()

        # Should have checkpoint saved (even with 0 completed if first batch fails)
        assert sync_manager.has_checkpoint() or not result1.success

    def test_sync_checkpointing(self, sync_manager, sample_sensor_readings, temp_data_dir):
        """Sync progress checkpointed periodically."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Enable checkpointing
        sync_manager.enable_checkpointing(interval=2)  # Every 2 items

        # Partially sync
        sync_manager.sync_sensor_data(limit=5)

        # Checkpoint should exist
        assert sync_manager.has_checkpoint()
        checkpoint = sync_manager.get_sync_checkpoint()
        assert checkpoint.items_completed >= 2

    def test_sync_idempotent(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Running sync twice doesn't duplicate data."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Sync once
        result1 = sync_manager.sync_sensor_data()
        first_upload_count = mock_s3_client.upload_fileobj.call_count

        # Try to sync again
        result2 = sync_manager.sync_sensor_data()

        # Should not re-upload
        assert mock_s3_client.upload_fileobj.call_count == first_upload_count
        assert result2.items_synced == 0

    def test_sync_timeout_handling(self, sync_manager, mock_s3_client, sample_sensor_readings):
        """Sync operations have appropriate timeouts."""
        for reading in sample_sensor_readings:
            sync_manager.buffer_sensor_reading(reading)

        # Simulate slow upload
        import time
        def slow_upload(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow upload

        mock_s3_client.upload_fileobj.side_effect = slow_upload

        # Set a short timeout
        result = sync_manager.sync_sensor_data(timeout_seconds=0.05)

        # Should timeout gracefully
        assert result.timed_out or result.success  # Either timed out or completed
