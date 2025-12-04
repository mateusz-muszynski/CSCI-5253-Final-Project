import pytest
from datetime import datetime
from worker import WorkerService
from models import JobStatus, ProcessingResult
from nlp_service import NLPService
from translation_service import TranslationService
from test_double_firestore import FirestoreTestDouble  # our test double
from unittest.mock import patch


@pytest.fixture
def firestore_double():
    """Provide a fresh in-memory Firestore test double for each test."""
    db = FirestoreTestDouble()
    yield db
    db.clear()


@pytest.fixture
def mock_nlp_service():
    """Return a mocked NLPService."""
    nlp = NLPService()
    nlp.analyze_sentiment = lambda text: {"label": "positive", "score": 0.9}
    nlp.summarize = lambda text, max_length=None: "This is a summary"
    nlp.extract_entities = lambda text: [{"text": "Alice", "label": "PERSON", "start": 0, "end": 5}]
    return nlp


@pytest.fixture
def mock_translation_service():
    """Return a mocked TranslationService."""
    ts = TranslationService()
    ts.detect_and_translate = lambda text: ("en", text)
    return ts


@pytest.fixture
def worker_service(firestore_double, mock_nlp_service, mock_translation_service):
    """Return a WorkerService instance patched to use mocks."""
    with patch("worker.Database", return_value=firestore_double), \
         patch("worker.NLPService", return_value=mock_nlp_service), \
         patch("worker.TranslationService", return_value=mock_translation_service):
        service = WorkerService()
        yield service


def test_process_job_success(worker_service, firestore_double):
    """Test that a job is processed successfully end-to-end."""
    job_id = "job-123"
    text = "Hello world"
    metadata = {"source": "unit-test"}

    # Create job in test double (simulates API creating it)
    firestore_double.create_job(job_id, text, "async", metadata)

    # Process the job
    worker_service.process_job({"job_id": job_id, "text": text, "metadata": metadata})

    # Verify job updated correctly
    job = firestore_double.get_job(job_id)
    assert job is not None
    assert job["status"] == JobStatus.COMPLETED.value
    assert job["sentiment"] == {"label": "positive", "score": 0.9}
    assert job["summary"] == "This is a summary"
    assert job["entities"] == [{"text": "Alice", "label": "PERSON", "start": 0, "end": 5}]
    assert job["completed_at"] is not None


def test_process_job_missing_fields(worker_service, firestore_double, caplog):
    """Test behavior when message is missing job_id or text."""
    caplog.set_level("ERROR")

    # Missing job_id
    worker_service.process_job({"text": "Hello"})
    assert "Invalid message data" in caplog.text

    # Missing text
    worker_service.process_job({"job_id": "job-456"})
    assert "Invalid message data" in caplog.text


def test_process_job_failure(worker_service, firestore_double, mock_nlp_service):
    """Test that an exception in NLP service sets status to FAILED."""
    job_id = "job-789"
    text = "Failing text"
    firestore_double.create_job(job_id, text, "async")

    # Patch NLPService to raise exception
    def fail_sentiment(text):
        raise ValueError("NLP model failure")
    mock_nlp_service.analyze_sentiment = fail_sentiment

    with pytest.raises(ValueError):
        worker_service.process_job({"job_id": job_id, "text": text})

    job = firestore_double.get_job(job_id)
    assert job["status"] == JobStatus.FAILED.value
    assert "NLP model failure" in job["error"]
