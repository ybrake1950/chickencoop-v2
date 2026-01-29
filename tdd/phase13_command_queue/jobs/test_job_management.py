"""
Phase 13: Job Management Tests
==============================

FUNCTIONALITY BEING TESTED:
---------------------------
- Job status tracking (pending, running, completed, failed)
- Job progress reporting
- Job result storage
- Job history and audit trail
- Job cancellation

WHY THIS MATTERS:
-----------------
Long-running operations like headcount or video recording need status
tracking. Users should see progress and results. Failed jobs need
retry or manual intervention.

HOW TESTS ARE EXECUTED:
-----------------------
    pytest tdd/phase13_command_queue/jobs/test_job_management.py -v
"""
import pytest
from unittest.mock import MagicMock

from src.command_queue.jobs import JobManager, Job, JobStatus, JobResult


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def manager():
    """Provide a job manager."""
    return JobManager()

@pytest.fixture
def sample_job(manager):
    """Provide a sample job."""
    return manager.create_job(action="record", params={"duration": 60}, user_id="user-123")


# =============================================================================
# TestJobStatus
# =============================================================================

class TestJobStatus:
    """Test job status tracking."""

    def test_job_starts_pending(self, sample_job):
        """New jobs start in pending status."""
        assert sample_job.status == JobStatus.PENDING

    def test_job_transitions_to_running(self, manager, sample_job):
        """Job transitions to running when started."""
        manager.start_job(sample_job.job_id)
        assert manager.get_job(sample_job.job_id).status == JobStatus.RUNNING

    def test_job_transitions_to_completed(self, manager, sample_job):
        """Job transitions to completed on success."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={"video_path": "/tmp/video.mp4"})
        assert manager.get_job(sample_job.job_id).status == JobStatus.COMPLETED

    def test_job_transitions_to_failed(self, manager, sample_job):
        """Job transitions to failed on error."""
        manager.start_job(sample_job.job_id)
        manager.fail_job(sample_job.job_id, error="Camera not available")
        assert manager.get_job(sample_job.job_id).status == JobStatus.FAILED

    def test_job_status_queryable(self, manager, sample_job):
        """Job status can be queried by ID."""
        job = manager.get_job(sample_job.job_id)
        assert job is not None
        assert job.job_id == sample_job.job_id


# =============================================================================
# TestJobProgress
# =============================================================================

class TestJobProgress:
    """Test job progress reporting."""

    def test_progress_percentage_updated(self, manager, sample_job):
        """Progress percentage updated during execution."""
        manager.start_job(sample_job.job_id)
        manager.update_progress(sample_job.job_id, percentage=50)
        job = manager.get_job(sample_job.job_id)
        assert job.progress_percentage == 50

    def test_progress_message_updated(self, manager, sample_job):
        """Progress message updated during execution."""
        manager.start_job(sample_job.job_id)
        manager.update_progress(sample_job.job_id, message="Recording video...")
        job = manager.get_job(sample_job.job_id)
        assert job.progress_message == "Recording video..."

    def test_progress_queryable(self, manager, sample_job):
        """Progress can be queried via API."""
        manager.start_job(sample_job.job_id)
        manager.update_progress(sample_job.job_id, percentage=75)
        progress = manager.get_progress(sample_job.job_id)
        assert progress is not None
        assert progress["percentage"] == 75

    def test_progress_visible_in_dashboard(self, manager, sample_job):
        """Progress visible in dashboard."""
        manager.start_job(sample_job.job_id)
        manager.update_progress(sample_job.job_id, percentage=30)
        dashboard = manager.get_active_jobs()
        assert len(dashboard) >= 1
        assert any(j.job_id == sample_job.job_id for j in dashboard)


# =============================================================================
# TestJobResults
# =============================================================================

class TestJobResults:
    """Test job result storage."""

    def test_success_result_stored(self, manager, sample_job):
        """Successful job result stored."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={"video_url": "s3://bucket/video.mp4"})
        job = manager.get_job(sample_job.job_id)
        assert job.result is not None
        assert job.result["video_url"] == "s3://bucket/video.mp4"

    def test_failure_result_stored(self, manager, sample_job):
        """Failed job error stored."""
        manager.start_job(sample_job.job_id)
        manager.fail_job(sample_job.job_id, error="Disk full")
        job = manager.get_job(sample_job.job_id)
        assert job.error == "Disk full"

    def test_result_includes_duration(self, manager, sample_job):
        """Result includes job duration."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={})
        job = manager.get_job(sample_job.job_id)
        assert job.duration_seconds is not None
        assert job.duration_seconds >= 0

    def test_result_retained_for_period(self, manager, sample_job):
        """Results retained for configured period."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={})
        assert manager.retention_days >= 7


# =============================================================================
# TestJobAudit
# =============================================================================

class TestJobAudit:
    """Test job audit trail."""

    def test_job_creation_logged(self, manager, sample_job):
        """Job creation logged with user."""
        history = manager.get_job_history(sample_job.job_id)
        assert any(e.event == "created" for e in history)

    def test_job_start_logged(self, manager, sample_job):
        """Job start time logged."""
        manager.start_job(sample_job.job_id)
        history = manager.get_job_history(sample_job.job_id)
        assert any(e.event == "started" for e in history)

    def test_job_completion_logged(self, manager, sample_job):
        """Job completion logged with result."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={})
        history = manager.get_job_history(sample_job.job_id)
        assert any(e.event == "completed" for e in history)

    def test_job_history_queryable(self, manager, sample_job):
        """Job history can be queried."""
        history = manager.get_job_history(sample_job.job_id)
        assert isinstance(history, list)
        assert len(history) >= 1


# =============================================================================
# TestJobCancellation
# =============================================================================

class TestJobCancellation:
    """Test job cancellation."""

    def test_pending_job_cancellable(self, manager, sample_job):
        """Pending jobs can be cancelled."""
        result = manager.cancel_job(sample_job.job_id)
        assert result is True
        assert manager.get_job(sample_job.job_id).status == JobStatus.CANCELLED

    def test_running_job_cancellable(self, manager, sample_job):
        """Running jobs can be cancelled."""
        manager.start_job(sample_job.job_id)
        result = manager.cancel_job(sample_job.job_id)
        assert result is True

    def test_completed_job_not_cancellable(self, manager, sample_job):
        """Completed jobs cannot be cancelled."""
        manager.start_job(sample_job.job_id)
        manager.complete_job(sample_job.job_id, result={})
        result = manager.cancel_job(sample_job.job_id)
        assert result is False

    def test_cancellation_logged(self, manager, sample_job):
        """Cancellation logged with user."""
        manager.cancel_job(sample_job.job_id)
        history = manager.get_job_history(sample_job.job_id)
        assert any(e.event == "cancelled" for e in history)


# =============================================================================
# TestJobRetry
# =============================================================================

class TestJobRetry:
    """Test job retry functionality."""

    def test_failed_job_retryable(self, manager, sample_job):
        """Failed jobs can be retried."""
        manager.start_job(sample_job.job_id)
        manager.fail_job(sample_job.job_id, error="Timeout")
        new_job = manager.retry_job(sample_job.job_id)
        assert new_job is not None
        assert new_job.status == JobStatus.PENDING

    def test_retry_count_tracked(self, manager, sample_job):
        """Retry count tracked."""
        manager.start_job(sample_job.job_id)
        manager.fail_job(sample_job.job_id, error="Timeout")
        job2 = manager.retry_job(sample_job.job_id)
        manager.start_job(job2.job_id)
        manager.fail_job(job2.job_id, error="Timeout again")
        job3 = manager.retry_job(job2.job_id)
        assert job3.retry_count == 2

    def test_max_retries_enforced(self, manager):
        """Maximum retries enforced."""
        job = manager.create_job(action="record", params={}, user_id="u1", max_retries=1)
        manager.start_job(job.job_id)
        manager.fail_job(job.job_id, error="Fail 1")
        job2 = manager.retry_job(job.job_id)
        manager.start_job(job2.job_id)
        manager.fail_job(job2.job_id, error="Fail 2")
        result = manager.retry_job(job2.job_id)
        assert result is None  # Max retries exceeded

    def test_retry_with_backoff(self, manager, sample_job):
        """Retries use exponential backoff."""
        delays = manager.get_retry_delays(max_retries=4)
        assert delays[1] > delays[0]
        assert delays[2] > delays[1]
