import pytest

from slothdesk.ai_engine import _clean_json


def test_clean_json_accepts_valid_model_response():
    result = _clean_json('{"category":"Documents","suggested_name":"meeting-notes.pdf"}')
    assert result == {"category": "Documents", "suggested_name": "meeting-notes.pdf"}


def test_clean_json_rejects_missing_filename():
    with pytest.raises(ValueError):
        _clean_json('{"category":"Documents"}')


def test_clean_json_normalizes_unknown_category():
    result = _clean_json('{"category":"DefinitelyNotAFileType","suggested_name":"notes.txt"}')
    assert result["category"] == "Other"


def test_clean_json_accepts_markdown_wrapped_json():
    fence = chr(96) * 3
    result = _clean_json(f'{fence}json\n{{"category":"Code","suggested_name":"app.py"}}\n{fence}')
    assert result["suggested_name"] == "app.py"
