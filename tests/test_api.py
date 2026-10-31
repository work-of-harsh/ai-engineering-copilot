
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
