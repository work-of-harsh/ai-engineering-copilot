
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
