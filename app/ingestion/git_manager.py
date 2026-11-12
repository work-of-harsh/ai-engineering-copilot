
import subprocess
from pathlib import Path

from app.ingestion.fix_validator import validate_fix
from app.ingestion.repo_paths import (
    resolve_supported_repo_root,
    SAMPLE_REPO,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROTECTED_BRANCHES = {"main", "master"}


class GitOperationError(RuntimeError):
    """Raised when a Git operation cannot be completed safely."""


def _run_git(args):
    """Run a Git command from the project root."""

    result = subprocess.run(
        ["git"] + list(args),
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()

        raise GitOperationError(
            "Git command failed: git {}\n{}".format(
                " ".join(args),
                message,
            )
        )

    return result.stdout.strip()


def get_git_state():
    """Return the current branch and working-tree status."""

    actual_root = Path(
        _run_git(["rev-parse", "--show-toplevel"])
    ).resolve()

    if actual_root != PROJECT_ROOT.resolve():
        raise GitOperationError(
            "Git root does not match the AI Engineering Copilot project."
        )

    branch = _run_git(["branch", "--show-current"])
    status = _run_git(["status", "--porcelain"])

    return {
        "branch": branch,
        "clean": not bool(status),
        "status": status,
    }


def apply_validated_patch(
    file_path,
    new_content,
    commit_message,
    repo_root=None,
):
    """
    Validate a patch, apply it to sample_repo, and commit it.

    Only the validated target file is staged and committed.
    """

    if not isinstance(commit_message, str) or not commit_message.strip():
        raise ValueError("Commit message cannot be empty")

    repository_root = resolve_supported_repo_root(repo_root)

    # Git automation initially supports only the sample repository.
    # Benchmark fixtures must not be committed by this workflow.
    if repository_root.resolve() != SAMPLE_REPO.resolve():
        raise ValueError(
            "Git patch automation currently supports only data/sample_repo."
        )

    relative_path = Path(file_path)

    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError("Invalid file path")

    source_file = (repository_root / relative_path).resolve()

    try:
        source_file.relative_to(repository_root.resolve())
    except ValueError:
        raise ValueError("File path escapes the sample repository")

    try:
        git_file_path = source_file.relative_to(
            PROJECT_ROOT.resolve()
        ).as_posix()
    except ValueError:
        raise ValueError("Target file is outside the Git project")

    if not source_file.is_file():
        raise FileNotFoundError("Target file does not exist")

    # Never commit on main/master or overwrite existing local work.
    git_state = get_git_state()

    if not git_state["branch"]:
        raise GitOperationError("Could not determine current Git branch")

    if git_state["branch"] in PROTECTED_BRANCHES:
        raise GitOperationError(
            "Refusing to commit directly on the protected branch."
        )

    if not git_state["clean"]:
        raise GitOperationError(
            "Working tree is not clean. Commit or save existing changes first."
        )

    original_content = source_file.read_text(encoding="utf-8")

    if original_content == new_content:
        raise ValueError("Proposed content is identical to the current file")

    # First validate in the temporary copy.
    validation = validate_fix(
        file_path=file_path,
        new_content=new_content,
        repo_root=repository_root,
    )

    if not validation["passed"]:
        return {
            "success": False,
            "stage": "validation",
            "message": "Tests failed. No file was changed or committed.",
            "validation": validation,
        }

    # Apply and commit only after validation succeeds.
    try:
        source_file.write_text(new_content, encoding="utf-8")

        _run_git(["add", "--", git_file_path])

        staged_files = _run_git(
            ["diff", "--cached", "--name-only"]
        ).splitlines()

        if staged_files != [git_file_path]:
            raise GitOperationError(
                "Staged files did not match the single intended target."
            )

        _run_git([
            "commit",
            "-m",
            commit_message.strip(),
        ])

    except Exception as exc:
        # Restore the original file and unstage it if the commit fails.
        try:
            source_file.write_text(
                original_content,
                encoding="utf-8",
            )
            _run_git(["reset", "--", git_file_path])
        except Exception as rollback_error:
            raise GitOperationError(
                "Git operation failed and automatic rollback also failed: "
                "{}".format(rollback_error)
            )

        if isinstance(exc, GitOperationError):
            raise

        raise GitOperationError(
            "Patch could not be committed: {}".format(exc)
        )

    commit_hash = _run_git(["rev-parse", "--short", "HEAD"])
    final_status = _run_git(["status", "--porcelain"])

    return {
        "success": True,
        "stage": "committed",
        "branch": git_state["branch"],
        "file": git_file_path,
        "commit_hash": commit_hash,
        "commit_message": commit_message.strip(),
        "working_tree_clean": not bool(final_status),
        "validation": validation,
    }
