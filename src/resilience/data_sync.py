"""Data synchronization manager for syncing buffered data after connectivity restoration.

This module provides the DataSyncManager orchestrator which coordinates
sensor data, video, and alert synchronization using dedicated handler classes.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Re-export models for backward compatibility
from src.resilience.sync_models import (
    SyncCheckpoint,
    SyncItem,
    SyncPriority,
    SyncResult,
    SyncStatus,
)
from src.resilience.sync_handlers import (
    AlertSyncHandler,
    SensorSyncHandler,
    VideoSyncHandler,
    hash_reading,
)


class DataSyncManager:
    """Manages data synchronization between local device and cloud services.

    Handles buffering, prioritization, and resilient upload of sensor data,
    videos, and alerts after network connectivity is restored.
    """

    def __init__(
        self,
        s3_client: Any,
        iot_client: Any,
        sns_client: Any,
        config: Dict[str, Any],
        data_dir: str,
    ):
        """Initialize the data sync manager.

        Args:
            s3_client: AWS S3 client for object storage.
            iot_client: AWS IoT client for real-time messaging.
            sns_client: AWS SNS client for notifications.
            config: Sync configuration dictionary.
            data_dir: Local directory for buffered data.
        """
        self.s3_client = s3_client
        self.iot_client = iot_client
        self.sns_client = sns_client
        self.config = config
        self.data_dir = Path(data_dir)

        # Handlers
        self._sensor_handler = SensorSyncHandler(s3_client, iot_client, config)
        self._video_handler = VideoSyncHandler(s3_client, config)
        self._alert_handler = AlertSyncHandler(sns_client, config)

        # State tracking
        self._status = SyncStatus.IDLE
        self._is_syncing = False
        self._sync_scheduled = False
        self._scheduled_sync_time: Optional[datetime] = None
        self._is_paused = False
        self._pause_reason: Optional[str] = None
        self._retry_count = 0
        self._last_sync_trigger: Optional[str] = None
        self._throttle_rate: Optional[int] = None

        # Buffers
        self._sensor_buffer: List[Dict[str, Any]] = []
        self._video_queue: List[Dict[str, Any]] = []
        self._alert_buffer: List[Dict[str, Any]] = []
        self._synced_sensor_hashes: set = set()
        self._duplicates_skipped: int = 0

        # Checkpointing
        self._checkpoint: Optional[SyncCheckpoint] = None
        self._checkpointing_enabled = False
        self._checkpoint_interval = 10

        # State file
        self._state_file = self.data_dir / "sync_queue.json"

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def status(self) -> SyncStatus:
        """Get current sync status."""
        return self._status

    @property
    def is_syncing(self) -> bool:
        """Check if sync is currently in progress."""
        return self._is_syncing

    @property
    def sync_scheduled(self) -> bool:
        """Check if sync is scheduled."""
        return self._sync_scheduled

    @property
    def scheduled_sync_time(self) -> Optional[datetime]:
        """Get scheduled sync time."""
        return self._scheduled_sync_time

    @property
    def is_paused(self) -> bool:
        """Check if sync is paused."""
        return self._is_paused

    @property
    def pause_reason(self) -> Optional[str]:
        """Get reason for pause."""
        return self._pause_reason

    @property
    def retry_count(self) -> int:
        """Get current retry count."""
        return self._retry_count

    @property
    def last_sync_trigger(self) -> Optional[str]:
        """Get last sync trigger type."""
        return self._last_sync_trigger

    # -------------------------------------------------------------------------
    # Buffering Methods
    # -------------------------------------------------------------------------

    def buffer_sensor_reading(self, reading: Dict[str, Any]) -> None:
        """Buffer a sensor reading for later sync.

        Args:
            reading: Sensor reading data.
        """
        reading_hash = hash_reading(reading)
        if reading_hash not in self._synced_sensor_hashes:
            existing_hashes = {hash_reading(r) for r in self._sensor_buffer}
            if reading_hash not in existing_hashes:
                self._sensor_buffer.append(reading)
            else:
                self._duplicates_skipped += 1

    def queue_video_upload(self, video: Dict[str, Any]) -> None:
        """Queue a video for upload.

        Args:
            video: Video metadata including path.
        """
        self._video_queue.append(video)

    def buffer_alert(self, alert: Dict[str, Any]) -> None:
        """Buffer an alert for later delivery.

        Args:
            alert: Alert data.
        """
        self._alert_buffer.append(alert)

    def _hash_reading(self, reading: Dict[str, Any]) -> str:
        """Create a hash of a reading for deduplication."""
        return hash_reading(reading)

    # -------------------------------------------------------------------------
    # Sync Trigger Methods
    # -------------------------------------------------------------------------

    def on_connectivity_restored(self) -> None:
        """Handle connectivity restoration - schedule sync with delay."""
        delay_seconds = self.config.get("reconnection_delay_seconds", 5)
        self._scheduled_sync_time = datetime.now(timezone.utc) + timedelta(
            seconds=delay_seconds
        )
        self._sync_scheduled = True
        self._status = SyncStatus.PENDING

    def trigger_manual_sync(self) -> SyncResult:
        """Trigger manual sync immediately.

        Returns:
            SyncResult with sync outcome.
        """
        self._last_sync_trigger = "manual"
        return self.sync_all()

    def sync_all(self) -> SyncResult:
        """Sync all buffered data.

        Returns:
            SyncResult with combined outcome.
        """
        self._is_syncing = True
        self._status = SyncStatus.IN_PROGRESS

        result = SyncResult()

        try:
            alert_result = self.sync_alerts()
            sensor_result = self.sync_sensor_data()
            video_result = self.sync_videos()

            result.success = (
                alert_result.success and sensor_result.success and video_result.success
            )
            result.items_synced = (
                alert_result.items_synced
                + sensor_result.items_synced
                + video_result.items_synced
            )
            result.errors = alert_result.errors + sensor_result.errors + video_result.errors

            if result.success:
                self._status = SyncStatus.COMPLETED
                self._retry_count = 0
                self._sync_scheduled = False
            else:
                self._status = SyncStatus.FAILED
                self._retry_count += 1
                self._sync_scheduled = True

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(str(e))
            self._status = SyncStatus.FAILED
            self._retry_count += 1
            self._sync_scheduled = True

        finally:
            self._is_syncing = False

        return result

    # -------------------------------------------------------------------------
    # Delegated Sync Methods
    # -------------------------------------------------------------------------

    def sync_sensor_data(
        self,
        publish_to_iot: bool = False,
        resume_from_checkpoint: bool = False,
        limit: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> SyncResult:
        """Sync buffered sensor data to S3 and optionally IoT.

        Args:
            publish_to_iot: Whether to publish to IoT Core.
            resume_from_checkpoint: Resume from last checkpoint.
            limit: Maximum items to sync.
            timeout_seconds: Timeout for sync operation.

        Returns:
            SyncResult with sync outcome.
        """
        result, self._sensor_buffer, self._checkpoint = self._sensor_handler.sync(
            sensor_buffer=self._sensor_buffer,
            synced_hashes=self._synced_sensor_hashes,
            checkpoint=self._checkpoint,
            checkpointing_enabled=self._checkpointing_enabled,
            throttle_rate=self._throttle_rate,
            duplicates_skipped=self._duplicates_skipped,
            publish_to_iot=publish_to_iot,
            resume_from_checkpoint=resume_from_checkpoint,
            limit=limit,
            timeout_seconds=timeout_seconds,
        )
        return result

    def sync_videos(
        self,
        generate_thumbnails: bool = False,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        max_retries: int = 3,
        delete_after_upload: bool = False,
        skip_existing: bool = False,
    ) -> SyncResult:
        """Sync queued videos to S3.

        Args:
            generate_thumbnails: Generate and upload thumbnails.
            progress_callback: Callback for progress updates.
            max_retries: Maximum retry attempts.
            delete_after_upload: Delete local file after upload.
            skip_existing: Skip videos that already exist in S3.

        Returns:
            SyncResult with sync outcome.
        """
        result, self._video_queue = self._video_handler.sync(
            video_queue=self._video_queue,
            generate_thumbnails=generate_thumbnails,
            progress_callback=progress_callback,
            max_retries=max_retries,
            delete_after_upload=delete_after_upload,
            skip_existing=skip_existing,
        )
        return result

    def sync_alerts(
        self,
        aggregate_similar: bool = False,
        cooldown_minutes: int = 0,
    ) -> SyncResult:
        """Sync buffered alerts via SNS.

        Args:
            aggregate_similar: Aggregate similar alerts.
            cooldown_minutes: Minimum minutes between same alert type.

        Returns:
            SyncResult with sync outcome.
        """
        result = self._alert_handler.sync(
            alert_buffer=self._alert_buffer,
            aggregate_similar=aggregate_similar,
            cooldown_minutes=cooldown_minutes,
        )
        if result.success or result.items_synced > 0:
            self._alert_buffer.clear()
        return result

    def get_sync_order(self) -> List[str]:
        """Get the order timestamps will be synced.

        Returns:
            List of timestamps in sync order.
        """
        return sorted([r.get("timestamp", "") for r in self._sensor_buffer])

    def get_pending_sensor_count(self) -> int:
        """Get count of pending sensor readings.

        Returns:
            Number of pending sensor readings.
        """
        return len(self._sensor_buffer)

    def get_alert_sync_order(self) -> List[Dict[str, Any]]:
        """Get alerts in sync order.

        Returns:
            List of alerts in priority/timestamp order.
        """
        return self._alert_handler.get_sync_order(self._alert_buffer)

    # -------------------------------------------------------------------------
    # Prioritization
    # -------------------------------------------------------------------------

    def get_prioritized_sync_queue(self) -> List[SyncItem]:
        """Get all sync items in priority order.

        Order: alerts (0) > headcount (1) > sensors (2) > videos (3)

        Returns:
            List of SyncItems ordered by priority.
        """
        items = []
        TYPE_PRIORITY = {"alert": 0, "headcount": 1, "sensor": 2, "video": 3}

        for alert in self._alert_buffer:
            items.append(
                SyncItem(
                    type="alert",
                    data=alert,
                    priority=alert.get("priority", SyncPriority.NORMAL),
                    timestamp=alert.get("timestamp", ""),
                )
            )

        for reading in self._sensor_buffer:
            items.append(
                SyncItem(
                    type="sensor",
                    data=reading,
                    priority=SyncPriority.NORMAL,
                    timestamp=reading.get("timestamp", ""),
                )
            )

        for video in self._video_queue:
            items.append(
                SyncItem(
                    type="video",
                    data=video,
                    priority=SyncPriority.LOW,
                    timestamp=video.get("timestamp", ""),
                )
            )

        return sorted(items, key=lambda i: (TYPE_PRIORITY.get(i.type, 99), i.priority, i.timestamp))

    # -------------------------------------------------------------------------
    # Bandwidth Management
    # -------------------------------------------------------------------------

    def set_throttle_rate(self, kbps: int) -> None:
        """Set upload throttle rate.

        Args:
            kbps: Kilobytes per second limit.
        """
        self._throttle_rate = kbps

    def pause_for_live_operation(self, reason: str) -> None:
        """Pause sync for live operation.

        Args:
            reason: Reason for pause (e.g., 'live_stream').
        """
        self._is_paused = True
        self._pause_reason = reason
        self._status = SyncStatus.PAUSED

    def resume_sync(self) -> None:
        """Resume paused sync."""
        self._is_paused = False
        self._pause_reason = None
        if self._sensor_buffer or self._video_queue or self._alert_buffer:
            self._status = SyncStatus.PENDING
        else:
            self._status = SyncStatus.IDLE

    def start_async_sync(self) -> None:
        """Start async sync operation."""
        self._sync_scheduled = True
        self._status = SyncStatus.PENDING

    def schedule_for_off_peak(self) -> datetime:
        """Schedule sync for off-peak hours.

        Returns:
            Scheduled datetime.
        """
        off_peak = self.config.get("off_peak_hours", {"start": 2, "end": 6})
        now = datetime.now(timezone.utc)

        target_hour = off_peak["start"]
        if now.hour >= target_hour and now.hour < off_peak["end"]:
            scheduled = now
        elif now.hour < target_hour:
            scheduled = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        else:
            scheduled = (now + timedelta(days=1)).replace(
                hour=target_hour, minute=0, second=0, microsecond=0
            )

        self._scheduled_sync_time = scheduled
        self._sync_scheduled = True
        return scheduled

    # -------------------------------------------------------------------------
    # Conflict Resolution
    # -------------------------------------------------------------------------

    def resolve_settings_conflict(
        self, local: Dict[str, Any], remote: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve settings conflict (remote wins by default).

        Args:
            local: Local settings.
            remote: Remote settings.

        Returns:
            Resolved settings.
        """
        return remote

    def resolve_config_conflict(
        self, config1: Dict[str, Any], config2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Resolve config conflict (last write wins).

        Args:
            config1: First config.
            config2: Second config.

        Returns:
            Config with most recent modification.
        """
        time1 = config1.get("modified_at", "")
        time2 = config2.get("modified_at", "")

        if time1 > time2:
            return config1
        return config2

    # -------------------------------------------------------------------------
    # Status and Progress
    # -------------------------------------------------------------------------

    def get_sync_progress(self) -> Dict[str, Any]:
        """Get current sync progress.

        Returns:
            Progress information dictionary.
        """
        total = len(self._sensor_buffer) + len(self._video_queue) + len(self._alert_buffer)
        completed = self._checkpoint.items_completed if self._checkpoint else 0

        return {
            "pending_count": total,
            "total_items": total,
            "completed": completed,
            "status": self._status.name,
        }

    def get_dashboard_status(self) -> Dict[str, Any]:
        """Get status for dashboard display.

        Returns:
            Dashboard status dictionary.
        """
        return {
            "status": self._status.name,
            "pending": len(self._sensor_buffer)
            + len(self._video_queue)
            + len(self._alert_buffer),
            "pending_count": len(self._sensor_buffer)
            + len(self._video_queue)
            + len(self._alert_buffer),
            "is_syncing": self._is_syncing,
            "is_paused": self._is_paused,
            "retry_count": self._retry_count,
        }

    def get_pending_counts(self) -> Dict[str, int]:
        """Get counts of pending items by type.

        Returns:
            Dictionary with counts by type.
        """
        return {
            "sensors": len(self._sensor_buffer),
            "alerts": len(self._alert_buffer),
            "videos": len(self._video_queue),
        }

    # -------------------------------------------------------------------------
    # Checkpointing and Persistence
    # -------------------------------------------------------------------------

    def enable_checkpointing(self, interval: int = 10) -> None:
        """Enable sync checkpointing.

        Args:
            interval: Checkpoint every N items.
        """
        self._checkpointing_enabled = True
        self._checkpoint_interval = interval

    def has_checkpoint(self) -> bool:
        """Check if checkpoint exists.

        Returns:
            True if checkpoint exists.
        """
        return self._checkpoint is not None

    def get_sync_checkpoint(self) -> Optional[SyncCheckpoint]:
        """Get current checkpoint.

        Returns:
            Current checkpoint or None.
        """
        return self._checkpoint

    def has_persistent_state(self) -> bool:
        """Check if persistent state exists.

        Returns:
            True if state file exists.
        """
        return self._state_file.exists()

    def save_state(self) -> None:
        """Save sync state to disk."""
        state = {
            "sensor_buffer": self._sensor_buffer,
            "video_queue": [
                {k: v for k, v in v.items() if k != "path" or isinstance(v, str)}
                for v in self._video_queue
            ],
            "alert_buffer": [
                {
                    k: (v.value if hasattr(v, "value") else v)
                    for k, v in a.items()
                }
                for a in self._alert_buffer
            ],
            "checkpoint": {
                "items_completed": self._checkpoint.items_completed,
                "timestamp": self._checkpoint.timestamp,
            }
            if self._checkpoint
            else None,
        }

        self._state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state_file.write_text(json.dumps(state, default=str))

    def load_state(self) -> None:
        """Load sync state from disk."""
        if not self._state_file.exists():
            return

        try:
            state = json.loads(self._state_file.read_text())
            self._sensor_buffer = state.get("sensor_buffer", [])
            self._video_queue = state.get("video_queue", [])
            self._alert_buffer = state.get("alert_buffer", [])

            if state.get("checkpoint"):
                self._checkpoint = SyncCheckpoint(
                    items_completed=state["checkpoint"].get("items_completed", 0),
                    timestamp=state["checkpoint"].get("timestamp", ""),
                )
        except Exception:
            pass
