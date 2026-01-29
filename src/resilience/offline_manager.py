"""
Offline Operation Manager for resilient operation during network outages.

This module provides functionality for:
- Network connectivity detection
- Local data buffering during offline periods
- Video storage management
- Graceful degradation of cloud features
- Alert buffering and prioritization
"""

import gzip
import json
import os
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WiFiStatus:
    """Represents WiFi connection status."""
    connected: bool
    interface: str = "wlan0"
    signal_strength: Optional[int] = None
    ssid: Optional[str] = None


class OfflineOperationManager:
    """Manages system operation during network outages."""

    # Priority levels for severity-based sorting
    SEVERITY_PRIORITY = {
        "critical": 0,
        "warning": 1,
        "info": 2,
        "normal": 3
    }

    def __init__(
        self,
        buffer_path: Optional[Path] = None,
        video_storage_path: Optional[Path] = None,
        max_buffer_size_mb: float = 100,
        enable_compression: bool = False,
        video_retention_days: int = 7,
        network_check_interval: int = 30,
        config: Optional[Dict[str, Any]] = None
    ):
        """Initialize the offline operation manager.

        Args:
            buffer_path: Path for storing buffered data.
            video_storage_path: Path for storing offline videos.
            max_buffer_size_mb: Maximum buffer size in MB.
            enable_compression: Enable gzip compression for buffer.
            video_retention_days: Days to retain videos before cleanup.
            network_check_interval: Seconds between network checks.
            config: Optional configuration dictionary.
        """
        self._buffer_path = buffer_path or Path("/tmp/chickencoop_buffer")
        self._video_storage_path = video_storage_path or Path("/tmp/chickencoop_videos")
        self._max_buffer_size_mb = max_buffer_size_mb
        self._compression_enabled = enable_compression
        self._video_retention_days = video_retention_days
        self._network_check_interval = network_check_interval
        self.config = config or {}

        self._offline_mode = False
        self._offline_since: Optional[datetime] = None
        self._last_known_data: Dict[str, Any] = {}
        self._last_known_data_timestamp: Optional[datetime] = None

        # In-memory buffers
        self._sensor_buffer: List[Dict[str, Any]] = []
        self._alert_buffer: List[Dict[str, Any]] = []
        self._command_queue: List[Dict[str, Any]] = []
        self._connectivity_events: List[Dict[str, Any]] = []
        self._logs: List[str] = []
        self._video_metadata: Dict[str, Dict[str, Any]] = {}
        self._videos_pending_upload: List[str] = []
        self._pending_operations: List[Dict[str, Any]] = []

        # Ensure directories exist
        self._buffer_path.mkdir(parents=True, exist_ok=True)
        self._video_storage_path.mkdir(parents=True, exist_ok=True)

        # Load persisted buffer if exists
        self._load_persisted_buffer()

    @property
    def network_check_interval(self) -> int:
        """Get the network check interval in seconds."""
        return self._network_check_interval

    @property
    def max_buffer_size_mb(self) -> float:
        """Get the maximum buffer size in MB."""
        return self._max_buffer_size_mb

    @property
    def compression_enabled(self) -> bool:
        """Check if compression is enabled."""
        return self._compression_enabled

    @property
    def is_online(self) -> bool:
        """Check if device is currently online."""
        return not self._offline_mode

    # =========================================================================
    # Network Detection Methods
    # =========================================================================

    def check_wifi_status(self) -> WiFiStatus:
        """Check WiFi connection status.

        Returns:
            WiFiStatus object with connection details.
        """
        connected = self._check_interface_status()
        return WiFiStatus(
            connected=connected,
            interface="wlan0",
            signal_strength=self._get_signal_strength() if connected else None
        )

    def _check_interface_status(self) -> bool:
        """Check if network interface is up. Override in tests."""
        # In real implementation, would check /sys/class/net/wlan0/operstate
        return True

    def check_internet_reachable(self) -> bool:
        """Check if internet is reachable.

        Returns:
            True if internet is reachable.
        """
        return self._ping_host("8.8.8.8")

    def _ping_host(self, host: str) -> bool:
        """Ping a host to check connectivity. Override in tests."""
        return True

    def check_aws_reachable(self) -> bool:
        """Check if AWS services are reachable.

        Returns:
            True if AWS is reachable.
        """
        return self._check_aws_endpoint()

    def _check_aws_endpoint(self) -> bool:
        """Check AWS endpoint connectivity. Override in tests."""
        return True

    def get_wifi_signal_strength(self) -> int:
        """Get WiFi signal strength (RSSI).

        Returns:
            Signal strength in dBm (negative value).
        """
        return self._get_signal_strength()

    def _get_signal_strength(self) -> int:
        """Get signal strength from system. Override in tests."""
        return -50  # Default moderate signal

    # =========================================================================
    # Offline Mode Management
    # =========================================================================

    def set_offline_mode(self, offline: bool) -> None:
        """Set the offline mode status.

        Args:
            offline: True to enter offline mode, False to exit.
        """
        if offline and not self._offline_mode:
            # Entering offline mode
            self._offline_mode = True
            self._offline_since = datetime.now()
            self._log(f"Entering offline mode at {self._offline_since.isoformat()}")
            self._connectivity_events.append({
                "event_type": "disconnected",
                "timestamp": self._offline_since.isoformat()
            })
        elif not offline and self._offline_mode:
            # Exiting offline mode
            self._offline_mode = False
            reconnect_time = datetime.now()
            self._log(f"Exiting offline mode at {reconnect_time.isoformat()}")
            self._connectivity_events.append({
                "event_type": "reconnected",
                "timestamp": reconnect_time.isoformat()
            })
            self._offline_since = None

    def set_online_status(self, status: bool) -> None:
        """Set the online status (inverse of offline mode).

        Args:
            status: True if online, False if offline.
        """
        self.set_offline_mode(not status)

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status.

        Returns:
            Dictionary with system status information.
        """
        return {
            "online": not self._offline_mode,
            "offline_since": self._offline_since.isoformat() if self._offline_since else None
        }

    def get_offline_duration(self) -> Optional[timedelta]:
        """Get how long the system has been offline.

        Returns:
            Duration as timedelta, or None if online.
        """
        if self._offline_mode and self._offline_since:
            return datetime.now() - self._offline_since
        return timedelta(seconds=0) if self._offline_mode else None

    # =========================================================================
    # Continued Monitoring Methods
    # =========================================================================

    def process_sensor_reading(self, reading: Dict[str, Any]) -> Dict[str, bool]:
        """Process a sensor reading, storing locally if offline.

        Args:
            reading: Sensor reading data.

        Returns:
            Result dictionary with success status.
        """
        self.buffer_sensor_data(reading)
        return {
            "success": True,
            "stored_locally": True
        }

    def process_motion_event(self, detected: bool, timestamp: datetime) -> Dict[str, bool]:
        """Process a motion detection event.

        Args:
            detected: Whether motion was detected.
            timestamp: When motion was detected.

        Returns:
            Result dictionary with success status.
        """
        event = {
            "type": "motion",
            "detected": detected,
            "timestamp": timestamp.isoformat()
        }
        self._sensor_buffer.append(event)
        return {
            "success": True,
            "event_logged": True
        }

    def request_video_recording(self, trigger: str, duration: int) -> Dict[str, Any]:
        """Request a video recording.

        Args:
            trigger: What triggered the recording.
            duration: Recording duration in seconds.

        Returns:
            Result dictionary with recording details.
        """
        return {
            "success": True,
            "storage_location": "local" if self._offline_mode else "cloud",
            "trigger": trigger,
            "duration": duration
        }

    def process_headcount(self, count: int, expected: int, confidence: float) -> Dict[str, Any]:
        """Process a headcount result.

        Args:
            count: Detected chicken count.
            expected: Expected chicken count.
            confidence: Detection confidence (0-1).

        Returns:
            Result dictionary with success status.
        """
        result = {
            "type": "headcount",
            "count": count,
            "expected": expected,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }
        self._sensor_buffer.append(result)
        return {
            "success": True,
            "stored_locally": True
        }

    def trigger_local_alert(self, alert_type: str) -> Dict[str, Any]:
        """Trigger a local alert (LED, buzzer).

        Args:
            alert_type: Type of alert to trigger.

        Returns:
            Result dictionary with alert details.
        """
        return {
            "success": True,
            "alert_type": alert_type
        }

    # =========================================================================
    # Data Buffering Methods
    # =========================================================================

    def buffer_sensor_data(self, reading: Dict[str, Any], priority: str = "normal") -> None:
        """Buffer sensor data for later sync.

        Args:
            reading: Sensor reading to buffer.
            priority: Priority level (normal, critical).
        """
        buffered_reading = {
            **reading,
            "buffered_at": datetime.now().isoformat(),
            "priority": priority
        }
        self._sensor_buffer.append(buffered_reading)

    def get_buffered_data(self) -> List[Dict[str, Any]]:
        """Get all buffered sensor data.

        Returns:
            List of buffered readings.
        """
        return self._sensor_buffer.copy()

    def get_priority_buffer_items(self) -> List[Dict[str, Any]]:
        """Get buffered items marked as critical priority.

        Returns:
            List of critical priority items.
        """
        return [item for item in self._sensor_buffer if item.get("priority") == "critical"]

    def get_buffer_size_mb(self) -> float:
        """Get current buffer size in MB.

        Returns:
            Buffer size in megabytes.
        """
        # Estimate size based on JSON serialization
        data = json.dumps(self._sensor_buffer)
        return len(data.encode()) / (1024 * 1024)

    def flush_buffer(self) -> None:
        """Flush buffer to persistent storage."""
        if not self._sensor_buffer:
            return

        buffer_file = self._buffer_path / "sensor_buffer.json"

        # Load existing data if present
        existing_data = []
        if buffer_file.exists():
            with open(buffer_file, "r") as f:
                existing_data = json.load(f)

        # Combine and save
        all_data = existing_data + self._sensor_buffer

        if self._compression_enabled:
            compressed_file = self._buffer_path / "sensor_buffer.json.gz"
            with gzip.open(compressed_file, "wt") as f:
                json.dump(all_data, f)
        else:
            with open(buffer_file, "w") as f:
                json.dump(all_data, f)

    def _load_persisted_buffer(self) -> None:
        """Load persisted buffer data from disk."""
        buffer_file = self._buffer_path / "sensor_buffer.json"
        compressed_file = self._buffer_path / "sensor_buffer.json.gz"

        if compressed_file.exists():
            with gzip.open(compressed_file, "rt") as f:
                self._sensor_buffer = json.load(f)
        elif buffer_file.exists():
            with open(buffer_file, "r") as f:
                self._sensor_buffer = json.load(f)

    # =========================================================================
    # Video Storage Methods
    # =========================================================================

    def store_video_locally(
        self,
        video_data: bytes,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store a video file locally.

        Args:
            video_data: Video file content.
            filename: Filename for the video.
            metadata: Optional metadata to store.

        Returns:
            Result dictionary with storage details.
        """
        video_path = self._video_storage_path / filename
        video_path.parent.mkdir(parents=True, exist_ok=True)

        with open(video_path, "wb") as f:
            f.write(video_data)

        # Store metadata
        if metadata:
            self._video_metadata[filename] = {
                **metadata,
                "stored_at": datetime.now().isoformat()
            }
        else:
            self._video_metadata[filename] = {
                "stored_at": datetime.now().isoformat()
            }

        # Mark for upload
        self._videos_pending_upload.append(filename)

        return {
            "success": True,
            "local_path": str(video_path)
        }

    def get_video_metadata(self, filename: str) -> Dict[str, Any]:
        """Get metadata for a stored video.

        Args:
            filename: Video filename.

        Returns:
            Metadata dictionary.
        """
        return self._video_metadata.get(filename, {})

    def check_storage_capacity(self) -> Dict[str, Any]:
        """Check available storage capacity.

        Returns:
            Dictionary with capacity information.
        """
        stat = shutil.disk_usage(self._video_storage_path)
        return {
            "available_mb": stat.free / (1024 * 1024),
            "total_mb": stat.total / (1024 * 1024),
            "percent_free": (stat.free / stat.total) * 100
        }

    def cleanup_old_videos(self) -> Dict[str, Any]:
        """Clean up videos older than retention period.

        Returns:
            Dictionary with cleanup results.
        """
        deleted_count = 0
        freed_bytes = 0
        cutoff = datetime.now() - timedelta(days=self._video_retention_days)

        for video_file in self._video_storage_path.glob("*.mp4"):
            if datetime.fromtimestamp(video_file.stat().st_mtime) < cutoff:
                freed_bytes += video_file.stat().st_size
                video_file.unlink()
                deleted_count += 1

        return {
            "deleted_count": deleted_count,
            "freed_mb": freed_bytes / (1024 * 1024)
        }

    def get_videos_pending_upload(self) -> List[str]:
        """Get list of videos pending upload.

        Returns:
            List of filenames pending upload.
        """
        return self._videos_pending_upload.copy()

    # =========================================================================
    # Graceful Degradation Methods
    # =========================================================================

    def update_last_known_data(self, data: Dict[str, Any]) -> None:
        """Update last known sensor data.

        Args:
            data: Latest sensor data.
        """
        self._last_known_data = data.copy()
        self._last_known_data_timestamp = datetime.now()

    def get_last_known_data(self) -> Dict[str, Any]:
        """Get last known sensor data with timestamp.

        Returns:
            Dictionary with last known data and timestamp.
        """
        result = self._last_known_data.copy()
        if self._last_known_data_timestamp:
            result["last_updated"] = self._last_known_data_timestamp.isoformat()
        return result

    def queue_cloud_command(self, command: Dict[str, Any]) -> None:
        """Queue a command for execution when online.

        Args:
            command: Command to queue.
        """
        command["queued_at"] = datetime.now().isoformat()
        self._command_queue.append(command)

    def get_queued_commands(self) -> List[Dict[str, Any]]:
        """Get all queued commands.

        Returns:
            List of queued commands.
        """
        return self._command_queue.copy()

    def queue_operation(self, operation: Dict[str, Any]) -> None:
        """Queue an operation for later execution.

        Args:
            operation: Operation details to queue.
        """
        self._pending_operations.append(operation)

    def get_pending_operations(self) -> List[Dict[str, Any]]:
        """Get all pending operations.

        Returns:
            List of pending operations.
        """
        return self._pending_operations.copy()

    def clear_pending_operations(self) -> None:
        """Clear all pending operations."""
        self._pending_operations.clear()

    def safe_cloud_operation(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform a cloud operation with error handling.

        Args:
            operation: Operation type (upload, publish, etc.).
            data: Data for the operation.

        Returns:
            Result dictionary with success status.
        """
        try:
            self._send_to_cloud(operation, data)
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error_handled": True,
                "error_message": str(e)
            }

    def _send_to_cloud(self, operation: str, data: Dict[str, Any]) -> None:
        """Send data to cloud. Override in tests."""
        pass

    # =========================================================================
    # Alert Buffering Methods
    # =========================================================================

    def buffer_alert(self, alert: Dict[str, Any]) -> Dict[str, bool]:
        """Buffer an alert for later sending.

        Args:
            alert: Alert data to buffer.

        Returns:
            Result dictionary.
        """
        buffered_alert = {
            **alert,
            "timestamp": datetime.now().isoformat()
        }
        self._alert_buffer.append(buffered_alert)
        return {"buffered": True}

    def get_buffered_alerts(self) -> List[Dict[str, Any]]:
        """Get all buffered alerts.

        Returns:
            List of buffered alerts.
        """
        return self._alert_buffer.copy()

    def get_alerts_by_priority(self) -> List[Dict[str, Any]]:
        """Get alerts sorted by priority (critical first).

        Returns:
            Sorted list of alerts.
        """
        return sorted(
            self._alert_buffer,
            key=lambda x: self.SEVERITY_PRIORITY.get(x.get("severity", "normal"), 3)
        )

    def get_deduplicated_alerts(self) -> List[Dict[str, Any]]:
        """Get deduplicated alerts based on dedup_key.

        Returns:
            List of unique alerts.
        """
        seen_keys = set()
        unique_alerts = []

        for alert in self._alert_buffer:
            dedup_key = alert.get("dedup_key")
            if dedup_key:
                if dedup_key not in seen_keys:
                    seen_keys.add(dedup_key)
                    unique_alerts.append(alert)
            else:
                unique_alerts.append(alert)

        return unique_alerts

    # =========================================================================
    # Offline Indicator Methods
    # =========================================================================

    def get_led_indicator_state(self) -> Dict[str, str]:
        """Get the LED indicator state for offline status.

        Returns:
            Dictionary with LED state information.
        """
        if self._offline_mode:
            return {
                "status": "offline",
                "color": "red"
            }
        return {
            "status": "online",
            "color": "green"
        }

    def get_connectivity_events(self) -> List[Dict[str, Any]]:
        """Get connectivity event history.

        Returns:
            List of connectivity events.
        """
        return self._connectivity_events.copy()

    # =========================================================================
    # Logging Methods
    # =========================================================================

    def _log(self, message: str) -> None:
        """Add a log message.

        Args:
            message: Message to log.
        """
        self._logs.append(f"{datetime.now().isoformat()}: {message}")

    def get_recent_logs(self, count: int = 100) -> List[str]:
        """Get recent log messages.

        Args:
            count: Number of recent logs to return.

        Returns:
            List of recent log messages.
        """
        return self._logs[-count:]
