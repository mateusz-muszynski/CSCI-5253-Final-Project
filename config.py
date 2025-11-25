"""
Configuration management for the Multilingual Text Intelligence Service.
"""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Google Cloud Project
    PROJECT_ID: str = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
    
    # Pub/Sub Configuration
    PUBSUB_TOPIC_NAME: str = os.getenv("PUBSUB_TOPIC_NAME", "text-processing-queue")
    PUBSUB_SUBSCRIPTION_NAME: str = os.getenv("PUBSUB_SUBSCRIPTION_NAME", "text-processing-subscription")
    
    # Firestore Configuration
    FIRESTORE_COLLECTION: str = os.getenv("FIRESTORE_COLLECTION", "text_jobs")
    
    # Processing Configuration
    SYNC_THRESHOLD: int = int(os.getenv("SYNC_THRESHOLD", "1000"))  # Characters threshold for sync processing
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8080"))
    
    # Translation API
    TRANSLATION_API_ENABLED: bool = os.getenv("TRANSLATION_API_ENABLED", "true").lower() == "true"
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls) -> None:
        """Validate that required configuration is present."""
        if not cls.PROJECT_ID:
            raise ValueError("GOOGLE_CLOUD_PROJECT_ID must be set in environment variables")
    
    @classmethod
    def get_pubsub_topic_path(cls) -> str:
        """Get the full Pub/Sub topic path."""
        return f"projects/{cls.PROJECT_ID}/topics/{cls.PUBSUB_TOPIC_NAME}"
    
    @classmethod
    def get_pubsub_subscription_path(cls) -> str:
        """Get the full Pub/Sub subscription path."""
        return f"projects/{cls.PROJECT_ID}/subscriptions/{cls.PUBSUB_SUBSCRIPTION_NAME}"

