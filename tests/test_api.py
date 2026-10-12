
from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ask_endpoint_returns_answer_and_sources(monkeypatch):
    def fake_answer_question(question):
        return {
            "question": question,
            "answer": "The tax calculation is incorrect.",
            "sources": [{
                "path": "app/payment.py",
                "start_line": 1,
                "end_line": 2,
                "similarity": 0.91,
            }],
        }

    monkeypatch.setattr(
        main, "answer_question", fake_answer_question
    )

    response = client.post(
        "/ask",
        json={
            "message": "Why is tax calculation incorrect?"
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "The tax calculation is incorrect."
    assert data["sources"][0]["path"] == "app/payment.py"


def test_ask_endpoint_rejects_empty_message():
    response = client.post(
        "/ask",
        json={"message": ""},
    )

    assert response.status_code == 422
