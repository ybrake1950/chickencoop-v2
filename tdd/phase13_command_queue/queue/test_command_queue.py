"""
Phase 13: Command Queue Tests
=============================

FUNCTIONALITY BEING TESTED:
---------------------------
- DynamoDB-backed command queue
- FIFO ordering of commands
- Command deduplication
- Queue persistence across restarts
- Command expiration

WHY THIS MATTERS:
-----------------
Replaces insecure /tmp file-based command triggers with a proper queue.
Commands from the dashboard are queued and executed reliably on the Pi,
with full audit trail and retry support.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase13_command_queue/queue/test_command_queue.py -v
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

from src.command_queue.queue import CommandQueue, Command, CommandStatus


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def queue(tmp_path):
    """Provide a command queue."""
    return CommandQueue(storage_path=tmp_path / "queue.db")

@pytest.fixture
def sample_command():
    """Provide a sample command."""
    return Command(action="record", params={"duration": 60, "camera": "indoor"}, user_id="user-123")


# =============================================================================
# TestQueueOperations
# =============================================================================

class TestQueueOperations:
    """Test basic queue operations."""

    def test_enqueue_command(self, queue, sample_command):
        """Commands can be enqueued."""
        queue.enqueue(sample_command)
        assert queue.size() == 1

    def test_dequeue_command(self, queue, sample_command):
        """Commands can be dequeued."""
        queue.enqueue(sample_command)
        cmd = queue.dequeue()
        assert cmd is not None
        assert cmd.action == "record"

    def test_fifo_ordering(self, queue):
        """Commands dequeued in FIFO order."""
        queue.enqueue(Command(action="record", params={}, user_id="u1"))
        queue.enqueue(Command(action="headcount", params={}, user_id="u1"))
        queue.enqueue(Command(action="restart", params={}, user_id="u1"))

        assert queue.dequeue().action == "record"
        assert queue.dequeue().action == "headcount"
        assert queue.dequeue().action == "restart"

    def test_queue_persistence(self, queue, sample_command, tmp_path):
        """Queue persists across restarts."""
        queue.enqueue(sample_command)
        queue.save()

        queue2 = CommandQueue(storage_path=tmp_path / "queue.db")
        queue2.load()
        assert queue2.size() >= 1

    def test_empty_queue_returns_none(self, queue):
        """Empty queue returns None on dequeue."""
        cmd = queue.dequeue()
        assert cmd is None


# =============================================================================
# TestCommandDeduplication
# =============================================================================

class TestCommandDeduplication:
    """Test command deduplication."""

    def test_duplicate_command_rejected(self, queue):
        """Duplicate commands rejected."""
        cmd1 = Command(action="record", params={}, user_id="u1", idempotency_key="key-1")
        cmd2 = Command(action="record", params={}, user_id="u1", idempotency_key="key-1")
        queue.enqueue(cmd1)
        result = queue.enqueue(cmd2)
        assert result.accepted is False or queue.size() == 1

    def test_dedup_window_configurable(self, queue):
        """Deduplication window is configurable."""
        queue.set_dedup_window(seconds=0)
        cmd1 = Command(action="record", params={}, user_id="u1", idempotency_key="key-1")
        cmd2 = Command(action="record", params={}, user_id="u1", idempotency_key="key-1")
        queue.enqueue(cmd1)
        result = queue.enqueue(cmd2)
        assert result.accepted is True or queue.size() == 2

    def test_different_params_not_duplicate(self, queue):
        """Same command with different params not duplicate."""
        cmd1 = Command(action="record", params={"duration": 30}, user_id="u1", idempotency_key="key-1")
        cmd2 = Command(action="record", params={"duration": 60}, user_id="u1", idempotency_key="key-2")
        queue.enqueue(cmd1)
        queue.enqueue(cmd2)
        assert queue.size() == 2

    def test_dedup_by_idempotency_key(self, queue):
        """Deduplication uses idempotency key."""
        cmd1 = Command(action="record", params={}, user_id="u1", idempotency_key="same-key")
        cmd2 = Command(action="headcount", params={}, user_id="u1", idempotency_key="same-key")
        queue.enqueue(cmd1)
        result = queue.enqueue(cmd2)
        assert result.accepted is False or queue.size() == 1


# =============================================================================
# TestCommandExpiration
# =============================================================================

class TestCommandExpiration:
    """Test command expiration."""

    def test_expired_command_not_executed(self, queue):
        """Expired commands not executed."""
        cmd = Command(action="record", params={}, user_id="u1", ttl_seconds=0)
        queue.enqueue(cmd)
        queue.remove_expired()
        result = queue.dequeue()
        assert result is None

    def test_expiration_configurable(self, queue):
        """Command expiration configurable."""
        cmd = Command(action="record", params={}, user_id="u1", ttl_seconds=3600)
        assert cmd.ttl_seconds == 3600

    def test_expired_commands_cleaned(self, queue):
        """Expired commands cleaned from queue."""
        for i in range(5):
            queue.enqueue(Command(action="record", params={}, user_id="u1", ttl_seconds=0))
        queue.remove_expired()
        assert queue.size() == 0


# =============================================================================
# TestCommandTypes
# =============================================================================

class TestCommandTypes:
    """Test different command types."""

    def test_manual_record_command(self, queue):
        """Manual record command queued."""
        cmd = Command(action="record", params={"duration": 60}, user_id="u1")
        queue.enqueue(cmd)
        assert queue.dequeue().action == "record"

    def test_check_door_command(self, queue):
        """Check door command queued."""
        cmd = Command(action="check_door", params={}, user_id="u1")
        queue.enqueue(cmd)
        assert queue.dequeue().action == "check_door"

    def test_headcount_command(self, queue):
        """Manual headcount command queued."""
        cmd = Command(action="headcount", params={}, user_id="u1")
        queue.enqueue(cmd)
        assert queue.dequeue().action == "headcount"

    def test_config_update_command(self, queue):
        """Config update command queued."""
        cmd = Command(action="config_update", params={"key": "threshold", "value": 95}, user_id="u1")
        queue.enqueue(cmd)
        dequeued = queue.dequeue()
        assert dequeued.action == "config_update"
        assert dequeued.params["key"] == "threshold"

    def test_restart_service_command(self, queue):
        """Restart service command queued."""
        cmd = Command(action="restart_service", params={"service": "monitor"}, user_id="u1")
        queue.enqueue(cmd)
        dequeued = queue.dequeue()
        assert dequeued.action == "restart_service"
        assert dequeued.params["service"] == "monitor"


# =============================================================================
# TestQueueSecurity
# =============================================================================

class TestQueueSecurity:
    """Test queue security."""

    def test_commands_authenticated(self, queue):
        """Commands require authentication."""
        cmd = Command(action="record", params={}, user_id=None)
        result = queue.enqueue(cmd, require_auth=True)
        assert result.accepted is False

    def test_command_authorization(self, queue):
        """Commands require authorization."""
        cmd = Command(action="restart_service", params={}, user_id="u1", user_role="viewer")
        result = queue.enqueue(cmd, require_role="admin")
        assert result.accepted is False

    def test_command_payload_validated(self, queue):
        """Command payload validated."""
        cmd = Command(action="", params=None, user_id="u1")
        result = queue.enqueue(cmd)
        assert result.accepted is False

    def test_dangerous_commands_require_confirm(self, queue):
        """Dangerous commands require confirmation."""
        cmd = Command(action="restart_service", params={"service": "monitor"}, user_id="u1")
        result = queue.enqueue(cmd, require_confirmation=True, confirmed=False)
        assert result.accepted is False
