#
import pytest
from unittest.mock import patch, MagicMock
from nlp_service import NLPService

# ---------------------------
# Fixtures
# ---------------------------

@pytest.fixture
def nlp_service():
    return NLPService()

# ---------------------------
# Sentiment Tests
# ---------------------------

@patch("nlp_service.pipeline")
def test_analyze_sentiment_positive(mock_pipeline):
    # Mock the sentiment-analysis pipeline
    mock_sentiment = MagicMock()
    mock_sentiment.return_value = [{"label": "POSITIVE", "score": 0.95}]
    mock_pipeline.return_value = mock_sentiment

    nlp = NLPService()
    result = nlp.analyze_sentiment("I love this!")
    
    assert result["label"] == "positive"
    assert result["score"] == 0.95


@patch("nlp_service.pipeline")
def test_analyze_sentiment_empty_text(mock_pipeline):
    # Pipeline should not fail on empty text
    mock_pipeline.return_value = MagicMock()
    nlp = NLPService()
    result = nlp.analyze_sentiment("")
    assert result["label"] == "neutral"
    assert result["score"] == 0.5

# ---------------------------
# Summarization Tests
# ---------------------------

@patch("nlp_service.pipeline")
def test_summarize_text(mock_pipeline):
    mock_summarizer = MagicMock()
    mock_summarizer.return_value = [{"summary_text": "This is a summary"}]
    mock_pipeline.return_value = mock_summarizer

    nlp = NLPService()
    summary = nlp.summarize("Some long text to summarize")
    assert summary == "This is a summary"


@patch("nlp_service.pipeline")
def test_summarize_empty_text(mock_pipeline):
    mock_pipeline.return_value = MagicMock()
    nlp = NLPService()
    summary = nlp.summarize("")
    assert summary == ""

# ---------------------------
# NER Tests
# ---------------------------

@patch("nlp_service.pipeline")
def test_extract_entities(mock_pipeline):
    mock_ner = MagicMock()
    mock_ner.return_value = [
        {"word": "Alice", "entity_group": "PER", "start": 0, "end": 5, "score": 0.99}
    ]
    mock_pipeline.return_value = mock_ner

    nlp = NLPService()
    entities = nlp.extract_entities("Alice went to Paris.")
    
    assert len(entities) == 1
    assert entities[0]["text"] == "Alice"
    assert entities[0]["label"] == "PER"
    assert entities[0]["start"] == 0
    assert entities[0]["end"] == 5
    assert entities[0]["score"] == 0.99

@patch("nlp_service.pipeline")
def test_extract_entities_empty_text(mock_pipeline):
    mock_pipeline.return_value = MagicMock()
    nlp = NLPService()
    entities = nlp.extract_entities("")
    assert entities == []
