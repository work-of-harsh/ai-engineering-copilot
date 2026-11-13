
import httpx
import pytest

from app.integrations.github_client import (
    create_pull_request,
    GitHubAPIError,
)


def test_create_pull_request_success(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")
    monkeypatch.setenv("GITHUB_BASE_BRANCH", "master")

    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json

        return httpx.Response(
            201,
            json={
                "number": 12,
                "title": "Add GitHub PR automation",
                "html_url": "https://github.com/work-of-harsh/ai-engineering-copilot/pull/12",
                "state": "open",
                "head": {"ref": "feature/github-pr-automation"},
                "base": {"ref": "master"},
            },
        )

    monkeypatch.setattr(
        "app.integrations.github_client.httpx.post",
        fake_post,
    )

    result = create_pull_request(
        title="Add GitHub PR automation",
        body="Adds automated pull request creation.",
        head="feature/github-pr-automation",
    )

    assert result["success"] is True
    assert result["number"] == 12
    assert result["state"] == "open"
    assert result["head"] == "feature/github-pr-automation"
    assert result["base"] == "master"

    assert captured["json"]["title"] == "Add GitHub PR automation"
    assert captured["json"]["head"] == "feature/github-pr-automation"


def test_missing_token_raises_error(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")

    with pytest.raises(GitHubAPIError):
        create_pull_request(
            title="Test PR",
            body="Test",
            head="feature/test",
        )


def test_empty_title_is_rejected(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")

    with pytest.raises(ValueError):
        create_pull_request(
            title=" ",
            body="Test",
            head="feature/test",
        )


def test_same_head_and_base_are_rejected(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")

    with pytest.raises(ValueError):
        create_pull_request(
            title="Test PR",
            body="Test",
            head="master",
            base="master",
        )


def test_github_api_error_is_handled(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")

    def fake_post(url, headers, json, timeout):
        return httpx.Response(
            422,
            json={"message": "A pull request already exists"},
        )

    monkeypatch.setattr(
        "app.integrations.github_client.httpx.post",
        fake_post,
    )

    with pytest.raises(
        GitHubAPIError,
        match="A pull request already exists",
    ):
        create_pull_request(
            title="Test PR",
            body="Test",
            head="feature/test",
        )


def test_network_error_is_handled(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setenv("GITHUB_OWNER", "work-of-harsh")
    monkeypatch.setenv("GITHUB_REPO", "ai-engineering-copilot")

    def fake_post(url, headers, json, timeout):
        raise httpx.ConnectError("Connection failed")

    monkeypatch.setattr(
        "app.integrations.github_client.httpx.post",
        fake_post,
    )

    with pytest.raises(
        GitHubAPIError,
        match="Could not connect to GitHub API",
    ):
        create_pull_request(
            title="Test PR",
            body="Test",
            head="feature/test",
        )
