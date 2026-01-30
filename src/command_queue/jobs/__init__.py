"""Job management for the command queue.

Provides job lifecycle management including status tracking, progress monitoring,
result storage, cancellation, and retry with exponential backoff.
"""

import enum
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class JobStatus(enum.Enum):
    """Possible states for a job in its lifecycle."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobResult:
    """Outcome of a completed or failed job."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class JobEvent:
    """An auditable event in a job's lifecycle."""

    event: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class Job:
    """A unit of work tracked by the job manager."""

    job_id: str
    action: str
    params: Dict[str, Any]
    user_id: str
    status: JobStatus = JobStatus.PENDING
    progress_percentage: int = 0
    progress_message: str = ""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    _start_time: Optional[float] = field(default=None, repr=False)


class JobManager:
    """Manages job creation, execution tracking, and lifecycle operations."""

    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._history: Dict[str, List[JobEvent]] = {}
        self.retention_days: int = 30

    def create_job(self, action: str, params: Dict[str, Any], user_id: str, max_retries: int = 3) -> Job:
        """Create a new job and register it with the manager.

        Args:
            action: The command action to execute.
            params: Parameters for the action.
            user_id: Identifier of the user who created the job.
            max_retries: Maximum number of retry attempts allowed.

        Returns:
            The newly created Job instance.
        """
        job_id = str(uuid.uuid4())
        job = Job(job_id=job_id, action=action, params=params, user_id=user_id, max_retries=max_retries)
        self._jobs[job_id] = job
        self._history[job_id] = [JobEvent(event="created")]
        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Retrieve a job by its ID, or None if not found."""
        return self._jobs.get(job_id)

    def start_job(self, job_id: str) -> None:
        """Transition a job to RUNNING status and record the start time."""
        job = self._jobs[job_id]
        job.status = JobStatus.RUNNING
        job._start_time = time.time()
        self._history[job_id].append(JobEvent(event="started"))

    def complete_job(self, job_id: str, result: Dict[str, Any]) -> None:
        """Mark a job as COMPLETED, storing its result and duration."""
        job = self._jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.result = result
        if job._start_time is not None:
            job.duration_seconds = time.time() - job._start_time
        else:
            job.duration_seconds = 0.0
        self._history[job_id].append(JobEvent(event="completed"))

    def fail_job(self, job_id: str, error: str) -> None:
        """Mark a job as FAILED with the given error message."""
        job = self._jobs[job_id]
        job.status = JobStatus.FAILED
        job.error = error
        self._history[job_id].append(JobEvent(event="failed"))

    def update_progress(self, job_id: str, percentage: int = 0, message: str = "") -> None:
        """Update the progress percentage and/or message for a running job."""
        job = self._jobs[job_id]
        if percentage:
            job.progress_percentage = percentage
        if message:
            job.progress_message = message

    def get_progress(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Return the current progress of a job, or None if the job doesn't exist."""
        job = self._jobs.get(job_id)
        if job is None:
            return None
        return {"percentage": job.progress_percentage, "message": job.progress_message}

    def get_active_jobs(self) -> List[Job]:
        """Return all jobs currently in RUNNING status."""
        return [j for j in self._jobs.values() if j.status == JobStatus.RUNNING]

    def get_job_history(self, job_id: str) -> List[JobEvent]:
        """Return the list of lifecycle events for a given job."""
        return self._history.get(job_id, [])

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job.

        Returns:
            True if the job was cancelled, False if it cannot be cancelled
            (already completed, failed, cancelled, or not found).
        """
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return False
        job.status = JobStatus.CANCELLED
        self._history[job_id].append(JobEvent(event="cancelled"))
        return True

    def retry_job(self, job_id: str) -> Optional[Job]:
        """Retry a failed job by creating a new job with an incremented retry count.

        Returns:
            A new Job instance if retry is allowed, or None if the job
            cannot be retried (not failed, not found, or max retries exceeded).
        """
        job = self._jobs.get(job_id)
        if job is None or job.status != JobStatus.FAILED:
            return None
        new_retry_count = job.retry_count + 1
        if new_retry_count > job.max_retries:
            return None
        new_job = self.create_job(action=job.action, params=job.params, user_id=job.user_id, max_retries=job.max_retries)
        new_job.retry_count = new_retry_count
        return new_job

    def get_retry_delays(self, max_retries: int) -> List[float]:
        """Return exponential backoff delays for the given number of retries."""
        return [2 ** i for i in range(max_retries)]
