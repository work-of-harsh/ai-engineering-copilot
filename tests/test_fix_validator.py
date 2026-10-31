import pytest

from app.ingestion.fix_validator import validate_fix


def test_rejects_path_traversal():
    with pytest.raises(ValueError):
        validate_fix("../outside.py", "malicious content")


def test_rejects_absolute_path():
    with pytest.raises(ValueError):
        validate_fix("C:/Windows/test.py", "malicious content")


def test_rejects_unsupported_file_type():
    with pytest.raises(ValueError):
        validate_fix("app/payment.exe", "content")


def test_original_file_is_not_modified():
    from pathlib import Path

    original = Path("data/sample_repo/app/payment.py")
    before = original.read_text(encoding="utf-8")

    proposed = "def calculate_total(amount, tax_rate):\n    return 999\n"

    try:
        validate_fix("app/payment.py", proposed)
    finally:
        after = original.read_text(encoding="utf-8")

    assert before == after