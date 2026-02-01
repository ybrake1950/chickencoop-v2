"""
Connection Retry and Recovery Module.

This module provides resilient connection handling for the ChickenCoop application,
including exponential backoff, circuit breaker pattern, connection pooling,
and graceful service degradation.
"""

import logging
import random
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class BackoffConfig:
    """Configuration for exponential backoff."""

    initial_delay: float = 1.0
    multiplier: float = 2.0
    max_delay: float = 300.0  # 5 minutes
    max_attempts: int = 10
    jitter: bool = True
    jitter_factor: float = 0.1


class ExponentialBackoff:
    """
    Implements exponential backoff with optional jitter.

    Each service can have independent backoff state to prevent
    one failing service from affecting retry timing of others.
    """

    def __init__(self, config: Optional[BackoffConfig] = None):
        """
        Initialize exponential backoff.

        Args:
            config: Backoff configuration. Uses defaults if not provided.
        """
        self.config = config or BackoffConfig()
        self._attempt = 0
        self._lock = threading.Lock()

    @property
    def attempt(self) -> int:
        """Current attempt number."""
        return self._attempt

    def get_next_delay(self) -> float:
        """
        Calculate the next delay with exponential backoff and optional jitter.

        Returns:
            Delay in seconds before next retry attempt.
        """
        with self._lock:
            if self._attempt == 0:
                # First retry is immediate or very short
                delay = 0.0
            else:
                # Exponential backoff: initial * multiplier^(attempt-1)
                delay = self.config.initial_delay * (
                    self.config.multiplier ** (self._attempt - 1)
                )

            # Apply maximum cap
            delay = min(delay, self.config.max_delay)

            # Add jitter to prevent thundering herd
            if self.config.jitter and delay > 0:
                jitter_range = delay * self.config.jitter_factor
                delay += random.uniform(-jitter_range, jitter_range)
                delay = max(0, delay)

            self._attempt += 1
            return delay

    def reset(self) -> None:
        """Reset backoff state after successful connection."""
        with self._lock:
            self._attempt = 0

    def should_retry(self) -> bool:
        """Check if more retry attempts are allowed."""
        return self._attempt < self.config.max_attempts

    def get_current_delay(self) -> float:
        """Get current delay without incrementing attempt counter."""
        if self._attempt == 0:
            return 0.0
        delay = self.config.initial_delay * (
            self.config.multiplier ** (self._attempt - 1)
        )
        return min(delay, self.config.max_delay)


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 1


class CircuitBreaker:
    """
    Implements the circuit breaker pattern for failing services.

    States:
    - CLOSED: Normal operation, requests go through
    - OPEN: Service is failing, requests fail fast without trying
    - HALF_OPEN: Testing if service recovered, allows limited requests
    """

    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[
            Callable[[str, CircuitState, CircuitState], None]
        ] = None,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Name of the service this circuit breaker protects.
            config: Circuit breaker configuration.
            on_state_change: Callback when state changes (name, old_state, new_state).
        """
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.Lock()
        self._on_state_change = on_state_change

    @property
    def state(self) -> CircuitState:
        """Current circuit state."""
        with self._lock:
            self._check_recovery_timeout()
            return self._state

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    def _check_recovery_timeout(self) -> None:
        """Check if open circuit should transition to half-open."""
        if self._state == CircuitState.OPEN and self._last_failure_time:
            elapsed = (
                datetime.now(timezone.utc) - self._last_failure_time
            ).total_seconds()
            if elapsed >= self.config.recovery_timeout:
                self._transition_to(CircuitState.HALF_OPEN)

    def _transition_to(self, new_state: CircuitState) -> None:
        """Transition to new state and log the change."""
        old_state = self._state
        if old_state != new_state:
            self._state = new_state
            logger.info(
                "Circuit breaker '%s' state change: %s -> %s",
                self.name,
                old_state.value,
                new_state.value,
            )
            if self._on_state_change:
                self._on_state_change(self.name, old_state, new_state)

            if new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0

    def can_execute(self) -> bool:
        """
        Check if a request can be executed.

        Returns:
            True if request should proceed, False if should fail fast.
        """
        with self._lock:
            self._check_recovery_timeout()

            if self._state == CircuitState.CLOSED:
                return True
            elif self._state == CircuitState.OPEN:
                return False
            else:  # HALF_OPEN
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

    def record_success(self) -> None:
        """Record a successful request."""
        with self._lock:
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.CLOSED)

    def record_failure(self) -> None:
        """Record a failed request."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now(timezone.utc)

            if self._state == CircuitState.HALF_OPEN:
                self._transition_to(CircuitState.OPEN)
            elif self._failure_count >= self.config.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def reset(self) -> None:
        """Reset circuit breaker to closed state."""
        with self._lock:
            self._failure_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
            self._transition_to(CircuitState.CLOSED)


@dataclass
class TimeoutConfig:
    """Configuration for connection timeouts."""

    connect_timeout: float = 10.0
    read_timeout: float = 30.0
    write_timeout: float = 30.0
    total_timeout: float = 60.0


class ConnectionPool:
    """
    Manages HTTP connection pooling and reuse.

    Tracks connections, detects stale connections, and handles
    network interface changes.
    """

    def __init__(self, max_size: int = 10, max_age: float = 300.0):
        """
        Initialize connection pool.

        Args:
            max_size: Maximum number of connections in pool.
            max_age: Maximum age of a connection in seconds before refresh.
        """
        self.max_size = max_size
        self.max_age = max_age
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    @property
    def size(self) -> int:
        """Current number of connections in pool."""
        return len(self._connections)

    def get_connection(self, key: str) -> Optional[Any]:
        """
        Get a connection from the pool.

        Args:
            key: Connection identifier (e.g., host:port).

        Returns:
            Connection object if available and not stale, None otherwise.
        """
        with self._lock:
            if key in self._connections:
                conn_info = self._connections[key]
                age = (
                    datetime.now(timezone.utc) - conn_info["created"]
                ).total_seconds()
                if age < self.max_age:
                    conn_info["last_used"] = datetime.now(timezone.utc)
                    return conn_info["connection"]
                else:
                    # Connection is stale, remove it
                    del self._connections[key]
            return None

    def put_connection(self, key: str, connection: Any) -> bool:
        """
        Add a connection to the pool.

        Args:
            key: Connection identifier.
            connection: Connection object to pool.

        Returns:
            True if connection was added, False if pool is full.
        """
        with self._lock:
            if len(self._connections) >= self.max_size and key not in self._connections:
                # Remove oldest connection
                if self._connections:
                    oldest_key = min(
                        self._connections.keys(),
                        key=lambda k: self._connections[k]["last_used"],
                    )
                    del self._connections[oldest_key]

            self._connections[key] = {
                "connection": connection,
                "created": datetime.now(timezone.utc),
                "last_used": datetime.now(timezone.utc),
            }
            return True

    def remove_connection(self, key: str) -> bool:
        """Remove a connection from the pool."""
        with self._lock:
            if key in self._connections:
                del self._connections[key]
                return True
            return False

    def refresh_stale(self) -> int:
        """
        Remove stale connections from the pool.

        Returns:
            Number of connections removed.
        """
        with self._lock:
            now = datetime.now(timezone.utc)
            stale_keys = [
                key
                for key, info in self._connections.items()
                if (now - info["created"]).total_seconds() >= self.max_age
            ]
            for key in stale_keys:
                del self._connections[key]
            return len(stale_keys)

    def clear(self) -> None:
        """Clear all connections (e.g., on network change)."""
        with self._lock:
            self._connections.clear()

    def handle_network_change(self) -> None:
        """Handle network interface changes by clearing stale connections."""
        self.clear()


@dataclass
class OutageRecord:
    """Record of a service outage."""

    service: str
    start_time: datetime
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[timedelta]:
        """Duration of the outage."""
        if self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def is_active(self) -> bool:
        """Whether the outage is still ongoing."""
        return self.end_time is None


class RecoveryTracker:
    """
    Tracks connection recovery and outage statistics.

    Records outage durations, recovery events, and generates
    recovery summaries.
    """

    def __init__(self):
        """Initialize recovery tracker."""
        self._outages: List[OutageRecord] = []
        self._lock = threading.Lock()
        self._recovery_callbacks: List[Callable[[str], None]] = []

    def record_outage_start(self, service: str) -> None:
        """Record the start of an outage."""
        with self._lock:
            # Check if there's already an active outage for this service
            for outage in self._outages:
                if outage.service == service and outage.is_active:
                    return  # Already tracking this outage

            outage = OutageRecord(
                service=service, start_time=datetime.now(timezone.utc)
            )
            self._outages.append(outage)
            logger.warning("Outage started for service: %s", service)

    def record_recovery(self, service: str) -> Optional[timedelta]:
        """
        Record recovery from an outage.

        Args:
            service: Name of the recovered service.

        Returns:
            Duration of the outage, or None if no active outage.
        """
        with self._lock:
            for outage in self._outages:
                if outage.service == service and outage.is_active:
                    outage.end_time = datetime.now(timezone.utc)
                    duration = outage.duration
                    logger.info(
                        "Connection restored for %s. Outage duration: %s",
                        service,
                        duration,
                    )

                    # Notify callbacks
                    for callback in self._recovery_callbacks:
                        try:
                            callback(service)
                        except Exception as e:  # pylint: disable=broad-exception-caught
                            logger.error("Recovery callback error: %s", e)

                    return duration
            return None

    def get_outage_duration(self, service: str) -> Optional[timedelta]:
        """Get the total outage duration for a service."""
        with self._lock:
            total = timedelta()
            for outage in self._outages:
                if outage.service == service and outage.duration:
                    total += outage.duration
            return total if total > timedelta() else None

    def get_active_outages(self) -> List[str]:
        """Get list of services currently experiencing outages."""
        with self._lock:
            return [o.service for o in self._outages if o.is_active]

    def get_recovery_summary(self) -> Dict[str, Any]:
        """Generate a summary of recent recovery activity."""
        with self._lock:
            summary = {
                "total_outages": len(self._outages),
                "active_outages": len([o for o in self._outages if o.is_active]),
                "recovered_outages": len([o for o in self._outages if not o.is_active]),
                "services": {},
            }

            services: Dict[str, Dict[str, Any]] = {}
            for outage in self._outages:
                if outage.service not in services:
                    services[outage.service] = {
                        "outage_count": 0,
                        "total_duration": timedelta(),
                        "is_active": False,
                    }

                svc = services[outage.service]
                svc["outage_count"] += 1
                if outage.duration:
                    svc["total_duration"] += outage.duration
                if outage.is_active:
                    svc["is_active"] = True

            summary["services"] = services

            return summary

    def add_recovery_callback(self, callback: Callable[[str], None]) -> None:
        """Add a callback to be invoked on recovery."""
        self._recovery_callbacks.append(callback)


class ServiceDegradationHandler:
    """
    Handles graceful service degradation when cloud services fail.

    Ensures local operations continue even when S3, IoT, or SNS are unavailable.
    """

    def __init__(self):
        """Initialize degradation handler."""
        self._degraded_services: Dict[str, bool] = {}
        self._buffered_alerts: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._local_operation_enabled = True

    def mark_degraded(self, service: str) -> None:
        """Mark a service as degraded."""
        with self._lock:
            self._degraded_services[service] = True
            logger.warning("Service %s marked as degraded", service)

    def mark_healthy(self, service: str) -> None:
        """Mark a service as healthy."""
        with self._lock:
            self._degraded_services[service] = False
            logger.info("Service %s marked as healthy", service)

    def is_degraded(self, service: str) -> bool:
        """Check if a service is degraded."""
        return self._degraded_services.get(service, False)

    def can_operate_locally(self) -> bool:
        """Check if local operations should continue."""
        return self._local_operation_enabled

    def buffer_alert(self, alert: Dict[str, Any]) -> None:
        """Buffer an alert for later delivery when SNS recovers."""
        with self._lock:
            self._buffered_alerts.append(
                {**alert, "buffered_at": datetime.now(timezone.utc).isoformat()}
            )
            logger.info(
                "Alert buffered for later delivery. Buffer size: %s",
                len(self._buffered_alerts),
            )

    def get_buffered_alerts(self) -> List[Dict[str, Any]]:
        """Get all buffered alerts."""
        with self._lock:
            return list(self._buffered_alerts)

    def clear_buffered_alerts(self) -> int:
        """Clear buffered alerts after successful delivery."""
        with self._lock:
            count = len(self._buffered_alerts)
            self._buffered_alerts.clear()
            return count

    def all_services_down(self) -> bool:
        """Check if all tracked services are down."""
        with self._lock:
            if not self._degraded_services:
                return False
            return all(self._degraded_services.values())


class WiFiReconnectionHandler:
    """
    Handles WiFi reconnection with exponential backoff and multi-SSID support.
    """

    def __init__(
        self,
        ssids: Optional[List[str]] = None,
        backoff_config: Optional[BackoffConfig] = None,
    ):
        """
        Initialize WiFi reconnection handler.

        Args:
            ssids: List of SSIDs to try, in priority order.
            backoff_config: Backoff configuration for retries.
        """
        self.ssids = ssids or []
        self.backoff = ExponentialBackoff(
            backoff_config
            or BackoffConfig(
                initial_delay=5.0,
                multiplier=2.0,
                max_delay=300.0,  # 5 minutes max
                max_attempts=100,  # Keep trying for a long time
            )
        )
        self._connected = False
        self._current_ssid: Optional[str] = None
        self._lock = threading.Lock()
        self._auto_reconnect = True

    @property
    def is_connected(self) -> bool:
        """Check if WiFi is connected."""
        return self._connected

    @property
    def current_ssid(self) -> Optional[str]:
        """Get currently connected SSID."""
        return self._current_ssid

    def set_connected(self, connected: bool, ssid: Optional[str] = None) -> None:
        """Update connection status."""
        with self._lock:
            was_connected = self._connected
            self._connected = connected
            self._current_ssid = ssid if connected else None

            if connected and not was_connected:
                self.backoff.reset()
                logger.info("WiFi connected to %s", ssid)
            elif not connected and was_connected:
                logger.warning("WiFi disconnected")

    def should_auto_reconnect(self) -> bool:
        """Check if auto-reconnect is enabled."""
        return self._auto_reconnect and not self._connected

    def get_reconnect_delay(self) -> float:
        """Get delay before next reconnection attempt."""
        return self.backoff.get_next_delay()

    def get_next_ssid(self) -> Optional[str]:
        """Get next SSID to try for fallback."""
        if not self.ssids:
            return None

        if self._current_ssid and self._current_ssid in self.ssids:
            current_idx = self.ssids.index(self._current_ssid)
            next_idx = (current_idx + 1) % len(self.ssids)
            return self.ssids[next_idx]

        return self.ssids[0]

    def attempt_reconnect(self, connect_func: Callable[[str], bool]) -> bool:
        """
        Attempt to reconnect to WiFi.

        Args:
            connect_func: Function that attempts connection to given SSID.

        Returns:
            True if reconnection succeeded.
        """
        for ssid in self.ssids or ([self._current_ssid] if self._current_ssid else []):
            if ssid and connect_func(ssid):
                self.set_connected(True, ssid)
                return True
        return False


class AWSReconnectionHandler:
    """
    Handles AWS service reconnection with per-service circuit breakers.
    """

    def __init__(self, region: str = "us-east-1"):
        """
        Initialize AWS reconnection handler.

        Args:
            region: Primary AWS region.
        """
        self.region = region
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._backoffs: Dict[str, ExponentialBackoff] = {}
        self._lock = threading.Lock()

    def get_circuit_breaker(self, service: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        with self._lock:
            if service not in self._circuit_breakers:
                self._circuit_breakers[service] = CircuitBreaker(service)
            return self._circuit_breakers[service]

    def get_backoff(self, service: str) -> ExponentialBackoff:
        """Get or create backoff for a service."""
        with self._lock:
            if service not in self._backoffs:
                self._backoffs[service] = ExponentialBackoff()
            return self._backoffs[service]

    def can_attempt(self, service: str) -> bool:
        """Check if a connection attempt should be made."""
        cb = self.get_circuit_breaker(service)
        backoff = self.get_backoff(service)
        return cb.can_execute() and backoff.should_retry()

    def record_success(self, service: str) -> None:
        """Record successful connection."""
        self.get_circuit_breaker(service).record_success()
        self.get_backoff(service).reset()

    def record_failure(self, service: str) -> None:
        """Record failed connection."""
        self.get_circuit_breaker(service).record_failure()

    def get_retry_delay(self, service: str) -> float:
        """Get delay before next retry for a service."""
        return self.get_backoff(service).get_next_delay()

    def should_refresh_credentials(self) -> bool:
        """Check if AWS credentials should be refreshed."""
        # Placeholder - in real implementation would check credential expiry
        return False


class ConnectionRetryManager:
    """
    Central manager for connection retry logic across all services.

    Coordinates WiFi reconnection, AWS service recovery, circuit breakers,
    connection pooling, and service degradation.
    """

    def __init__(
        self,
        wifi_handler: Optional[WiFiReconnectionHandler] = None,
        aws_handler: Optional[AWSReconnectionHandler] = None,
    ):
        """
        Initialize connection retry manager.

        Args:
            wifi_handler: WiFi reconnection handler.
            aws_handler: AWS reconnection handler.
        """
        self.wifi = wifi_handler or WiFiReconnectionHandler()
        self.aws = aws_handler or AWSReconnectionHandler()
        self.connection_pool = ConnectionPool()
        self.degradation = ServiceDegradationHandler()
        self.recovery_tracker = RecoveryTracker()
        self.timeout_config = TimeoutConfig()
        self._lock = threading.Lock()

    def execute_with_retry(
        self,
        service: str,
        operation: Callable[[], T],
        max_retries: Optional[int] = None,
    ) -> Optional[T]:
        """
        Execute an operation with retry logic.

        Args:
            service: Name of the service (e.g., "s3", "iot", "sns").
            operation: Callable to execute.
            max_retries: Maximum retry attempts (overrides default).

        Returns:
            Operation result, or None if all retries failed.
        """
        cb = self.aws.get_circuit_breaker(service)
        backoff = self.aws.get_backoff(service)

        if max_retries:
            backoff.config.max_attempts = max_retries

        while backoff.should_retry():
            if not cb.can_execute():
                logger.debug("Circuit open for %s, failing fast", service)
                return None

            try:
                result = operation()
                cb.record_success()
                backoff.reset()
                self.degradation.mark_healthy(service)
                self.recovery_tracker.record_recovery(service)
                return result
            except Exception as e:  # pylint: disable=broad-exception-caught
                cb.record_failure()
                backoff.get_next_delay()
                logger.warning("Operation failed for %s: %s", service, e)

                if not backoff.should_retry():
                    self.degradation.mark_degraded(service)
                    self.recovery_tracker.record_outage_start(service)

        return None

    def is_service_available(self, service: str) -> bool:
        """Check if a service is currently available."""
        cb = self.aws.get_circuit_breaker(service)
        return not cb.is_open and not self.degradation.is_degraded(service)

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all tracked services."""
        return {
            "wifi_connected": self.wifi.is_connected,
            "degraded_services": [
                s
                for s, d in self.degradation._degraded_services.items()  # pylint: disable=protected-access
                if d
            ],
            "active_outages": self.recovery_tracker.get_active_outages(),
            "connection_pool_size": self.connection_pool.size,
        }


class PartialUploadTracker:
    """Tracks partial uploads for resumable operations."""

    def __init__(self):
        """Initialize partial upload tracker."""
        self._uploads: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start_upload(self, upload_id: str, total_size: int) -> None:
        """Record start of an upload."""
        with self._lock:
            self._uploads[upload_id] = {
                "total_size": total_size,
                "uploaded_bytes": 0,
                "parts": [],
                "started_at": datetime.now(timezone.utc),
            }

    def record_part(self, upload_id: str, part_number: int, size: int) -> None:
        """Record a successfully uploaded part."""
        with self._lock:
            if upload_id in self._uploads:
                self._uploads[upload_id]["parts"].append(part_number)
                self._uploads[upload_id]["uploaded_bytes"] += size

    def get_resume_point(self, upload_id: str) -> Optional[int]:
        """Get the byte offset to resume from."""
        with self._lock:
            if upload_id in self._uploads:
                return self._uploads[upload_id]["uploaded_bytes"]
            return None

    def is_resumable(self, upload_id: str) -> bool:
        """Check if an upload can be resumed."""
        with self._lock:
            return upload_id in self._uploads

    def complete_upload(self, upload_id: str) -> None:
        """Mark an upload as complete."""
        with self._lock:
            if upload_id in self._uploads:
                del self._uploads[upload_id]


def make_idempotent(operation_id: str) -> Callable:
    """
    Decorator to make operations idempotent using operation IDs.

    Args:
        operation_id: Unique identifier for the operation.
    """
    _completed_operations: Dict[str, Any] = {}

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args, **kwargs) -> T:
            if operation_id in _completed_operations:
                return _completed_operations[operation_id]

            result = func(*args, **kwargs)
            _completed_operations[operation_id] = result
            return result

        return wrapper

    return decorator
