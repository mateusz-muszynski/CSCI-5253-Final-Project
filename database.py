"""
Firestore database integration for storing and retrieving job data.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from google.cloud import firestore
from google.cloud.exceptions import NotFound
import logging

from config import Config
from models import JobStatus, ProcessingResult

logger = logging.getLogger(__name__)


class Database:
    """Firestore database client for job storage."""
    
    def __init__(self):
        """Initialize Firestore client."""
        self.db = firestore.Client(project=Config.PROJECT_ID)
        self.collection = Config.FIRESTORE_COLLECTION
    
    def create_job(
        self,
        job_id: str,
        original_text: str,
        mode: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new job document in Firestore.
        
        Args:
            job_id: Unique job identifier
            original_text: Original submitted text
            mode: Processing mode (sync/async)
            metadata: Optional metadata
            
        Returns:
            Dictionary with job data
        """
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "original_text": original_text,
            "mode": mode,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {}
        }
        
        try:
            doc_ref = self.db.collection(self.collection).document(job_id)
            doc_ref.set(job_data)
            logger.info(f"Created job {job_id} in Firestore")
            return job_data
        except Exception as e:
            logger.error(f"Error creating job {job_id}: {str(e)}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a job document from Firestore.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job data dictionary or None if not found
        """
        try:
            doc_ref = self.db.collection(self.collection).document(job_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                # Convert Firestore timestamps to datetime if needed
                if "created_at" in data and hasattr(data["created_at"], "timestamp"):
                    data["created_at"] = data["created_at"]
                if "completed_at" in data and hasattr(data["completed_at"], "timestamp"):
                    data["completed_at"] = data["completed_at"]
                return data
            else:
                logger.warning(f"Job {job_id} not found in Firestore")
                return None
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {str(e)}")
            raise
    
    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error: Optional[str] = None
    ) -> None:
        """
        Update job status in Firestore.
        
        Args:
            job_id: Unique job identifier
            status: New job status
            error: Optional error message
        """
        try:
            doc_ref = self.db.collection(self.collection).document(job_id)
            update_data = {
                "status": status.value,
                "updated_at": datetime.utcnow()
            }
            
            if error:
                update_data["error"] = error
            
            if status == JobStatus.PROCESSING:
                update_data["processing_started_at"] = datetime.utcnow()
            elif status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                update_data["completed_at"] = datetime.utcnow()
            
            doc_ref.update(update_data)
            logger.info(f"Updated job {job_id} status to {status.value}")
        except Exception as e:
            logger.error(f"Error updating job {job_id} status: {str(e)}")
            raise
    
    def save_result(self, job_id: str, result: ProcessingResult) -> None:
        """
        Save processing results to Firestore.
        
        Args:
            job_id: Unique job identifier
            result: ProcessingResult object
        """
        try:
            doc_ref = self.db.collection(self.collection).document(job_id)
            
            result_data = {
                "status": result.status.value,
                "detected_language": result.detected_language,
                "translated_text": result.translated_text,
                "sentiment": result.sentiment,
                "summary": result.summary,
                "entities": result.entities,
                "completed_at": result.completed_at or datetime.utcnow(),
                "error": result.error,
                "updated_at": datetime.utcnow()
            }
            
            doc_ref.update(result_data)
            logger.info(f"Saved results for job {job_id}")
        except Exception as e:
            logger.error(f"Error saving results for job {job_id}: {str(e)}")
            raise

