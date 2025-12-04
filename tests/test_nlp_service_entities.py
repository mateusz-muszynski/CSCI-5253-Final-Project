def test_entities_output_structure(nlp):
    text = "Barack Obama visited Paris."
    result = nlp.extract_entities(text)

    assert isinstance(result, list)
    assert len(result) > 0

    ent = result[0]
    assert "text" in ent
    assert "label" in ent
    assert "start" in ent
    assert "end" in ent

def test_entities_indices_are_ints(nlp):
    result = nlp.extract_entities("hello world")
    ent = result[0]
    assert isinstance(ent["start"], int)
    assert isinstance(ent["end"], int)

def test_entities_handles_empty_text(nlp):
    result = nlp.extract_entities("")
    assert isinstance(result, list)

def test_entities_logs(nlp, caplog):
    with caplog.at_level("INFO"):
        nlp.extract_entities("hello")
    assert "Extracting entities" in caplog.text
