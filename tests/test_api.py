
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

def test_diagnose_endpoint(monkeypatch):
    from app import main

    def fake_diagnosis(test_name, error_output):
        return {
            "test_name": test_name,
            "diagnosis": "Tax calculation is incorrect.",
            "sources": [{"path": "app/payment.py"}],
        }

    monkeypatch.setattr(
        main,
        "diagnose_test_failure",
        fake_diagnosis,
    )

    response = client.post(
        "/diagnose",
        json={
            "test_name": "test_calculate_total",
            "error_output": "Expected 118 but received 100.18",
        },
    )

    assert response.status_code == 200
    assert response.json()["test_name"] == "test_calculate_total"
    assert response.json()["sources"][0]["path"] == "app/payment.py"
    
def test_validate_fix_endpoint(monkeypatch):
    from app import main

    def fake_validation(file_path, new_content):
        return {
            "passed": True,
            "return_code": 0,
            "stdout": "3 passed",
            "stderr": "",
            "file_validated": file_path,
            "timed_out": False
        }

    monkeypatch.setattr(
        main,
        "run_fix_validation",
        fake_validation
    )

    response = client.post(
        "/validate-fix",
        json={
            "file_path": "app/payment.py",
            "new_content": "def calculate_total():\n    return 118"
        }
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    
def test_validate_fix_endpoint(monkeypatch):
    from app import main

    def fake_validation(file_path, new_content):
        return {
            "passed": True,
            "return_code": 0,
            "stdout": "3 passed",
            "stderr": "",
            "file_validated": file_path,
            "timed_out": False
        }

    monkeypatch.setattr(
        main,
        "run_fix_validation",
        fake_validation
    )

    response = client.post(
        "/validate-fix",
        json={
            "file_path": "app/payment.py",
            "new_content": "def calculate_total():\n    return 118"
        }
    )

    assert response.status_code == 200
    assert response.json()["passed"] is True
    
def test_generate_fix_endpoint(monkeypatch):
    from app import main

    def fake_generate_patch(test_name, error_output, file_path):
        return {
            "file_path": file_path,
            "summary": "Fix percentage tax.",
            "explanation": "Multiply the amount by the tax rate.",
            "old_text": "return amount + tax_rate",
            "new_text": "return amount + (amount * tax_rate)",
            "confidence": "high",
            "limitations": [],
            "proposed_content": "def calculate_total(amount, tax_rate):\n    return amount + (amount * tax_rate)",
            "sources": []
        }

    monkeypatch.setattr(
        main,
        "generate_fix_patch",
        fake_generate_patch
    )

    response = client.post(
        "/generate-fix",
        json={
            "test_name": "test_calculate_total_applies_percentage_tax",
            "error_output": "Expected 118 but got 100.18",
            "file_path": "app/payment.py"
        }
    )

    assert response.status_code == 200
    assert response.json()["confidence"] == "high"


from fastapi.testclient import TestClient
from app.main import app
import app.main as main_module


def test_chat_blocks_llm_identity(monkeypatch):
    def should_not_be_called(prompt):
        raise AssertionError(
            "AI API should not be called for blocked questions"
        )

    monkeypatch.setattr(
        main_module,
        "generate_response",
        should_not_be_called,
    )

    client = TestClient(app)

    response = client.post(
        "/chat",
        json={
            "message": "Which LLM model powers you?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "don't disclose" in data["answer"].lower()
    assert data["model"] == "AI Engineering Copilot"
    
    

def test_chat_blocks_semantic_match(monkeypatch):
    from app import main

    def fake_semantic_check(message):
        return ("model_identity", 0.91)

    def should_not_be_called(prompt):
        raise AssertionError(
            "AI API should not be called for restricted questions"
        )

    monkeypatch.setattr(
        main,
        "check_semantic_guardrail",
        fake_semantic_check,
    )

    monkeypatch.setattr(
        main,
        "generate_response",
        should_not_be_called,
    )

    response = client.post(
        "/chat",
        json={"message": "Who created the intelligence behind you?"},
    )

    assert response.status_code == 200
    assert "don't disclose" in response.json()["answer"].lower()


def test_chat_fails_closed_when_semantic_check_fails(monkeypatch):
    from app import main

    def failing_semantic_check(message):
        raise RuntimeError("Simulated embedding failure")

    monkeypatch.setattr(
        main,
        "check_semantic_guardrail",
        failing_semantic_check,
    )

    response = client.post(
        "/chat",
        json={"message": "Explain Python decorators."},
    )

    assert response.status_code == 503
    assert "security verification" in response.json()["detail"].lower()
