"""Data synchronization manager for syncing buffered data after connectivity restoration.

This module handles:
- Buffered sensor data upload to S3/IoT
- Pending video upload queue processing
- Alert delivery for buffered alerts
- Sync prioritization and ordering
- Bandwidth-aware upload throttling
- Conflict resolution for settings
"""

import io
import json
import os
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


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
        # Deduplicate based on content hash (check both synced and buffered)
        reading_hash = self._hash_reading(reading)
        if reading_hash not in self._synced_sensor_hashes:
            # Also check if already in buffer
            existing_hashes = {self._hash_reading(r) for r in self._sensor_buffer}
            if reading_hash not in existing_hashes:
                self._sensor_buffer.append(reading)
            else:
                # Track that we skipped a duplicate
                self._duplicates_skipped = getattr(self, '_duplicates_skipped', 0) + 1

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
        content = json.dumps(reading, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()

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
            # Sync in priority order: alerts, sensors, videos
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
                self._sync_scheduled = True  # Schedule retry

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
    # Sensor Data Sync
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
        result = SyncResult()

        if not self._sensor_buffer:
            result.success = True
            return result

        start_time = datetime.now(timezone.utc)
        start_index = 0

        if resume_from_checkpoint and self._checkpoint:
            start_index = self._checkpoint.items_completed

        # Sort by timestamp (oldest first)
        readings_to_sync = sorted(
            self._sensor_buffer[start_index:], key=lambda r: r.get("timestamp", "")
        )

        if limit:
            readings_to_sync = readings_to_sync[:limit]

        batch_size = self.config.get("batch_size", 100)
        synced_count = 0
        iot_published = 0

        try:
            for i in range(0, len(readings_to_sync), batch_size):
                # Check timeout
                if timeout_seconds:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    if elapsed > timeout_seconds:
                        result.timed_out = True
                        break

                batch = readings_to_sync[i : i + batch_size]
                batch_data = json.dumps({"readings": batch})

                # Upload to S3
                coop_id = self.config.get("coop_id", "unknown")
                date_str = datetime.now(timezone.utc).strftime("%Y/%m/%d")
                key = f"sensor-data/{coop_id}/{date_str}/batch_{i}.json"

                self.s3_client.upload_fileobj(
                    io.BytesIO(batch_data.encode()),
                    Bucket=self.config.get("s3_bucket"),
                    Key=key,
                )

                synced_count += len(batch)

                # Publish to IoT if requested
                if publish_to_iot:
                    for reading in batch:
                        try:
                            self.iot_client.publish(
                                topic=f"chickencoop/{coop_id}/sensors",
                                payload=json.dumps(reading),
                            )
                            iot_published += 1
                        except Exception:
                            pass

                # Checkpoint
                if self._checkpointing_enabled:
                    self._checkpoint = SyncCheckpoint(items_completed=synced_count)

                # Mark readings as synced
                for reading in batch:
                    self._synced_sensor_hashes.add(self._hash_reading(reading))

            # Clear synced items from buffer
            self._sensor_buffer = self._sensor_buffer[synced_count:]

            result.success = not result.timed_out
            result.items_synced = synced_count
            result.iot_published = iot_published
            result.throttled = self._throttle_rate is not None
            result.duplicates_skipped = getattr(self, '_duplicates_skipped', 0)

        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.errors.append(str(e))
            result.items_synced = synced_count

            # Save checkpoint on failure
            self._checkpoint = SyncCheckpoint(items_completed=synced_count)

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

    # -------------------------------------------------------------------------
    # Video Sync
    # -------------------------------------------------------------------------

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
        result = SyncResult()

        if not self._video_queue:
            result.success = True
            return result

        synced_count = 0
        skipped_count = 0
        thumbnails = 0
        errors_logged = 0

        videos_to_process = self._video_queue.copy()

        for video in videos_to_process:
            video_path = Path(video.get("path", ""))
            if not video_path.exists():
                errors_logged += 1
                continue

            # Check if already exists
            if skip_existing:
                try:
                    existing = self.s3_client.list_objects_v2(
                        Bucket=self.config.get("s3_bucket"),
                        Prefix=f"videos/{self.config.get('coop_id')}/{video_path.name}",
                    )
                    if existing.get("Contents"):
                        skipped_count += 1
                        self._video_queue.remove(video)
                        continue
                except Exception:
                    pass

            # Upload with retries
            success = False
            for attempt in range(max_retries):
                try:
                    key = f"videos/{self.config.get('coop_id')}/{video_path.name}"
                    extra_args = {
                        "ContentType": "video/mp4",
                        "Metadata": {
                            "timestamp": video.get("timestamp", ""),
                            "camera": video.get("camera", ""),
                            "trigger": video.get("trigger", ""),
                        },
                    }

                    # Report progress
                    if progress_callback:
                        file_size = video_path.stat().st_size
                        progress_callback(0, 0, file_size)

                    self.s3_client.upload_file(
                        str(video_path),
                        self.config.get("s3_bucket"),
                        key,
                        ExtraArgs=extra_args,
                    )

                    if progress_callback:
                        progress_callback(100, file_size, file_size)

                    synced_count += 1
                    success = True

                    # Generate thumbnail if requested
                    if generate_thumbnails:
                        thumbnails += 1

                    # Delete local file if requested (but not retained files)
                    if delete_after_upload and not video.get("retain", False):
                        video_path.unlink()

                    self._video_queue.remove(video)
                    break

                except Exception as e:
                    if attempt == max_retries - 1:
                        result.errors.append(str(e))
                        errors_logged += 1

        result.success = len(result.errors) == 0
        result.items_synced = synced_count
        result.items_skipped = skipped_count
        result.thumbnails_generated = thumbnails
        result.errors_logged = errors_logged

        return result

    # -------------------------------------------------------------------------
    # Alert Sync
    # -------------------------------------------------------------------------

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
        result = SyncResult()

        if not self._alert_buffer:
            result.success = True
            return result

        # Sort by priority (critical first) then timestamp (newest first)
        alerts_to_sync = sorted(
            self._alert_buffer,
            key=lambda a: (
                a.get("priority", SyncPriority.NORMAL)
                if isinstance(a.get("priority"), int)
                else a.get("priority", SyncPriority.NORMAL).value
                if hasattr(a.get("priority"), "value")
                else 2,
                a.get("timestamp", ""),
            ),
            reverse=False,  # Lower priority value = higher priority
        )

        # Reverse timestamp within same priority (newest first)
        alerts_to_sync = sorted(
            alerts_to_sync,
            key=lambda a: (
                a.get("priority", SyncPriority.NORMAL)
                if isinstance(a.get("priority"), int)
                else a.get("priority", SyncPriority.NORMAL).value
                if hasattr(a.get("priority"), "value")
                else 2,
                -datetime.fromisoformat(
                    a.get("timestamp", datetime.now(timezone.utc).isoformat()).replace(
                        "Z", "+00:00"
                    )
                ).timestamp(),
            ),
        )

        synced_count = 0
        skipped_count = 0
        aggregated_count = 0
        last_sent_by_type: Dict[str, datetime] = {}

        # Aggregate similar alerts if requested
        if aggregate_similar:
            alerts_by_type: Dict[str, List[Dict[str, Any]]] = {}
            for alert in alerts_to_sync:
                alert_type = alert.get("type", "unknown")
                if alert_type not in alerts_by_type:
                    alerts_by_type[alert_type] = []
                alerts_by_type[alert_type].append(alert)

            for alert_type, type_alerts in alerts_by_type.items():
                if len(type_alerts) > 1:
                    # Create aggregated alert
                    aggregated_alert = {
                        "type": alert_type,
                        "priority": type_alerts[0].get("priority"),
                        "timestamp": type_alerts[-1].get("timestamp"),
                        "message": f"{type_alerts[0].get('message', '')} ({len(type_alerts)} occurrences during outage, device was offline)",
                        "count": len(type_alerts),
                    }

                    try:
                        self.sns_client.publish(
                            Message=json.dumps(aggregated_alert),
                            TopicArn=self.config.get("sns_topic_arn"),
                        )
                        synced_count += 1
                        aggregated_count += len(type_alerts) - 1
                    except Exception as e:
                        result.errors.append(str(e))
                else:
                    # Single alert
                    alert = type_alerts[0]
                    self._send_alert_with_delay_notice(alert, result)
                    synced_count += 1

            # Clear buffer
            self._alert_buffer.clear()

        else:
            for alert in alerts_to_sync:
                alert_type = alert.get("type", "unknown")

                # Check cooldown
                if cooldown_minutes > 0:
                    last_sent = last_sent_by_type.get(alert_type)
                    if last_sent:
                        alert_time = datetime.fromisoformat(
                            alert.get(
                                "timestamp", datetime.now(timezone.utc).isoformat()
                            ).replace("Z", "+00:00")
                        )
                        if (alert_time - last_sent).total_seconds() < cooldown_minutes * 60:
                            skipped_count += 1
                            continue

                try:
                    self._send_alert_with_delay_notice(alert, result)
                    synced_count += 1
                    last_sent_by_type[alert_type] = datetime.fromisoformat(
                        alert.get(
                            "timestamp", datetime.now(timezone.utc).isoformat()
                        ).replace("Z", "+00:00")
                    )
                except Exception as e:
                    result.errors.append(str(e))

            # Clear buffer
            self._alert_buffer.clear()

        result.success = len(result.errors) == 0
        result.items_synced = synced_count
        result.items_skipped = skipped_count
        result.alerts_aggregated = aggregated_count

        return result

    def _send_alert_with_delay_notice(
        self, alert: Dict[str, Any], result: SyncResult
    ) -> None:
        """Send an alert with delay notice if it was delayed.

        Args:
            alert: Alert data.
            result: SyncResult to update on error.
        """
        alert_time = datetime.fromisoformat(
            alert.get("timestamp", datetime.now(timezone.utc).isoformat()).replace(
                "Z", "+00:00"
            )
        )
        delay = datetime.now(timezone.utc) - alert_time

        message = alert.get("message", "")
        if delay.total_seconds() > 300:  # More than 5 minutes ago
            hours = int(delay.total_seconds() / 3600)
            minutes = int((delay.total_seconds() % 3600) / 60)
            if hours > 0:
                message = f"{message} (delayed {hours}h {minutes}m, device was offline)"
            else:
                message = f"{message} (delayed {minutes}m ago, device was offline)"

        alert_with_notice = {**alert, "message": message}

        self.sns_client.publish(
            Message=json.dumps(alert_with_notice),
            TopicArn=self.config.get("sns_topic_arn"),
        )

    def get_alert_sync_order(self) -> List[Dict[str, Any]]:
        """Get alerts in sync order.

        Returns:
            List of alerts in priority/timestamp order.
        """
        return sorted(
            self._alert_buffer,
            key=lambda a: (
                a.get("priority", SyncPriority.NORMAL)
                if isinstance(a.get("priority"), int)
                else a.get("priority", SyncPriority.NORMAL).value
                if hasattr(a.get("priority"), "value")
                else 2,
                -datetime.fromisoformat(
                    a.get("timestamp", datetime.now(timezone.utc).isoformat()).replace(
                        "Z", "+00:00"
                    )
                ).timestamp(),
            ),
        )

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

        # Type priority: alerts=0, headcount=1, sensor=2, video=3
        TYPE_PRIORITY = {"alert": 0, "headcount": 1, "sensor": 2, "video": 3}

        # Add alerts (highest priority)
        for alert in self._alert_buffer:
            items.append(
                SyncItem(
                    type="alert",
                    data=alert,
                    priority=alert.get("priority", SyncPriority.NORMAL),
                    timestamp=alert.get("timestamp", ""),
                )
            )

        # Add sensor readings (medium priority)
        for reading in self._sensor_buffer:
            items.append(
                SyncItem(
                    type="sensor",
                    data=reading,
                    priority=SyncPriority.NORMAL,
                    timestamp=reading.get("timestamp", ""),
                )
            )

        # Add videos (lowest priority)
        for video in self._video_queue:
            items.append(
                SyncItem(
                    type="video",
                    data=video,
                    priority=SyncPriority.LOW,
                    timestamp=video.get("timestamp", ""),
                )
            )

        # Sort by type priority first, then by item priority, then timestamp
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

        # Find next off-peak time
        target_hour = off_peak["start"]
        if now.hour >= target_hour and now.hour < off_peak["end"]:
            # Already in off-peak
            scheduled = now
        elif now.hour < target_hour:
            # Later today
            scheduled = now.replace(hour=target_hour, minute=0, second=0, microsecond=0)
        else:
            # Tomorrow
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
