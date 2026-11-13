from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def test_chat_ui_page_loads():
    response = client.get("/chat-ui")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'fetch("/chat"' in response.text


def test_chat_endpoint_returns_answer(monkeypatch):
    def fake_generate_response(message):
        return "RAG combines retrieval with generation."

    monkeypatch.setattr(
        main,
        "generate_response",
        fake_generate_response
    )

    monkeypatch.setenv("GEMINI_MODEL", "test-model")

    response = client.post(
        "/chat",
        json={"message": "Explain RAG"}
    )

    assert response.status_code == 200
    assert response.json()["answer"] == (
        "RAG combines retrieval with generation."
    )
    assert response.json()["model"] == "test-model"