def test_sentiment_output_structure(nlp):
    text = "I love this!"
    result = nlp.analyze_sentiment(text)

    assert isinstance(result, dict)
    assert "label" in result
    assert result["label"] in ["positive", "negative", "neutral", "neutral"] or isinstance(result["label"], str)
    assert "score" in result
    assert isinstance(result["score"], float)

def test_sentiment_handles_empty_string(nlp):
    result = nlp.analyze_sentiment("")
    assert isinstance(result, dict)
    assert "label" in result
    assert "score" in result

def test_sentiment_raises_on_non_string_input(nlp):
    import pytest
    with pytest.raises(Exception):
        nlp.analyze_sentiment(123)  # type: ignore

def test_sentiment_logs(nlp, caplog):
    with caplog.at_level("INFO"):
        nlp.analyze_sentiment("hello")
    assert "Analyzing sentiment" in caplog.text
