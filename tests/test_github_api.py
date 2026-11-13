
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.github_client import GitHubAPIError


client = TestClient(app)


def test_create_pull_request_success(monkeypatch):
    def fake_create_pull_request(
        title,
        body,
        head,
        base,
    ):
        return {
            "success": True,
            "number": 15,
            "title": title,
            "url": "https://github.com/work-of-harsh/ai-engineering-copilot/pull/15",
            "state": "open",
            "head": head,
            "base": base,
        }

    monkeypatch.setattr(
        "app.main.create_pull_request",
        fake_create_pull_request,
    )

    response = client.post(
        "/create-pull-request",
        json={
            "title": "Add GitHub PR automation",
            "body": "Automates pull request creation.",
            "head": "feature/github-pr-automation",
            "base": "master",
        },
    )

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["number"] == 15


def test_create_pull_request_api_error(monkeypatch):
    def fake_create_pull_request(**kwargs):
        raise GitHubAPIError("GitHub API failed")

    monkeypatch.setattr(
        "app.main.create_pull_request",
        fake_create_pull_request,
    )

    response = client.post(
        "/create-pull-request",
        json={
            "title": "Test PR",
            "body": "Test",
            "head": "feature/test",
            "base": "master",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "GitHub API failed"


def test_create_pull_request_invalid_request():
    response = client.post(
        "/create-pull-request",
        json={
            "title": "",
            "body": "Test",
            "head": "feature/test",
            "base": "master",
        },
    )

    assert response.status_code == 422
