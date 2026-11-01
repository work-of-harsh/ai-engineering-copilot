import json

import pytest

from app.ingestion.patch_generator import (
    generate_fix_patch,
    parse_patch_response,
    PatchGenerationError,
)


def test_parse_valid_patch_response():
    raw = json.dumps({
        "summary": "Fix percentage tax calculation.",
        "explanation": "Tax must be calculated from the amount.",
        "old_text": "return amount + tax_rate",
        "new_text": "return amount + (amount * tax_rate)",
        "confidence": "high",
        "limitations": []
    })

    result = parse_patch_response(raw)

    assert result["confidence"] == "high"
    assert result["old_text"] == "return amount + tax_rate"


def test_invalid_json_is_rejected():
    with pytest.raises(PatchGenerationError):
        parse_patch_response("This is not JSON")


def test_generate_patch_returns_proposed_content(monkeypatch):
    fake_response = {
        "summary": "Fix percentage tax calculation.",
        "explanation": "Multiply the amount by the tax rate.",
        "old_text": "return amount + tax_rate",
        "new_text": "return amount + (amount * tax_rate)",
        "confidence": "high",
        "limitations": []
    }

    def fake_answer_question(question):
        return {
            "answer": json.dumps(fake_response),
            "sources": [
                {
                    "path": "app/payment.py",
                    "start_line": 1,
                    "end_line": 5,
                    "similarity": 0.8
                }
            ]
        }

    monkeypatch.setattr(
        "app.ingestion.patch_generator.answer_question",
        fake_answer_question
    )

    result = generate_fix_patch(
        test_name="test_calculate_total_applies_percentage_tax",
        error_output="Expected 118 but got 100.18",
        file_path="app/payment.py"
    )

    assert result["file_path"] == "app/payment.py"
    assert "amount * tax_rate" in result["proposed_content"]
    assert result["confidence"] == "high"
    assert len(result["sources"]) == 1


def test_generate_patch_rejects_path_traversal():
    with pytest.raises(ValueError):
        generate_fix_patch(
            "test_example",
            "Some failure",
            "../outside.py"
        )


def test_generate_patch_rejects_non_python_file():
    with pytest.raises(ValueError):
        generate_fix_patch(
            "test_example",
            "Some failure",
            "app/payment.yaml"
        )