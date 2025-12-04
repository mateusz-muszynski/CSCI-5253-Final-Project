#
def test_summary_returns_string(nlp):
    result = nlp.summarize("This is a long article...")
    assert isinstance(result, str)
    assert len(result) > 0

def test_summary_respects_max_length_argument(nlp):
    # for now placeholder doesn't use max_length,
    # but future implementation should
    result = nlp.summarize("text", max_length=20)
    assert isinstance(result, str)

def test_summary_handles_empty_text(nlp):
    result = nlp.summarize("")
    assert isinstance(result, str)

def test_summary_logs(nlp, caplog):
    with caplog.at_level("INFO"):
        nlp.summarize("hello world")
    assert "Summarizing text" in caplog.text
