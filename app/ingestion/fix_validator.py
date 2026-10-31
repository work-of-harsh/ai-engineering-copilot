import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_REPO = PROJECT_ROOT / "data" / "sample_repo"

ALLOWED_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".json", ".txt", ".md"
}

MAX_CONTENT_LENGTH = 500000
TEST_TIMEOUT_SECONDS = 60


def validate_fix(file_path: str, new_content: str) -> dict:
    """Validate proposed file content against tests in a temporary copy."""

    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty")

    if not isinstance(new_content, str) or not new_content:
        raise ValueError("New file content cannot be empty")

    if len(new_content) > MAX_CONTENT_LENGTH:
        raise ValueError("New file content exceeds 500000 characters")

    relative_path = Path(file_path)

    if relative_path.is_absolute():
        raise ValueError("Absolute paths are not allowed")

    if ".." in relative_path.parts:
        raise ValueError("Path traversal is not allowed")

    if relative_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    source_file = (SAMPLE_REPO / relative_path).resolve()

    try:
        source_file.relative_to(SAMPLE_REPO.resolve())
    except ValueError:
        raise ValueError("Invalid file path")

    if not source_file.is_file():
        raise FileNotFoundError("Target file does not exist")

    with tempfile.TemporaryDirectory(
        prefix="copilot-validation-"
    ) as temp_dir:

        temp_repo = Path(temp_dir) / "sample_repo"

        shutil.copytree(SAMPLE_REPO, temp_repo)

        target_file = temp_repo / relative_path
        target_file.write_text(new_content, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "tests",
                    "-q"
                ],
                cwd=str(temp_repo),
                capture_output=True,
                text=True,
                timeout=TEST_TIMEOUT_SECONDS,
                env=env,
            )

            return {
                "passed": result.returncode == 0,
                "return_code": result.returncode,
                "stdout": result.stdout[-5000:],
                "stderr": result.stderr[-5000:],
                "file_validated": str(relative_path),
                "timed_out": False,
            }

        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""

            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")

            if isinstance(stderr, bytes):
                stderr = stderr.decode("utf-8", errors="replace")

            return {
                "passed": False,
                "return_code": 124,
                "stdout": stdout[-5000:],
                "stderr": stderr[-5000:],
                "file_validated": str(relative_path),
                "timed_out": True,
            }