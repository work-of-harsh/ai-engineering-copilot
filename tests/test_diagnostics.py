
from app.ingestion import diagnostics


def test_diagnose_test_failure(monkeypatch):
    captured = {}

    def fake_answer_question(question):
        captured["question"] = question

        return {
            "answer": "The tax rate is added directly.",
            "sources": [
                {"path": "app/payment.py"}
            ],
        }

    monkeypatch.setattr(
        diagnostics,
        "answer_question",
        fake_answer_question,
    )

    result = diagnostics.diagnose_test_failure(
        "test_calculate_total",
        "Expected 118 but received 100.18",
    )

    assert result["test_name"] == "test_calculate_total"
    assert "tax rate" in result["diagnosis"]
    assert result["sources"][0]["path"] == "app/payment.py"

    assert "Expected 118" in captured["question"]
    assert "UNTRUSTED FAILURE OUTPUT" in captured["question"]


def test_diagnose_rejects_empty_test_name():
    try:
        diagnostics.diagnose_test_failure(
            "",
            "AssertionError",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass


def test_diagnose_rejects_empty_error_output():
    try:
        diagnostics.diagnose_test_failure(
            "test_payment",
            "",
        )
        assert False, "Expected ValueError"
    except ValueError:
        pass
from app.ingestion.diagnostics import parse_structured_diagnosis


def test_parse_valid_structured_diagnosis():
    raw = """
    {
        "summary": "Tax calculation is incorrect.",
        "root_cause": "The function adds the tax rate directly.",
        "evidence": ["calculate_total returns amount + tax_rate"],
        "suggested_fix": "Return amount + (amount * tax_rate).",
        "confidence": "high",
        "limitations": ["The correction has not been tested."]
    }
    """

    result = parse_structured_diagnosis(raw)

    assert result["summary"] == "Tax calculation is incorrect."
    assert result["confidence"] == "high"
    assert len(result["evidence"]) == 1
    assert "amount * tax_rate" in result["suggested_fix"]


def test_parse_json_inside_markdown_fence():
    raw = """```json
    {
        "summary": "Payment check works.",
        "root_cause": "No issue found.",
        "evidence": [],
        "suggested_fix": "No change required.",
        "confidence": "medium",
        "limitations": []
    }
    ```"""

    result = parse_structured_diagnosis(raw)

    assert result["summary"] == "Payment check works."
    assert result["confidence"] == "medium"


def test_invalid_json_uses_fallback():
    raw = "The function appears to have a tax calculation bug."

    result = parse_structured_diagnosis(raw)

    assert result["confidence"] == "low"
    assert result["root_cause"] == raw
    assert len(result["limitations"]) > 0