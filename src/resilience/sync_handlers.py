"""Sync handler classes for sensor data, video, and alert synchronization.

Each handler encapsulates the upload logic for a specific data type,
operating on buffers and clients passed in from the DataSyncManager.
"""

import io
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

from src.resilience.sync_models import SyncCheckpoint, SyncPriority, SyncResult


class SensorSyncHandler:
    """Handles buffered sensor data uploads to S3 and IoT."""

    def __init__(self, s3_client: Any, iot_client: Any, config: Dict[str, Any]):
        """Initialize the sensor sync handler.

        Args:
            s3_client: AWS S3 client for object storage.
            iot_client: AWS IoT client for real-time messaging.
            config: Sync configuration dictionary.
        """
        self.s3_client = s3_client
        self.iot_client = iot_client
        self.config = config

    def sync(
        self,
        sensor_buffer: List[Dict[str, Any]],
        synced_hashes: Set[str],
        checkpoint: Optional[SyncCheckpoint],
        checkpointing_enabled: bool,
        throttle_rate: Optional[int],
        duplicates_skipped: int,
        publish_to_iot: bool = False,
        resume_from_checkpoint: bool = False,
        limit: Optional[int] = None,
        timeout_seconds: Optional[float] = None,
    ) -> tuple[SyncResult, List[Dict[str, Any]], Optional[SyncCheckpoint]]:
        """Sync buffered sensor data to S3 and optionally IoT.

        Args:
            sensor_buffer: List of buffered sensor readings.
            synced_hashes: Set of already-synced reading hashes.
            checkpoint: Current sync checkpoint.
            checkpointing_enabled: Whether checkpointing is active.
            throttle_rate: Current throttle rate or None.
            duplicates_skipped: Count of duplicates skipped so far.
            publish_to_iot: Whether to publish to IoT Core.
            resume_from_checkpoint: Resume from last checkpoint.
            limit: Maximum items to sync.
            timeout_seconds: Timeout for sync operation.

        Returns:
            Tuple of (SyncResult, remaining buffer, updated checkpoint).
        """
        result = SyncResult()

        if not sensor_buffer:
            result.success = True
            return result, sensor_buffer, checkpoint

        start_time = datetime.now(timezone.utc)
        start_index = 0

        if resume_from_checkpoint and checkpoint:
            start_index = checkpoint.items_completed

        # Sort by timestamp (oldest first)
        readings_to_sync = sorted(
            sensor_buffer[start_index:], key=lambda r: r.get("timestamp", "")
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
                        except Exception:  # pylint: disable=broad-exception-caught
                            pass

                # Checkpoint
                if checkpointing_enabled:
                    checkpoint = SyncCheckpoint(items_completed=synced_count)

                # Mark readings as synced
                for reading in batch:
                    synced_hashes.add(hash_reading(reading))

            # Clear synced items from buffer
            remaining_buffer = sensor_buffer[synced_count:]

            result.success = not result.timed_out
            result.items_synced = synced_count
            result.iot_published = iot_published
            result.throttled = throttle_rate is not None
            result.duplicates_skipped = duplicates_skipped

        except Exception as e:  # pylint: disable=broad-exception-caught
            remaining_buffer = sensor_buffer
            result.success = False
            result.error_message = str(e)
            result.errors.append(str(e))
            result.items_synced = synced_count

            # Save checkpoint on failure
            checkpoint = SyncCheckpoint(items_completed=synced_count)

        return result, remaining_buffer, checkpoint


class VideoSyncHandler:
    """Handles video file uploads to S3."""

    def __init__(self, s3_client: Any, config: Dict[str, Any]):
        """Initialize the video sync handler.

        Args:
            s3_client: AWS S3 client for object storage.
            config: Sync configuration dictionary.
        """
        self.s3_client = s3_client
        self.config = config

    def sync(
        self,
        video_queue: List[Dict[str, Any]],
        generate_thumbnails: bool = False,
        progress_callback: Optional[Callable[[int, int, int], None]] = None,
        max_retries: int = 3,
        delete_after_upload: bool = False,
        skip_existing: bool = False,
    ) -> tuple[SyncResult, List[Dict[str, Any]]]:
        """Sync queued videos to S3.

        Args:
            video_queue: List of video metadata dicts to upload.
            generate_thumbnails: Generate and upload thumbnails.
            progress_callback: Callback for progress updates.
            max_retries: Maximum retry attempts.
            delete_after_upload: Delete local file after upload.
            skip_existing: Skip videos that already exist in S3.

        Returns:
            Tuple of (SyncResult, remaining queue).
        """
        result = SyncResult()

        if not video_queue:
            result.success = True
            return result, video_queue

        synced_count = 0
        skipped_count = 0
        thumbnails = 0
        errors_logged = 0

        remaining = video_queue.copy()
        videos_to_process = remaining.copy()

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
                        remaining.remove(video)
                        continue
                except Exception:  # pylint: disable=broad-exception-caught
                    pass

            # Upload with retries
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

                    # Generate thumbnail if requested
                    if generate_thumbnails:
                        thumbnails += 1

                    # Delete local file if requested (but not retained files)
                    if delete_after_upload and not video.get("retain", False):
                        video_path.unlink()

                    remaining.remove(video)
                    break

                except Exception as e:  # pylint: disable=broad-exception-caught
                    if attempt == max_retries - 1:
                        result.errors.append(str(e))
                        errors_logged += 1

        result.success = len(result.errors) == 0
        result.items_synced = synced_count
        result.items_skipped = skipped_count
        result.thumbnails_generated = thumbnails
        result.errors_logged = errors_logged

        return result, remaining


class AlertSyncHandler:
    """Handles buffered alert delivery via SNS."""

    def __init__(self, sns_client: Any, config: Dict[str, Any]):
        """Initialize the alert sync handler.

        Args:
            sns_client: AWS SNS client for notifications.
            config: Sync configuration dictionary.
        """
        self.sns_client = sns_client
        self.config = config

    def sync(
        self,
        alert_buffer: List[Dict[str, Any]],
        aggregate_similar: bool = False,
        cooldown_minutes: int = 0,
    ) -> SyncResult:
        """Sync buffered alerts via SNS.

        Args:
            alert_buffer: List of buffered alerts.
            aggregate_similar: Aggregate similar alerts.
            cooldown_minutes: Minimum minutes between same alert type.

        Returns:
            SyncResult with sync outcome.
        """
        result = SyncResult()

        if not alert_buffer:
            result.success = True
            return result

        # Sort by priority then newest-first within same priority
        alerts_to_sync = self._sort_alerts(alert_buffer)

        synced_count = 0
        skipped_count = 0
        aggregated_count = 0
        last_sent_by_type: Dict[str, datetime] = {}

        if aggregate_similar:
            synced_count, aggregated_count = self._sync_aggregated(
                alerts_to_sync, result
            )
        else:
            synced_count, skipped_count = self._sync_individual(
                alerts_to_sync, result, cooldown_minutes, last_sent_by_type
            )

        result.success = len(result.errors) == 0
        result.items_synced = synced_count
        result.items_skipped = skipped_count
        result.alerts_aggregated = aggregated_count

        return result

    def get_sync_order(
        self, alert_buffer: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Get alerts in sync order.

        Args:
            alert_buffer: List of buffered alerts.

        Returns:
            List of alerts in priority/timestamp order.
        """
        return self._sort_alerts(alert_buffer)

    def _sync_aggregated(
        self,
        alerts: List[Dict[str, Any]],
        result: SyncResult,
    ) -> tuple[int, int]:
        """Sync alerts with aggregation of similar types.

        Returns:
            Tuple of (synced_count, aggregated_count).
        """
        synced_count = 0
        aggregated_count = 0

        alerts_by_type: Dict[str, List[Dict[str, Any]]] = {}
        for alert in alerts:
            alert_type = alert.get("type", "unknown")
            if alert_type not in alerts_by_type:
                alerts_by_type[alert_type] = []
            alerts_by_type[alert_type].append(alert)

        for alert_type, type_alerts in alerts_by_type.items():
            if len(type_alerts) > 1:
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
                except Exception as e:  # pylint: disable=broad-exception-caught
                    result.errors.append(str(e))
            else:
                self._send_with_delay_notice(type_alerts[0], result)
                synced_count += 1

        return synced_count, aggregated_count

    def _sync_individual(
        self,
        alerts: List[Dict[str, Any]],
        result: SyncResult,
        cooldown_minutes: int,
        last_sent_by_type: Dict[str, datetime],
    ) -> tuple[int, int]:
        """Sync alerts individually with optional cooldown.

        Returns:
            Tuple of (synced_count, skipped_count).
        """
        synced_count = 0
        skipped_count = 0

        for alert in alerts:
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
                self._send_with_delay_notice(alert, result)
                synced_count += 1
                last_sent_by_type[alert_type] = datetime.fromisoformat(
                    alert.get(
                        "timestamp", datetime.now(timezone.utc).isoformat()
                    ).replace("Z", "+00:00")
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                result.errors.append(str(e))

        return synced_count, skipped_count

    def _send_with_delay_notice(
        self, alert: Dict[str, Any], _result: SyncResult
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

    def _sort_alerts(self, alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort alerts by priority (critical first) then newest first.

        Args:
            alerts: List of alert dicts.

        Returns:
            Sorted list of alerts.
        """
        return sorted(
            alerts,
            key=lambda a: (
                _get_priority_value(a),
                -datetime.fromisoformat(
                    a.get("timestamp", datetime.now(timezone.utc).isoformat()).replace(
                        "Z", "+00:00"
                    )
                ).timestamp(),
            ),
        )


def hash_reading(reading: Dict[str, Any]) -> str:
    """Create a hash of a sensor reading for deduplication.

    Args:
        reading: Sensor reading data.

    Returns:
        MD5 hex digest of the reading.
    """
    content = json.dumps(reading, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()


def _get_priority_value(alert: Dict[str, Any]) -> int:
    """Extract numeric priority value from an alert.

    Args:
        alert: Alert data dict.

    Returns:
        Integer priority value.
    """
    priority = alert.get("priority", SyncPriority.NORMAL)
    if isinstance(priority, int):
        return priority
    if hasattr(priority, "value"):
        return priority.value
    return 2
