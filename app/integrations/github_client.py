
import os

import httpx


class GitHubAPIError(RuntimeError):
    pass


def create_pull_request(
    title,
    body,
    head,
    base=None,
):
    """Create a GitHub pull request for an already-pushed branch."""

    token = os.getenv("GITHUB_TOKEN")
    owner = os.getenv("GITHUB_OWNER")
    repo = os.getenv("GITHUB_REPO")
    base = base or os.getenv("GITHUB_BASE_BRANCH", "master")

    if not token:
        raise GitHubAPIError("GITHUB_TOKEN is not configured")

    if not owner or not repo:
        raise GitHubAPIError(
            "GITHUB_OWNER or GITHUB_REPO is not configured"
        )

    if not isinstance(title, str) or not title.strip():
        raise ValueError("Pull request title cannot be empty")

    if not isinstance(body, str):
        raise ValueError("Pull request body must be a string")

    if not isinstance(head, str) or not head.strip():
        raise ValueError("Head branch cannot be empty")

    if head == base:
        raise ValueError("Head and base branches must be different")

    url = (
        "https://api.github.com/repos/"
        "{}/{}/pulls".format(owner, repo)
    )

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer {}".format(token),
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Engineering-Copilot",
    }

    payload = {
        "title": title.strip(),
        "body": body,
        "head": head,
        "base": base,
    }

    try:
        response = httpx.post(
            url,
            headers=headers,
            json=payload,
            timeout=20.0,
        )

    except httpx.RequestError as exc:
        raise GitHubAPIError(
            "Could not connect to GitHub API"
        ) from exc

    if response.status_code != 201:
        try:
            error_data = response.json()
            message = error_data.get(
                "message",
                "Unknown GitHub API error",
            )
        except ValueError:
            message = "GitHub returned an invalid error response"

        raise GitHubAPIError(
            "GitHub API returned status {}: {}".format(
                response.status_code,
                message,
            )
        )

    result = response.json()

    return {
        "success": True,
        "number": result["number"],
        "title": result["title"],
        "url": result["html_url"],
        "state": result["state"],
        "head": result["head"]["ref"],
        "base": result["base"]["ref"],
    }
