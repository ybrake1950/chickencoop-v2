"""Command queue with FIFO ordering, deduplication, expiration, and security.

Provides a persistent command queue that supports idempotency keys for
deduplication, TTL-based expiration, and role-based access control.
"""

import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CommandStatus(Enum):
    """Status of a command in the queue."""

    PENDING = "pending"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass
class Command:
    """A command to be enqueued and processed."""

    action: str
    params: Optional[Dict[str, Any]]
    user_id: Optional[str]
    idempotency_key: Optional[str] = None
    ttl_seconds: Optional[int] = None
    user_role: Optional[str] = None
    created_at: float = field(default_factory=time.time)


@dataclass
class EnqueueResult:
    """Result of an enqueue operation indicating acceptance or rejection."""

    accepted: bool
    reason: str = ""


class CommandQueue:
    """FIFO command queue with deduplication, expiration, and persistence.

    Args:
        storage_path: Optional path for JSON-based queue persistence.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._queue: List[Command] = []
        self._storage_path = storage_path
        self._seen_keys: Dict[str, float] = {}
        self._dedup_window: Optional[int] = None

    def enqueue(
        self,
        command: Command,
        require_auth: bool = False,
        require_role: Optional[str] = None,
        require_confirmation: bool = False,
        confirmed: bool = False,
    ) -> EnqueueResult:
        """Add a command to the queue after validation and deduplication checks.

        Args:
            command: The command to enqueue.
            require_auth: If True, reject commands without a user_id.
            require_role: If set, reject commands whose user_role doesn't match.
            require_confirmation: If True, require the confirmed flag to be set.
            confirmed: Whether the command has been explicitly confirmed.

        Returns:
            An EnqueueResult indicating whether the command was accepted.
        """
        if not command.action or command.params is None:
            return EnqueueResult(accepted=False, reason="Invalid payload")

        if require_auth and command.user_id is None:
            return EnqueueResult(accepted=False, reason="Authentication required")

        if require_role and command.user_role != require_role:
            return EnqueueResult(accepted=False, reason="Insufficient role")

        if require_confirmation and not confirmed:
            return EnqueueResult(accepted=False, reason="Confirmation required")

        if command.idempotency_key is not None:
            window = self._dedup_window
            now = time.time()
            if window is None or window > 0:
                if command.idempotency_key in self._seen_keys:
                    prev_time = self._seen_keys[command.idempotency_key]
                    if window is None or (now - prev_time) < window:
                        return EnqueueResult(accepted=False, reason="Duplicate")
            self._seen_keys[command.idempotency_key] = now

        self._queue.append(command)
        return EnqueueResult(accepted=True)

    def dequeue(self) -> Optional[Command]:
        """Remove and return the next command from the queue, or None if empty."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def size(self) -> int:
        """Return the number of commands currently in the queue."""
        return len(self._queue)

    def set_dedup_window(self, seconds: int) -> None:
        """Set the deduplication window in seconds for idempotency key checks."""
        self._dedup_window = seconds

    def remove_expired(self) -> None:
        """Remove all commands whose TTL has elapsed."""
        now = time.time()
        self._queue = [
            cmd for cmd in self._queue
            if cmd.ttl_seconds is None or (now - cmd.created_at) < cmd.ttl_seconds
        ]

    def save(self) -> None:
        """Persist the current queue to the configured storage path as JSON."""
        if self._storage_path is None:
            return
        data = []
        for cmd in self._queue:
            data.append({
                "action": cmd.action,
                "params": cmd.params,
                "user_id": cmd.user_id,
                "idempotency_key": cmd.idempotency_key,
                "ttl_seconds": cmd.ttl_seconds,
                "user_role": cmd.user_role,
                "created_at": cmd.created_at,
            })
        self._storage_path.write_text(json.dumps(data))

    def load(self) -> None:
        """Load the queue from the configured storage path."""
        if self._storage_path is None or not self._storage_path.exists():
            return
        data = json.loads(self._storage_path.read_text())
        for entry in data:
            cmd = Command(
                action=entry["action"],
                params=entry["params"],
                user_id=entry["user_id"],
                idempotency_key=entry.get("idempotency_key"),
                ttl_seconds=entry.get("ttl_seconds"),
                user_role=entry.get("user_role"),
                created_at=entry.get("created_at", time.time()),
            )
            self._queue.append(cmd)
