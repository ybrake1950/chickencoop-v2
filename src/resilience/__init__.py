"""Resilience module for offline operation and connectivity management."""

from src.resilience.offline_manager import OfflineOperationManager, WiFiStatus
from src.resilience.data_sync import (
    DataSyncManager,
    SyncStatus,
    SyncPriority,
    SyncItem,
    SyncResult,
    SyncCheckpoint,
)
from src.resilience.connection_retry import (
    AWSReconnectionHandler,
    BackoffConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    ConnectionPool,
    ConnectionRetryManager,
    ExponentialBackoff,
    OutageRecord,
    PartialUploadTracker,
    RecoveryTracker,
    ServiceDegradationHandler,
    TimeoutConfig,
    WiFiReconnectionHandler,
    make_idempotent,
)

__all__ = [
    "OfflineOperationManager",
    "WiFiStatus",
    "DataSyncManager",
    "SyncStatus",
    "SyncPriority",
    "SyncItem",
    "SyncResult",
    "SyncCheckpoint",
    "AWSReconnectionHandler",
    "BackoffConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "ConnectionPool",
    "ConnectionRetryManager",
    "ExponentialBackoff",
    "OutageRecord",
    "PartialUploadTracker",
    "RecoveryTracker",
    "ServiceDegradationHandler",
    "TimeoutConfig",
    "WiFiReconnectionHandler",
    "make_idempotent",
]
