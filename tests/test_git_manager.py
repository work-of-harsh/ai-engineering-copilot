
from pathlib import Path

import pytest

from app.ingestion import git_manager


@pytest.fixture
def git_environment(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    repo_root = project_root / "data" / "sample_repo"

    repo_root.mkdir(parents=True)

    target = repo_root / "app" / "payment.py"
    target.parent.mkdir(parents=True)

    original_content = "def calculate_total(amount, tax_rate):\n    return amount + tax_rate\n"
    target.write_text(original_content, encoding="utf-8")

    monkeypatch.setattr(
        git_manager,
        "PROJECT_ROOT",
        project_root,
    )

    monkeypatch.setattr(
        git_manager,
        "SAMPLE_REPO",
        repo_root,
    )

    monkeypatch.setattr(
        git_manager,
        "resolve_supported_repo_root",
        lambda repo_root=None: repo_root or git_manager.SAMPLE_REPO,
    )

    commands = []

    def fake_git(args):
        args = list(args)
        commands.append(args)

        if args == ["rev-parse", "--show-toplevel"]:
            return str(project_root)

        if args == ["branch", "--show-current"]:
            return "feature/git-pr-automation"

        if args == ["status", "--porcelain"]:
            return ""

        if args == ["diff", "--cached", "--name-only"]:
            return "data/sample_repo/app/payment.py"

        if args == ["rev-parse", "--short", "HEAD"]:
            return "abc1234"

        return ""

    monkeypatch.setattr(
        git_manager,
        "_run_git",
        fake_git,
    )

    monkeypatch.setattr(
        git_manager,
        "validate_fix",
        lambda **kwargs: {"passed": True, "return_code": 0},
    )

    return {
        "project_root": project_root,
        "repo_root": repo_root,
        "target": target,
        "original_content": original_content,
        "commands": commands,
        "new_content": (
            "def calculate_total(amount, tax_rate):\n"
            "    return amount + (amount * tax_rate)\n"
        ),
    }


def test_successful_patch_is_committed(git_environment):
    env = git_environment

    result = git_manager.apply_validated_patch(
        file_path="app/payment.py",
        new_content=env["new_content"],
        commit_message="Fix percentage tax calculation",
    )

    assert result["success"] is True
    assert result["stage"] == "committed"
    assert result["branch"] == "feature/git-pr-automation"
    assert result["commit_hash"] == "abc1234"
    assert result["working_tree_clean"] is True

    assert env["target"].read_text(encoding="utf-8") == env["new_content"]

    assert ["commit", "-m", "Fix percentage tax calculation"] in env["commands"]


def test_failed_validation_does_not_modify_file(
    git_environment,
    monkeypatch,
):
    env = git_environment

    monkeypatch.setattr(
        git_manager,
        "validate_fix",
        lambda **kwargs: {"passed": False, "return_code": 1},
    )

    result = git_manager.apply_validated_patch(
        file_path="app/payment.py",
        new_content=env["new_content"],
        commit_message="Attempt invalid fix",
    )

    assert result["success"] is False
    assert result["stage"] == "validation"

    assert env["target"].read_text(
        encoding="utf-8"
    ) == env["original_content"]

    assert not any(
        command[0] == "commit"
        for command in env["commands"]
    )


def test_dirty_working_tree_is_rejected(
    git_environment,
    monkeypatch,
):
    env = git_environment
    original_git = git_manager._run_git

    def dirty_git(args):
        if list(args) == ["status", "--porcelain"]:
            return " M README.md"

        return original_git(args)

    monkeypatch.setattr(git_manager, "_run_git", dirty_git)

    with pytest.raises(git_manager.GitOperationError):
        git_manager.apply_validated_patch(
            "app/payment.py",
            env["new_content"],
            "Fix payment calculation",
        )

    assert env["target"].read_text(
        encoding="utf-8"
    ) == env["original_content"]


def test_protected_branch_is_rejected(
    git_environment,
    monkeypatch,
):
    env = git_environment
    original_git = git_manager._run_git

    def master_git(args):
        if list(args) == ["branch", "--show-current"]:
            return "master"

        return original_git(args)

    monkeypatch.setattr(git_manager, "_run_git", master_git)

    with pytest.raises(git_manager.GitOperationError):
        git_manager.apply_validated_patch(
            "app/payment.py",
            env["new_content"],
            "Fix payment calculation",
        )

    assert env["target"].read_text(
        encoding="utf-8"
    ) == env["original_content"]


def test_identical_content_is_rejected(git_environment):
    env = git_environment

    with pytest.raises(ValueError):
        git_manager.apply_validated_patch(
            "app/payment.py",
            env["original_content"],
            "No change",
        )
