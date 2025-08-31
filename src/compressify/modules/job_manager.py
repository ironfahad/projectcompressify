"""
Job management system for handling compression tasks.
"""

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple, Union

from rich.console import Console
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from ..config import ImageSettings, VideoSettings
from ..utils import format_file_size


class JobStatus(Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class JobType(Enum):
    """Job type enumeration."""

    VIDEO = "video"
    IMAGE = "image"


@dataclass
class JobResult:
    """Results from a completed job."""

    success: bool
    input_path: Path
    output_path: Optional[Path] = None
    original_size: int = 0
    compressed_size: int = 0
    savings: Optional[Dict] = None
    error: Optional[str] = None
    duration: float = 0.0
    input_info: Optional[Dict] = None
    output_info: Optional[Dict] = None


@dataclass
class Job:
    """Individual compression job."""

    id: str
    input_path: Path
    output_path: Path
    job_type: JobType
    settings: Union[VideoSettings, ImageSettings]
    status: JobStatus = JobStatus.PENDING
    result: Optional[JobResult] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    progress: float = 0.0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def duration(self) -> float:
        """Get job duration in seconds."""
        if self.started_at is None:
            return 0.0

        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict:
        """Convert job to dictionary for serialization."""
        return {
            "id": self.id,
            "input_path": str(self.input_path),
            "output_path": str(self.output_path),
            "job_type": self.job_type.value,
            "settings": self.settings.dict()
            if hasattr(self.settings, "dict")
            else asdict(self.settings),
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
            "error": self.error,
            "progress": self.progress,
            "result": asdict(self.result) if self.result else None,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Job":
        """Create job from dictionary."""
        # Parse dates
        created_at = (
            datetime.fromisoformat(data["created_at"])
            if data.get("created_at")
            else None
        )
        started_at = (
            datetime.fromisoformat(data["started_at"])
            if data.get("started_at")
            else None
        )
        completed_at = (
            datetime.fromisoformat(data["completed_at"])
            if data.get("completed_at")
            else None
        )

        # Parse settings based on job type
        job_type = JobType(data["job_type"])
        if job_type == JobType.VIDEO:
            settings = VideoSettings(**data["settings"])
        else:
            settings = ImageSettings(**data["settings"])

        # Parse result if present
        result = None
        if data.get("result"):
            result_data = data["result"]
            result = JobResult(
                success=result_data["success"],
                input_path=Path(result_data["input_path"]),
                output_path=Path(result_data["output_path"])
                if result_data.get("output_path")
                else None,
                original_size=result_data.get("original_size", 0),
                compressed_size=result_data.get("compressed_size", 0),
                savings=result_data.get("savings"),
                error=result_data.get("error"),
                duration=result_data.get("duration", 0.0),
                input_info=result_data.get("input_info"),
                output_info=result_data.get("output_info"),
            )

        return cls(
            id=data["id"],
            input_path=Path(data["input_path"]),
            output_path=Path(data["output_path"]),
            job_type=job_type,
            settings=settings,
            status=JobStatus(data["status"]),
            result=result,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            error=data.get("error"),
            progress=data.get("progress", 0.0),
        )


class JobManager:
    """
    Manages compression jobs with progress tracking and parallel execution.
    """

    def __init__(
        self,
        console: Console,
        max_workers: Optional[int] = None,
        state_dir: Optional[Path] = None,
    ):
        self.console = console
        self.max_workers = max_workers or min(4, (threading.active_count() or 1) + 4)
        self.jobs: Dict[str, Job] = {}
        self.active_jobs: Set[str] = set()
        self.progress_bars: Dict[str, TaskID] = {}
        self._shutdown = False
        self._lock = threading.Lock()

        # Set up state directory
        if state_dir:
            self.state_dir = state_dir
        else:
            # Try environment variable first, fallback to default
            env_dir = os.environ.get("COMPRESSIFY_JOBS_DIR")
            if env_dir:
                self.state_dir = Path(env_dir)
            else:
                self.state_dir = Path.home() / ".compressify"

        self.state_file = self.state_dir / "jobs.json"

        # Load existing state
        self.load_state()

    def create_job(
        self,
        input_path: Path,
        output_path: Path,
        job_type: JobType,
        settings: Union[VideoSettings, ImageSettings],
    ) -> str:
        """Create a new compression job."""
        job_id = f"{job_type.value}_{input_path.stem}_{int(time.time())}"

        job = Job(
            id=job_id,
            input_path=input_path,
            output_path=output_path,
            job_type=job_type,
            settings=settings,
        )

        self.jobs[job_id] = job
        self.save_state()
        return job_id

    def create_batch_jobs(
        self,
        file_pairs: List[Tuple[Path, Path]],
        job_type: JobType,
        settings: Union[VideoSettings, ImageSettings],
    ) -> List[str]:
        """Create multiple compression jobs."""
        job_ids = []
        timestamp = int(time.time())

        for i, (input_path, output_path) in enumerate(file_pairs):
            job_id = f"{job_type.value}_{input_path.stem}_{timestamp}_{i}"

            job = Job(
                id=job_id,
                input_path=input_path,
                output_path=output_path,
                job_type=job_type,
                settings=settings,
            )

            self.jobs[job_id] = job
            job_ids.append(job_id)

        self.save_state()
        return job_ids

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(
        self, status: Optional[JobStatus] = None, job_type: Optional[JobType] = None
    ) -> List[Job]:
        """List jobs with optional filtering."""
        jobs = list(self.jobs.values())

        if status:
            jobs = [job for job in jobs if job.status == status]

        if job_type:
            jobs = [job for job in jobs if job.job_type == job_type]

        return sorted(jobs, key=lambda j: j.created_at, reverse=True)

    def execute_jobs(
        self, job_ids: List[str], worker_func: Callable[[Path, Path, Dict], JobResult]
    ) -> Dict[str, JobResult]:
        """Execute multiple jobs in parallel with progress tracking."""
        if not job_ids:
            return {}

        # Create progress tracking
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            with Live(progress, console=self.console, refresh_per_second=10):
                # Submit all jobs
                future_to_job = {}
                for job_id in job_ids:
                    job = self.jobs[job_id]
                    if job.status in [JobStatus.PENDING, JobStatus.FAILED]:
                        # Create progress task
                        task_id = progress.add_task(
                            f"Processing {job.input_path.name}",
                            filename=job.input_path.name,
                            total=100,
                        )
                        self.progress_bars[job_id] = task_id

                        # Mark job as running
                        job.status = JobStatus.RUNNING
                        job.started_at = datetime.now()
                        self.active_jobs.add(job_id)

                        # Submit to executor
                        future = executor.submit(
                            self._execute_single_job,
                            job,
                            worker_func,
                            lambda p: progress.update(task_id, completed=p),
                        )
                        future_to_job[future] = job_id

                # Wait for completion
                for future in future_to_job:
                    try:
                        result = future.result()
                        job_id = future_to_job[future]
                        job = self.jobs[job_id]

                        # Update job with result
                        job.result = result
                        job.completed_at = datetime.now()
                        job.status = (
                            JobStatus.COMPLETED if result.success else JobStatus.FAILED
                        )
                        job.error = result.error

                        # Update progress to 100%
                        if job_id in self.progress_bars:
                            progress.update(self.progress_bars[job_id], completed=100)

                        results[job_id] = result
                        self.active_jobs.discard(job_id)

                        # Save state after each job completion
                        self.save_state()

                    except Exception as e:
                        job_id = future_to_job[future]
                        job = self.jobs[job_id]
                        job.status = JobStatus.FAILED
                        job.error = str(e)
                        job.completed_at = datetime.now()
                        self.active_jobs.discard(job_id)

                        # Create failed result
                        result = JobResult(
                            success=False, input_path=job.input_path, error=str(e)
                        )
                        job.result = result
                        results[job_id] = result

                        # Update progress to show error
                        if job_id in self.progress_bars:
                            progress.update(
                                self.progress_bars[job_id],
                                completed=100,
                                description=f"[red]Failed: {job.input_path.name}[/red]",
                            )

                        self.save_state()

        return results

    def _execute_single_job(
        self,
        job: Job,
        worker_func: Callable[[Path, Path, Dict], JobResult],
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> JobResult:
        """Execute a single compression job."""
        try:
            # Convert settings to dict for worker function
            if hasattr(job.settings, "dict"):
                settings_dict = job.settings.dict()
            else:
                settings_dict = asdict(job.settings)

            # Execute the actual compression
            result = worker_func(
                job.input_path, job.output_path, settings_dict, progress_callback
            )

            return result

        except Exception as e:
            return JobResult(
                success=False, input_path=job.input_path, error=str(e)
            )

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a specific job."""
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            self.active_jobs.discard(job_id)
            self.save_state()
            return True
        return False

    def cancel_all_jobs(self):
        """Cancel all running jobs."""
        cancelled_count = 0
        for job_id in list(self.active_jobs):
            if self.cancel_job(job_id):
                cancelled_count += 1

        if cancelled_count > 0:
            self.console.print(f"[yellow]Cancelled {cancelled_count} jobs[/yellow]")

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.RUNNING:
            job.status = JobStatus.PAUSED
            self.save_state()
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        job = self.jobs.get(job_id)
        if job and job.status == JobStatus.PAUSED:
            job.status = JobStatus.PENDING
            self.save_state()
            return True
        return False

    def retry_failed_jobs(self) -> List[str]:
        """Retry all failed jobs."""
        failed_jobs = self.list_jobs(status=JobStatus.FAILED)
        retried_jobs = []

        for job in failed_jobs:
            job.status = JobStatus.PENDING
            job.error = None
            job.result = None
            job.started_at = None
            job.completed_at = None
            job.progress = 0.0
            retried_jobs.append(job.id)

        self.save_state()
        return retried_jobs

    def save_state(self):
        """Save job state to file."""
        if self._shutdown:
            return

        with self._lock:
            try:
                # Ensure directory exists
                self.state_file.parent.mkdir(parents=True, exist_ok=True)

                # Convert jobs to serializable format
                jobs_data = {job_id: job.to_dict() for job_id, job in self.jobs.items()}

                # Save to file
                with open(self.state_file, "w") as f:
                    json.dump(jobs_data, f, indent=2)

            except (PermissionError, OSError):
                # Silently ignore permission/file system errors in containerized environments
                # Job state saving is non-critical for core compression functionality
                pass
            except Exception as e:
                # Only log unexpected errors
                self.console.print(f"[yellow]Warning: Failed to save job state: {e}[/yellow]")

    def load_state(self):
        """Load job state from file."""
        with self._lock:
            try:
                if not self.state_file.exists():
                    return

                with open(self.state_file, "r") as f:
                    jobs_data = json.load(f)

                # Reconstruct jobs from data
                for job_id, job_data in jobs_data.items():
                    try:
                        job = Job.from_dict(job_data)
                        self.jobs[job_id] = job

                        # Reset running jobs to pending (they were interrupted)
                        if job.status == JobStatus.RUNNING:
                            job.status = JobStatus.PENDING
                            job.started_at = None

                    except Exception as e:
                        self.console.print(
                            f"[yellow]Warning: Could not load job {job_id}: {e}[/yellow]"
                        )

            except Exception:
                # If state file is corrupted or unreadable, start fresh
                self.jobs = {}

    def get_statistics(self) -> Dict:
        """Get job statistics."""
        total_jobs = len(self.jobs)
        pending = len([j for j in self.jobs.values() if j.status == JobStatus.PENDING])
        running = len([j for j in self.jobs.values() if j.status == JobStatus.RUNNING])
        completed = len(
            [j for j in self.jobs.values() if j.status == JobStatus.COMPLETED]
        )
        failed = len([j for j in self.jobs.values() if j.status == JobStatus.FAILED])
        cancelled = len(
            [j for j in self.jobs.values() if j.status == JobStatus.CANCELLED]
        )

        # Calculate total compression savings
        successful_jobs = [
            j for j in self.jobs.values() if j.result and j.result.success
        ]
        total_original = sum(j.result.original_size for j in successful_jobs)
        total_compressed = sum(j.result.compressed_size for j in successful_jobs)
        total_savings = total_original - total_compressed
        savings_percentage = (
            (total_savings / total_original * 100) if total_original > 0 else 0
        )

        return {
            "total_jobs": total_jobs,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "total_original_size": total_original,
            "total_compressed_size": total_compressed,
            "total_savings": total_savings,
            "savings_percentage": savings_percentage,
        }

    def display_status(self):
        """Display current job status in a table."""
        stats = self.get_statistics()

        table = Table(title="Job Manager Status")
        table.add_column("Status", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Total Jobs", str(stats["total_jobs"]))
        table.add_row("Pending", str(stats["pending"]))
        table.add_row("Running", str(stats["running"]))
        table.add_row("Completed", str(stats["completed"]))
        table.add_row("Failed", str(stats["failed"]))
        table.add_row("Cancelled", str(stats["cancelled"]))

        if stats["total_original_size"] > 0:
            table.add_row("", "")  # Separator
            table.add_row(
                "Original Size", format_file_size(stats["total_original_size"])
            )
            table.add_row(
                "Compressed Size", format_file_size(stats["total_compressed_size"])
            )
            table.add_row("Total Savings", format_file_size(stats["total_savings"]))
            table.add_row("Savings %", f"{stats['savings_percentage']:.1f}%")

        self.console.print(table)

    def clear_completed_jobs(self) -> int:
        """Remove completed jobs from memory."""
        completed_jobs = [
            job_id
            for job_id, job in self.jobs.items()
            if job.status in [JobStatus.COMPLETED, JobStatus.CANCELLED]
        ]

        for job_id in completed_jobs:
            del self.jobs[job_id]

        self.save_state()
        return len(completed_jobs)

    def clear_failed_jobs(self) -> int:
        """Remove failed jobs from memory."""
        failed_jobs = [
            job_id for job_id, job in self.jobs.items() if job.status == JobStatus.FAILED
        ]

        for job_id in failed_jobs:
            del self.jobs[job_id]

        self.save_state()
        return len(failed_jobs)

    def shutdown(self):
        """Shutdown the job manager."""
        self._shutdown = True
        self.cancel_all_jobs()
        self.save_state()