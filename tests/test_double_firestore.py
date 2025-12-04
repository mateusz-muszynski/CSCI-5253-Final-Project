from datetime import datetime
from typing import Dict, Any, Optional
from models import JobStatus, ProcessingResult


class FirestoreTestDouble:
    """In-memory test double for Firestore Database."""

    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(
        self, job_id: str, original_text: str, mode: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Simulate creating a job document in Firestore."""
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "original_text": original_text,
            "mode": mode,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
            "updated_at": None,
            "completed_at": None,
            "processing_started_at": None,
            "detected_language": None,
            "translated_text": None,
            "sentiment": None,
            "summary": None,
            "entities": None,
            "error": None,
        }
        self._jobs[job_id] = job_data
        return job_data

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a job by ID."""
        return self._jobs.get(job_id)

    def update_job_status(self, job_id: str, status: JobStatus, error: Optional[str] = None) -> None:
        """Update job status (and optional error) in memory."""
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} does not exist")
        job = self._jobs[job_id]
        job["status"] = status.value
        now = datetime.utcnow()
        job["updated_at"] = now
        if status == JobStatus.PROCESSING:
            job["processing_started_at"] = now
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
            job["completed_at"] = now
        if error:
            job["error"] = error

    def save_result(self, job_id: str, result: ProcessingResult) -> None:
        """Save processing results to in-memory store."""
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} does not exist")
        job = self._jobs[job_id]
        job.update({
            "status": result.status.value,
            "detected_language": result.detected_language,
            "translated_text": result.translated_text,
            "sentiment": result.sentiment,
            "summary": result.summary,
            "entities": result.entities,
            "completed_at": result.completed_at or datetime.utcnow(),
            "error": result.error,
            "updated_at": datetime.utcnow(),
        })

    def clear(self):
        """Clear all stored jobs (useful for test isolation)."""
        self._jobs.clear()
