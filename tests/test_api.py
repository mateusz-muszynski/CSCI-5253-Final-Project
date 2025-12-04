import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import api
from models import ProcessingMode, JobStatus


# --------------------------------------------------
# Test Client Fixture (Mocks all dependencies)
# --------------------------------------------------
@pytest.fixture
def client():
    with patch.object(api, "db", MagicMock()), \
         patch.object(api, "translation_service", MagicMock()), \
         patch.object(api, "nlp_service", MagicMock()), \
         patch.object(api, "pubsub", MagicMock()):

        return TestClient(api.app)


# --------------------------------------------------
# Root Endpoint
# --------------------------------------------------
def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert data["service"] == "Multilingual Text Intelligence Service"
    assert data["status"] == "running"
    assert "version" in data


# --------------------------------------------------
# Health Check Endpoint
# --------------------------------------------------
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


# --------------------------------------------------
# Sync Processing Path
# --------------------------------------------------
def test_sync_process_text(client):
    short_text = "hello world"

    # Force synchronous mode
    api.determine_processing_mode = MagicMock(return_value=ProcessingMode.SYNC)

    # Mock translation + nlp pipeline
    api.translation_service.detect_and_translate.return_value = ("en", short_text)
    api.nlp_service.analyze_sentiment.return_value = {"label": "POSITIVE", "score": 0.9}
    api.nlp_service.summarize.return_value = "summary"
    api.nlp_service.extract_entities.return_value = []

    response = client.post("/api/v1/process", json={"text": short_text})
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == JobStatus.COMPLETED
    assert data["mode"] == ProcessingMode.SYNC

    # DB interactions
    api.db.create_job.assert_called_once()
    api.db.save_result.assert_called_once()
    api.db.update_job_status.assert_any_call(
        data["job_id"], JobStatus.COMPLETED
    )


# --------------------------------------------------
# Async Processing Path
# --------------------------------------------------
def test_async_process_text(client):
    long_text = "x" * 5000  # artificially long to trigger async

    api.determine_processing_mode = MagicMock(return_value=ProcessingMode.ASYNC)

    response = client.post("/api/v1/process", json={"text": long_text})
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == JobStatus.PENDING
    assert data["mode"] == ProcessingMode.ASYNC

    api.pubsub.publish_job.assert_called_once()


# --------------------------------------------------
# Input Validation
# --------------------------------------------------
def test_invalid_text_rejected(client):
    response = client.post("/api/v1/process", json={"text": ""})
    assert response.status_code == 422  # Pydantic validation error


# --------------------------------------------------
# get_job_status: job not found
# --------------------------------------------------
def test_job_status_not_found(client):
    api.db.get_job.return_value = None

    response = client.get("/api/v1/jobs/unknown123")
    assert response.status_code == 404


# --------------------------------------------------
# get_job_status: completed job with results
# --------------------------------------------------
def test_job_status_completed_with_results(client):
    fake_job = {
        "status": JobStatus.COMPLETED,
        "created_at": "2025-01-01T00:00:00Z",
        "completed_at": "2025-01-01T00:00:05Z",
        "original_text": "hello",
        "detected_language": "en",
        "translated_text": "hello",
        "sentiment": {"label": "POSITIVE"},
        "summary": "short summary",
        "entities": [{"text": "Google"}],
        "metadata": {"source": "unit-test"},
    }

    api.db.get_job.return_value = fake_job

    response = client.get("/api/v1/jobs/abc123")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == JobStatus.COMPLETED
    assert data["result"]["original_text"] == "hello"
    assert data["result"]["sentiment"]["label"] == "POSITIVE"
    assert data["result"]["entities"][0]["text"] == "Google"
