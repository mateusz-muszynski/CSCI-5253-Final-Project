import json
import pytest
from unittest.mock import MagicMock, patch, call
from google.api_core.exceptions import NotFound

from pubsub_client import PubSubClient, PubSubSubscriber


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def mock_config():
    """Mock Config values."""
    with patch("pubsub_client.Config") as MockConfig:
        MockConfig.PROJECT_ID = "test-project"
        MockConfig.PUBSUB_TOPIC_NAME = "test-topic"
        MockConfig.PUBSUB_SUBSCRIPTION_NAME = "test-sub"
        MockConfig.get_pubsub_topic_path.return_value = (
            "projects/test-project/topics/test-topic"
        )
        MockConfig.get_pubsub_subscription_path.return_value = (
            "projects/test-project/subscriptions/test-sub"
        )
        yield MockConfig


# ---------------------------------------------------------------------
# Tests for PubSubClient (Publisher)
# ---------------------------------------------------------------------

@patch("pubsub_client.pubsub_v1.PublisherClient")
def test_pubsubclient_initializes_and_creates_topic(mock_publisher, mock_config):
    """Ensure PubSubClient creates the topic if missing."""
    mock_publisher_instance = mock_publisher.return_value

    # Simulate topic NOT found -> raise NotFound
    mock_publisher_instance.get_topic.side_effect = NotFound("not found")

    # Mock topic creation
    mock_publisher_instance.create_topic.return_value = {"name": "created"}

    client = PubSubClient()

    mock_publisher_instance.get_topic.assert_called_once()
    mock_publisher_instance.create_topic.assert_called_once()


@patch("pubsub_client.pubsub_v1.PublisherClient")
def test_pubsubclient_initializes_when_topic_exists(mock_publisher, mock_config):
    """If topic exists, no creation should happen."""
    mock_publisher_instance = mock_publisher.return_value

    # Existing topic
    mock_publisher_instance.get_topic.return_value = {"name": "existing"}

    client = PubSubClient()

    mock_publisher_instance.get_topic.assert_called_once()
    mock_publisher_instance.create_topic.assert_not_called()


@patch("pubsub_client.pubsub_v1.PublisherClient")
def test_publish_job_success(mock_publisher, mock_config):
    """Test successful publishing of a job."""
    mock_publisher_instance = mock_publisher.return_value
    mock_future = MagicMock()
    mock_future.result.return_value = "message-123"

    mock_publisher_instance.publish.return_value = mock_future

    client = PubSubClient()
    msg_id = client.publish_job("job1", "Hello world", metadata={"x": 1})

    assert msg_id == "message-123"
    mock_publisher_instance.publish.assert_called_once()

    # Validate payload sent to Pub/Sub
    sent_data = mock_publisher_instance.publish.call_args[0][1]
    decoded = json.loads(sent_data.decode("utf-8"))
    assert decoded["job_id"] == "job1"
    assert decoded["text"] == "Hello world"
    assert decoded["metadata"] == {"x": 1}


@patch("pubsub_client.pubsub_v1.PublisherClient")
def test_publish_job_failure(mock_publisher, mock_config):
    """Test error handling when publish fails."""
    mock_publisher_instance = mock_publisher.return_value
    mock_publisher_instance.publish.side_effect = RuntimeError("publish err")

    client = PubSubClient()

    with pytest.raises(RuntimeError):
        client.publish_job("job1", "text")


# ---------------------------------------------------------------------
# Tests for PubSubSubscriber
# ---------------------------------------------------------------------

@patch("pubsub_client.pubsub_v1.SubscriberClient")
def test_subscriber_initializes_and_creates_subscription(mock_subscriber, mock_config):
    """If subscription does not exist, ensure creation."""
    mock_subscriber_instance = mock_subscriber.return_value

    # Simulate not found on subscription
    mock_subscriber_instance.get_subscription.side_effect = NotFound("not found")
    mock_subscriber_instance.create_subscription.return_value = {"name": "created"}

    callback = MagicMock()
    subscriber = PubSubSubscriber(callback)

    mock_subscriber_instance.get_subscription.assert_called_once()
    mock_subscriber_instance.create_subscription.assert_called_once()


@patch("pubsub_client.pubsub_v1.SubscriberClient")
def test_subscriber_initializes_when_subscription_exists(mock_subscriber, mock_config):
    """If subscription exists, should not create one."""
    mock_subscriber_instance = mock_subscriber.return_value
    mock_subscriber_instance.get_subscription.return_value = {"name": "existing"}

    callback = MagicMock()
    subscriber = PubSubSubscriber(callback)

    mock_subscriber_instance.get_subscription.assert_called_once()
    mock_subscriber_instance.create_subscription.assert_not_called()


@patch("pubsub_client.pubsub_v1.SubscriberClient")
def test_message_callback_ack(mock_subscriber, mock_config):
    """Test that valid message calls callback and acks."""
    mock_subscriber_instance = mock_subscriber.return_value

    # Mock streaming future
    mock_stream_future = MagicMock()
    mock_subscriber_instance.subscribe.return_value = mock_stream_future

    # Create subscriber
    received_data = {}
    def callback(data):
        received_data.update(data)

    subscriber = PubSubSubscriber(callback)

    # Pull out the wrapper function passed to subscribe()
    wrapper = mock_subscriber_instance.subscribe.call_args[1]["callback"]

    # Fake a Pub/Sub message
    mock_message = MagicMock()
    mock_message.data = json.dumps({"job_id": "123", "text": "hello"}).encode("utf-8")

    # Execute callback
    wrapper(mock_message)

    assert received_data["job_id"] == "123"
    assert received_data["text"] == "hello"
    mock_message.ack.assert_called_once()


@patch("pubsub_client.pubsub_v1.SubscriberClient")
def test_message_callback_nack_on_error(mock_subscriber, mock_config):
    """Test that decoding failure triggers nack()."""
    mock_subscriber_instance = mock_subscriber.return_value
    mock_stream_future = MagicMock()
    mock_subscriber_instance.subscribe.return_value = mock_stream_future

    def callback(_):
        raise RuntimeError("bad callback")

    subscriber = PubSubSubscriber(callback)
    wrapper = mock_subscriber_instance.subscribe.call_args[1]["callback"]

    # Bad JSON -> should error
    mock_message = MagicMock()
    mock_message.data = b"not-json"

    wrapper(mock_message)

    mock_message.nack.assert_called_once()
