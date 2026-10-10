from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

EXCLUDED_FILES = {
    ".env",
    "credentials.json",
}

MAX_FILE_SIZE_BYTES = 500_000


def scan_repository(repo_path: str) -> List[Path]:
    root = Path(repo_path).resolve()

    if not root.exists():
        raise FileNotFoundError(
            "Repository directory does not exist: {}".format(root)
        )

    if not root.is_dir():
        raise NotADirectoryError(
            "Path is not a directory: {}".format(root)
        )

    discovered_files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        relative_path = path.relative_to(root)

        # Skip files inside excluded directories.
        if any(
            part in EXCLUDED_DIRECTORIES
            for part in relative_path.parts[:-1]
        ):
            continue

        # Never ingest obvious local secrets.
        if path.name.lower() in EXCLUDED_FILES:
            continue

        # Only scan file types we currently support.
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        # Skip unusually large files.
        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
        except OSError:
            continue

        discovered_files.append(path)

    return sorted(discovered_files)