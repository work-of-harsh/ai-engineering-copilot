
from app.ingestion import qa


def test_answer_question_uses_retrieved_context(monkeypatch):
    def fake_search_repository(question, top_k=3):
        assert question == "Why is tax wrong?"
        assert top_k == 3

        return [{
            "path": "app/payment.py",
            "start_line": 1,
            "end_line": 2,
            "content": "return amount + tax_rate",
            "score": 0.91,
        }]

    def fake_generate_response(prompt):
        assert "return amount + tax_rate" in prompt
        assert "app/payment.py" in prompt
        assert "Why is tax wrong?" in prompt
        return "The function adds the rate directly."

    monkeypatch.setattr(
        qa, "search_repository", fake_search_repository
    )
    monkeypatch.setattr(
        qa, "generate_response", fake_generate_response
    )

    result = qa.answer_question("Why is tax wrong?")

    assert result["answer"] == (
        "The function adds the rate directly."
    )
    assert result["sources"][0]["path"] == "app/payment.py"
    assert result["sources"][0]["start_line"] == 1
    assert result["sources"][0]["similarity"] == 0.91



def test_answer_question_handles_no_results(monkeypatch):
    monkeypatch.setattr(
        qa, "search_repository", lambda question, top_k=3: []
    )

    result = qa.answer_question("Question with no matching context")

    assert result["sources"] == []
    assert "could not find relevant" in result["answer"].lower()


def test_answer_question_rejects_low_similarity(monkeypatch):
    monkeypatch.setattr(
        qa,
        "search_repository",
        lambda question, top_k=3: [{
            "path": "app/payment.py",
            "start_line": 1,
            "end_line": 2,
            "content": "return amount + tax_rate",
            "score": 0.10,
        }],
    )

    result = qa.answer_question("Question unrelated to payments")

    assert result["sources"] == []
    assert "could not find sufficiently relevant" in result["answer"].lower()