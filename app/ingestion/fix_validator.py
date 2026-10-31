import os
import shutil
import subprocess
import tempfile
from pathlib import Path


SAMPLE_REPO = Path("data/sample_repo").resolve()

ALLOWED_EXTENSIONS = {
    ".py", ".yaml", ".yml", ".json", ".txt", ".md"
}


def validate_fix(file_path: str, new_content: str) -> dict:
    """
    Apply proposed content to a disposable copy of the sample repo,
    run its tests, and return the result.
    """

    relative_path = Path(file_path)

    if relative_path.is_absolute():
        raise ValueError("Absolute paths are not allowed")

    if ".." in relative_path.parts:
        raise ValueError("Path traversal is not allowed")

    if relative_path.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type")

    source_file = (SAMPLE_REPO / relative_path).resolve()

    if os.path.commonpath([str(SAMPLE_REPO), str(source_file)]) != str(SAMPLE_REPO):
        raise ValueError("Invalid file path")

    if not source_file.is_file():
        raise FileNotFoundError("Target file does not exist")

    with tempfile.TemporaryDirectory(prefix="copilot-validation-") as temp_dir:
        temp_repo = Path(temp_dir) / "sample_repo"

        shutil.copytree(SAMPLE_REPO, temp_repo)

        target_file = temp_repo / relative_path
        target_file.write_text(new_content, encoding="utf-8")

        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"

        result = subprocess.run(
            ["python", "-m", "pytest", "tests", "-q"],
            cwd=str(temp_repo),
            capture_output=True,
            text=True,
            timeout=60,
            env=env,
        )

        return {
            "passed": result.returncode == 0,
            "return_code": result.returncode,
            "stdout": result.stdout[-5000:],
            "stderr": result.stderr[-5000:],
            "file_validated": str(relative_path),
        }