"""
Main FastAPI application for the Multilingual Text Intelligence Service.

"""
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from models import (
    TextSubmissionRequest,
    JobResponse,
    JobStatusResponse,
    ProcessingMode,
    JobStatus,
    ProcessingResult
)
from database import Database
from pubsub_client import PubSubClient
from translation_service import TranslationService
from utils import generate_job_id, determine_processing_mode, setup_logging
from nlp_service import NLPService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multilingual Text Intelligence Service",
    description="Cloud-native service for multilingual text analysis",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
try:
    Config.validate()
    db = Database()
    pubsub = PubSubClient()
    translation_service = TranslationService()
    # Lazy initialization for NLP service (loads models on first use)
    nlp_service = None
    logger.info("Core services initialized successfully")
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    raise


def get_nlp_service():
    """Get or initialize NLP service lazily."""
    global nlp_service
    if nlp_service is None:
        logger.info("Initializing NLP service (lazy load)...")
        nlp_service = NLPService()
        logger.info("NLP service initialized")
    return nlp_service


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "service": "Multilingual Text Intelligence Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/v1/process", response_model=JobResponse)
async def process_text(request: TextSubmissionRequest):
    """
    Submit text for processing.
    
    Determines processing mode (sync/async) based on text length and processes accordingly.
    """
    try:
        # Generate job ID
        job_id = generate_job_id()
        
        # Determine processing mode
        mode = determine_processing_mode(request.text)
        
        # Create job in database
        db.create_job(
            job_id=job_id,
            original_text=request.text,
            mode=mode.value,
            metadata=request.metadata
        )
        
        if mode == ProcessingMode.SYNC:
            # Synchronous processing
            logger.info(f"Processing job {job_id} synchronously")
            db.update_job_status(job_id, JobStatus.PROCESSING)
            
            try:
                # Detect language and translate
                detected_language, translated_text = translation_service.detect_and_translate(
                    request.text
                )
                
                # Process with NLP services (lazy initialization)
                nlp = get_nlp_service()
                sentiment = nlp.analyze_sentiment(translated_text or request.text)
                summary = nlp.summarize(translated_text or request.text)
                entities = nlp.extract_entities(translated_text or request.text)
                
                # Create result
                result = ProcessingResult(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    original_text=request.text,
                    detected_language=detected_language,
                    translated_text=translated_text,
                    sentiment=sentiment,
                    summary=summary,
                    entities=entities,
                    created_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    metadata=request.metadata
                )
                
                # Save result
                db.save_result(job_id, result)
                db.update_job_status(job_id, JobStatus.COMPLETED)
                
                logger.info(f"Completed synchronous processing for job {job_id}")
                
                return JobResponse(
                    job_id=job_id,
                    status=JobStatus.COMPLETED,
                    mode=mode,
                    created_at=result.created_at,
                    message="Text processed successfully"
                )
                
            except Exception as e:
                logger.error(f"Error in synchronous processing for job {job_id}: {str(e)}")
                db.update_job_status(job_id, JobStatus.FAILED, error=str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Processing failed: {str(e)}"
                )
        
        else:
            # Asynchronous processing
            logger.info(f"Publishing job {job_id} to Pub/Sub for async processing")
            pubsub.publish_job(
                job_id=job_id,
                text=request.text,
                metadata=request.metadata
            )
            
            return JobResponse(
                job_id=job_id,
                status=JobStatus.PENDING,
                mode=mode,
                created_at=datetime.utcnow(),
                message="Job queued for asynchronous processing"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Retrieve the status and results of a processing job.
    """
    try:
        job_data = db.get_job(job_id)
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Build response
        response = JobStatusResponse(
            job_id=job_id,
            status=JobStatus(job_data["status"]),
            created_at=job_data["created_at"],
            completed_at=job_data.get("completed_at"),
            error=job_data.get("error")
        )
        
        # If completed, include result
        if response.status == JobStatus.COMPLETED:
            result = ProcessingResult(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                original_text=job_data["original_text"],
                detected_language=job_data.get("detected_language"),
                translated_text=job_data.get("translated_text"),
                sentiment=job_data.get("sentiment"),
                summary=job_data.get("summary"),
                entities=job_data.get("entities"),
                created_at=job_data["created_at"],
                completed_at=job_data.get("completed_at"),
                metadata=job_data.get("metadata")
            )
            response.result = result
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level=Config.LOG_LEVEL.lower()
    )

