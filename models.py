"""
Data models for the Multilingual Text Intelligence Service.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ProcessingMode(str, Enum):
    """Processing mode enumeration."""
    SYNC = "sync"
    ASYNC = "async"


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class TextSubmissionRequest(BaseModel):
    """Request model for text submission."""
    text: str = Field(..., description="The text to process", min_length=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata for the request")


class JobResponse(BaseModel):
    """Response model for job creation."""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    mode: ProcessingMode = Field(..., description="Processing mode (sync or async)")
    created_at: datetime = Field(..., description="Job creation timestamp")
    message: str = Field(..., description="Response message")


class ProcessingResult(BaseModel):
    """Model for processing results."""
    job_id: str
    status: JobStatus
    original_text: str
    detected_language: Optional[str] = None
    translated_text: Optional[str] = None
    sentiment: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    entities: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    """Response model for job status query."""
    job_id: str
    status: JobStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[ProcessingResult] = None
    error: Optional[str] = None

