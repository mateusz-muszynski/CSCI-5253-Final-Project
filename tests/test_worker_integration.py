#
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from worker import WorkerService
from models import JobStatus, ProcessingResult


@pytest.fixture
def fixed_time():
    """Freeze time for deterministic tests."""
    with patch("worker.datetime") as mock_dt:
        mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
        yield mock_dt


@pytest.fixture
def worker_with_mocks():
    """Create a WorkerService with all dependent services mocked."""
    with patch("worker.Database") as MockDB, \
         patch("worker.TranslationService") as MockTrans, \
         patch("worker.NLPService") as MockNLP:

        db = MockDB.return_value
        trans = MockTrans.return_value
        nlp = MockNLP.return_value

        # Initialize worker
        worker = WorkerService()

        yield worker, db, trans, nlp


# ---------------------------------------------------------------------
#  Test successful worker job processing
# ---------------------------------------------------------------------

def test_worker_processes_job_success(worker_with_mocks, fixed_time):
    worker, db, trans, nlp = worker_with_mocks

    # Fake inputs
    message = {
        "job_id": "abc123",
        "text": "Bonjour, je suis très content!",
        "metadata": {"source": "test"}
    }

    # Mock translation
    trans.detect_and_translate.return_value = ("fr", "Hello, I am very happy!")

    # Mock NLP tools
    nlp.analyze_sentiment.return_value = {"sentiment": "positive", "score": 0.94}
    nlp.summarize.return_value = "User is very happy."
    nlp.extract_entities.return_value = [{"text": "User", "type": "PERSON"}]

    worker.process_job(message)

    # --------------------
    # Verify DB writes
    # --------------------

    # 1. Status set to PROCESSING
    db.update_job_status.assert_any_call("abc123", JobStatus.PROCESSING)

    # 2. Translation called correctly
    trans.detect_and_translate.assert_called_once_with(message["text"])

    # 3. NLP called on translated text
    nlp.analyze_sentiment.assert_called_once_with("Hello, I am very happy!")
    nlp.summarize.assert_called_once_with("Hello, I am very happy!")
    nlp.extract_entities.assert_called_once_with("Hello, I am very happy!")

    # 4. Result object saved
    save_call = db.save_result.call_args[0]
    _, result = save_call

    assert isinstance(result, ProcessingResult)
    assert result.job_id == "abc123"
    assert result.original_text == "Bonjour, je suis très content!"
    assert result.detected_language == "fr"
    assert result.translated_text == "Hello, I am very happy!"
    assert result.sentiment["sentiment"] == "positive"
    assert result.summary == "User is very happy."
    assert result.entities == [{"text": "User", "type": "PERSON"}]
    assert result.metadata == {"source": "test"}

    # 5. Status eventually set to COMPLETED
    db.update_job_status.assert_any_call("abc123", JobStatus.COMPLETED)


# ---------------------------------------------------------------------
#  Test worker error handling path
# ---------------------------------------------------------------------

def test_worker_processes_job_failure(worker_with_mocks):
    worker, db, trans, nlp = worker_with_mocks

    # Simulate failure during NLP
    trans.detect_and_translate.return_value = ("fr", "Hello")
    nlp.analyze_sentiment.side_effect = RuntimeError("NLP crashed")

    message = {"job_id": "xyz789", "text": "test"}

    with pytest.raises(RuntimeError):
        worker.process_job(message)

    # Ensure failure state saved to DB
    db.update_job_status.assert_any_call("xyz789", JobStatus.FAILED, error="NLP crashed")


# ---------------------------------------------------------------------
#  Test worker ignores invalid message (missing fields)
# ---------------------------------------------------------------------

def test_worker_invalid_message_skipped(worker_with_mocks):
    worker, db, trans, nlp = worker_with_mocks

    # Missing job_id and text
    message = {"not_job": "zzz"}

    # Should NOT raise
    worker.process_job(message)

    # Ensure nothing was called
    db.update_job_status.assert_not_called()
    trans.detect_and_translate.assert_not_called()
    nlp.analyze_sentiment.assert_not_called()
