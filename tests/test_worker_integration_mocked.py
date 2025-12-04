import pytest
from unittest.mock import patch, MagicMock
from worker import WorkerService
from models import JobStatus, ProcessingResult

@pytest.fixture
def mock_firestore():
    with patch("database.firestore.Client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        yield mock_db

@pytest.fixture
def mock_pubsub():
    with patch("pubsub_client.pubsub_v1.PublisherClient") as mock_pub:
        mock_publisher = MagicMock()
        mock_pub.return_value = mock_publisher
        yield mock_publisher

@pytest.fixture
def worker(mock_firestore, mock_pubsub):
    return WorkerService()

def test_process_job_success(worker):
    message = {
        "job_id": "job-123",
        "text": "Hello world",
        "metadata": {"source": "test"}
    }
    # Patch NLPService methods
    with patch("nlp_service.NLPService.analyze_sentiment", return_value={"label":"positive","score":0.9}), \
         patch("nlp_service.NLPService.summarize", return_value="Summary"), \
         patch("nlp_service.NLPService.extract_entities", return_value=[{"text":"world","label":"MISC","start":6,"end":11}]):
        worker.process_job(message)
    
    # Assert Firestore update called
    assert worker.db.collection().document().update.called
