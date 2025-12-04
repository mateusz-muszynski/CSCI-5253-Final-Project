import pytest
from unittest.mock import MagicMock, patch
from worker import WorkerService
from models import JobStatus


@pytest.fixture
def mock_services():
    """Patch all external services used by WorkerService."""
    with patch("worker.Config.validate") as mock_validate, \
         patch("worker.Database") as mock_db_cls, \
         patch("worker.TranslationService") as mock_translation_cls, \
         patch("worker.NLPService") as mock_nlp_cls, \
         patch("worker.ProcessingResult") as mock_processing_result_cls:

        mock_db = MagicMock()
        mock_translation = MagicMock()
        mock_nlp = MagicMock()

        mock_db_cls.return_value = mock_db
        mock_translation_cls.return_value = mock_translation
        mock_nlp_cls.return_value = mock_nlp

        yield {
            "db": mock_db,
            "translation": mock_translation,
            "nlp": mock_nlp,
            "validate": mock_validate,
            "processing_result": mock_processing_result_cls,
        }


def test_worker_initialization_success(mock_services):
    worker = WorkerService()

    mock_services["validate"].assert_called_once()
    assert worker.db is mock_services["db"]
    assert worker.translation_service is mock_services["translation"]
    assert worker.nlp_service is mock_services["nlp"]


def test_worker_initialization_failure():
    with patch("worker.Config.validate", side_effect=Exception("config error")):
        with pytest.raises(Exception):
            WorkerService()


def test_process_job_happy_path(mock_services):
    worker = WorkerService()

    # Mock translation
    mock_services["translation"].detect_and_translate.return_value = (
        "en",
        "translated text",
    )

    # Mock NLP
    mock_services["nlp"].analyze_sentiment.return_value = {"score": 0.9}
    mock_services["nlp"].summarize.return_value = "summary"
    mock_services["nlp"].extract_entities.return_value = [{"type": "ORG", "name": "OpenAI"}]

    message = {
        "job_id": "123",
        "text": "hello world",
        "metadata": {"source": "test"},
    }

    worker.process_job(message)

    # Assertions
    db = mock_services["db"]
    translation = mock_services["translation"]
    nlp = mock_services["nlp"]

    db.update_job_status.assert_any_call("123", JobStatus.PROCESSING)
    translation.detect_and_translate.assert_called_once_with("hello world")

    nlp.analyze_sentiment.assert_called_once_with("translated text")
    nlp.summarize.assert_called_once_with("translated text")
    nlp.extract_entities.assert_called_once_with("translated text")

    # ProcessingResult should be constructed
    mock_services["processing_result"].assert_called_once()

    # Final status update
    db.update_job_status.assert_any_call("123", JobStatus.COMPLETED)


def test_process_job_invalid_input(mock_services):
    worker = WorkerService()

    # Missing job_id or text → return early
    worker.process_job({"job_id": None, "text": "abc"})
    worker.process_job({"job_id": "123", "text": None})

    # Database should NOT be called
    mock_services["db"].update_job_status.assert_not_called()


def test_process_job_failure(mock_services):
    worker = WorkerService()

    # Cause translation to fail
    mock_services["translation"].detect_and_translate.side_effect = Exception("boom")

    message = {"job_id": "999", "text": "test"}

    with pytest.raises(Exception):
        worker.process_job(message)

    mock_services["db"].update_job_status.assert_any_call(
        "999",
        JobStatus.FAILED,
        error="boom"
    )
