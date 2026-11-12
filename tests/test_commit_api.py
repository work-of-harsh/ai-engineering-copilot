
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.git_manager import GitOperationError


client = TestClient(app)


def test_commit_fix_success(monkeypatch):
    captured = {}

    def fake_apply_validated_patch(
        file_path,
        new_content,
        commit_message,
    ):
        captured["file_path"] = file_path
        captured["new_content"] = new_content
        captured["commit_message"] = commit_message

        return {
            "success": True,
            "stage": "committed",
            "branch": "feature/git-pr-automation",
            "file": file_path,
            "commit_hash": "abc123",
            "commit_message": commit_message,
            "working_tree_clean": True,
            "validation": {"passed": True},
        }

    monkeypatch.setattr(
        "app.main.apply_validated_patch",
        fake_apply_validated_patch,
    )

    payload = {
        "file_path": "app/payment.py",
        "new_content": "def calculate_total(amount, tax_rate):\n    return amount * (1 + tax_rate)\n",
        "commit_message": "Fix payment tax calculation",
    }

    response = client.post("/commit-fix", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["commit_hash"] == "abc123"
    assert captured == payload


def test_commit_fix_maps_value_error_to_400(monkeypatch):
    def fake_apply_validated_patch(**kwargs):
        raise ValueError("Invalid patch")

    monkeypatch.setattr(
        "app.main.apply_validated_patch",
        fake_apply_validated_patch,
    )

    response = client.post(
        "/commit-fix",
        json={
            "file_path": "app/payment.py",
            "new_content": "updated content",
            "commit_message": "Fix payment",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid patch"


def test_commit_fix_maps_missing_file_to_404(monkeypatch):
    def fake_apply_validated_patch(**kwargs):
        raise FileNotFoundError("Target file does not exist")

    monkeypatch.setattr(
        "app.main.apply_validated_patch",
        fake_apply_validated_patch,
    )

    response = client.post(
        "/commit-fix",
        json={
            "file_path": "app/missing.py",
            "new_content": "updated content",
            "commit_message": "Fix missing file",
        },
    )

    assert response.status_code == 404


def test_commit_fix_maps_git_error_to_409(monkeypatch):
    def fake_apply_validated_patch(**kwargs):
        raise GitOperationError("Working tree is not clean")

    monkeypatch.setattr(
        "app.main.apply_validated_patch",
        fake_apply_validated_patch,
    )

    response = client.post(
        "/commit-fix",
        json={
            "file_path": "app/payment.py",
            "new_content": "updated content",
            "commit_message": "Fix payment",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Working tree is not clean"
