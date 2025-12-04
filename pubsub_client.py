"""
Google Cloud Pub/Sub integration for asynchronous message queueing.

"""
import json
import logging
from typing import Dict, Any, Optional
from google.cloud import pubsub_v1
from google.api_core import exceptions

from config import Config

logger = logging.getLogger(__name__)


class PubSubClient:
    """Pub/Sub client for publishing and subscribing to messages."""
    
    def __init__(self):
        """Initialize Pub/Sub publisher client."""
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = Config.get_pubsub_topic_path()
        self._ensure_topic_exists()
    
    def _ensure_topic_exists(self) -> None:
        """Ensure the Pub/Sub topic exists, create if it doesn't."""
        try:
            project_path = f"projects/{Config.PROJECT_ID}"
            topic_name = Config.PUBSUB_TOPIC_NAME
            
            # Try to get the topic
            try:
                topic = self.publisher.get_topic(request={"topic": self.topic_path})
                logger.info(f"Topic {self.topic_path} already exists")
            except exceptions.NotFound:
                # Topic doesn't exist, create it
                logger.info(f"Creating topic {self.topic_path}")
                topic = self.publisher.create_topic(
                    request={"name": self.topic_path}
                )
                logger.info(f"Created topic {self.topic_path}")
        except Exception as e:
            logger.warning(f"Could not ensure topic exists: {str(e)}")
            logger.warning("Topic creation may require manual setup or proper IAM permissions")
    
    def publish_job(self, job_id: str, text: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Publish a job to the Pub/Sub queue for asynchronous processing.
        
        Args:
            job_id: Unique job identifier
            text: Text to process
            metadata: Optional metadata
            
        Returns:
            Message ID from Pub/Sub
        """
        try:
            message_data = {
                "job_id": job_id,
                "text": text,
                "metadata": metadata or {}
            }
            
            message_json = json.dumps(message_data).encode("utf-8")
            
            future = self.publisher.publish(
                self.topic_path,
                message_json,
                job_id=job_id
            )
            
            message_id = future.result()
            logger.info(f"Published job {job_id} to Pub/Sub with message ID {message_id}")
            return message_id
        except Exception as e:
            logger.error(f"Error publishing job {job_id} to Pub/Sub: {str(e)}")
            raise


class PubSubSubscriber:
    """Pub/Sub subscriber for processing messages from the queue."""
    
    def __init__(self, callback):
        """
        Initialize Pub/Sub subscriber.
        
        Args:
            callback: Function to call when a message is received
        """
        self.subscriber = pubsub_v1.SubscriberClient()
        self.subscription_path = Config.get_pubsub_subscription_path()
        self.topic_path = Config.get_pubsub_topic_path()
        self.callback = callback
        self._ensure_subscription_exists()
    
    def _ensure_subscription_exists(self) -> None:
        """Ensure the Pub/Sub subscription exists, create if it doesn't."""
        try:
            try:
                subscription = self.subscriber.get_subscription(
                    request={"subscription": self.subscription_path}
                )
                logger.info(f"Subscription {self.subscription_path} already exists")
            except exceptions.NotFound:
                # Subscription doesn't exist, create it
                logger.info(f"Creating subscription {self.subscription_path}")
                subscription = self.subscriber.create_subscription(
                    request={
                        "name": self.subscription_path,
                        "topic": self.topic_path
                    }
                )
                logger.info(f"Created subscription {self.subscription_path}")
        except Exception as e:
            logger.warning(f"Could not ensure subscription exists: {str(e)}")
            logger.warning("Subscription creation may require manual setup or proper IAM permissions")
    
    def start_listening(self) -> None:
        """Start listening for messages from the subscription."""
        def message_wrapper(message):
            try:
                data = json.loads(message.data.decode("utf-8"))
                logger.info(f"Received message: {data.get('job_id')}")
                self.callback(data)
                message.ack()
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                message.nack()
        
        logger.info(f"Starting to listen on subscription {self.subscription_path}")
        streaming_pull_future = self.subscriber.subscribe(
            self.subscription_path,
            callback=message_wrapper
        )
        
        try:
            streaming_pull_future.result()
        except KeyboardInterrupt:
            streaming_pull_future.cancel()
            logger.info("Stopped listening to subscription")

