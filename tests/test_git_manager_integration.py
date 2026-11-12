
import subprocess

from app.ingestion import git_manager


def run_git(repository, *args):
    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(repository),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    if result.returncode != 0:
        raise RuntimeError(result.stderr)

    return result.stdout.strip()


def test_apply_validated_patch_creates_real_commit(
    tmp_path,
    monkeypatch,
):
    # Create a temporary project and sample repository.
    project_root = tmp_path / "copilot"
    sample_repo = project_root / "data" / "sample_repo"

    target_file = sample_repo / "app" / "payment.py"
    target_file.parent.mkdir(parents=True)

    original_content = (
        "def calculate_total(amount, tax_rate):\n"
        "    return amount + tax_rate\n"
    )

    new_content = (
        "def calculate_total(amount, tax_rate):\n"
        "    return amount * (1 + tax_rate)\n"
    )

    target_file.write_text(original_content, encoding="utf-8")

    # Initialize an actual Git repository.
    run_git(project_root, "init")
    run_git(project_root, "config", "user.name", "Test User")
    run_git(project_root, "config", "user.email", "test@example.com")

    run_git(project_root, "add", ".")
    run_git(project_root, "commit", "-m", "Initial test fixture")

    run_git(project_root, "checkout", "-b", "feature/test-commit")

    # Redirect Git manager to the temporary repository.
    monkeypatch.setattr(
        git_manager,
        "PROJECT_ROOT",
        project_root,
    )

    monkeypatch.setattr(
        git_manager,
        "SAMPLE_REPO",
        sample_repo,
    )

    monkeypatch.setattr(
        git_manager,
        "resolve_supported_repo_root",
        lambda repo_root=None: sample_repo,
    )

    # Mock validation so this test focuses on real Git operations.
    monkeypatch.setattr(
        git_manager,
        "validate_fix",
        lambda **kwargs: {
            "passed": True,
            "stdout": "4 passed",
            "stderr": "",
            "timed_out": False,
        },
    )

    result = git_manager.apply_validated_patch(
        file_path="app/payment.py",
        new_content=new_content,
        commit_message="Fix payment tax calculation",
        repo_root=sample_repo,
    )

    # Verify the operation returned success.
    assert result["success"] is True
    assert result["stage"] == "committed"
    assert result["branch"] == "feature/test-commit"
    assert result["commit_hash"]
    assert result["working_tree_clean"] is True

    # Verify the file was actually modified.
    assert target_file.read_text(encoding="utf-8") == new_content

    # Verify a real Git commit was created.
    commit_message = run_git(
        project_root,
        "log",
        "-1",
        "--pretty=%s",
    )

    assert commit_message == "Fix payment tax calculation"

    committed_files = run_git(
        project_root,
        "diff",
        "HEAD^",
        "HEAD",
        "--name-only",
    )

    assert committed_files == "data/sample_repo/app/payment.py"

    # Verify no uncommitted changes remain.
    assert run_git(
        project_root,
        "status",
        "--porcelain",
    ) == ""
