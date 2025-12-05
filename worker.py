"""
Background worker service for processing asynchronous jobs from Pub/Sub.
"""
import logging
import os
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from config import Config
from models import JobStatus, ProcessingResult
from database import Database
from translation_service import TranslationService
from nlp_service import NLPService
from pubsub_client import PubSubSubscriber
from utils import setup_logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


class WorkerService:
    """Worker service for processing async jobs."""
    
    def __init__(self):
        """Initialize worker services."""
        try:
            Config.validate()
            self.db = Database()
            self.translation_service = TranslationService()
            self.nlp_service = NLPService()
            logger.info("Worker service initialized")
        except Exception as e:
            logger.error(f"Error initializing worker service: {str(e)}")
            raise
    
    def process_job(self, message_data: dict) -> None:
        """
        Process a job from the Pub/Sub queue.
        
        Args:
            message_data: Dictionary containing job_id, text, and metadata
        """
        job_id = message_data.get("job_id")
        text = message_data.get("text")
        metadata = message_data.get("metadata", {})
        
        if not job_id or not text:
            logger.error(f"Invalid message data: {message_data}")
            return
        
        logger.info(f"Processing async job {job_id}")
        
        try:
            # Update job status to processing
            self.db.update_job_status(job_id, JobStatus.PROCESSING)
            
            # Detect language and translate
            detected_language, translated_text = self.translation_service.detect_and_translate(text)
            
            # Process with NLP services
            sentiment = self.nlp_service.analyze_sentiment(translated_text or text)
            summary = self.nlp_service.summarize(translated_text or text)
            entities = self.nlp_service.extract_entities(translated_text or text)
            
            # Create result
            result = ProcessingResult(
                job_id=job_id,
                status=JobStatus.COMPLETED,
                original_text=text,
                detected_language=detected_language,
                translated_text=translated_text,
                sentiment=sentiment,
                summary=summary,
                entities=entities,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                metadata=metadata
            )
            
            # Save result
            self.db.save_result(job_id, result)
            self.db.update_job_status(job_id, JobStatus.COMPLETED)
            
            logger.info(f"Successfully completed processing for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")
            self.db.update_job_status(job_id, JobStatus.FAILED, error=str(e))
            raise


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check handler for Cloud Run."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == "/health" or self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "worker"}')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_health_server(port: int = 8080):
    """Start a simple HTTP server for health checks."""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()


def main():
    """Main entry point for the worker service."""
    logger.info("Starting worker service...")
    
    # Start health check server in a separate thread
    port = int(os.environ.get("PORT", 8080))
    health_thread = threading.Thread(target=start_health_server, args=(port,), daemon=True)
    health_thread.start()
    logger.info(f"Health check server running on port {port}")
    
    # Initialize worker
    worker = WorkerService()
    
    def message_callback(message_data: dict):
        """Callback function for Pub/Sub messages."""
        worker.process_job(message_data)
    
    # Start listening to Pub/Sub (this blocks)
    logger.info("Starting Pub/Sub subscriber...")
    subscriber = PubSubSubscriber(message_callback)
    subscriber.start_listening()


if __name__ == "__main__":
    main()

