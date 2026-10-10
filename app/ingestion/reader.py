
from pathlib import Path
from typing import Dict, List

from app.ingestion.scanner import scan_repository


def read_repository(repo_path: str) -> List[Dict[str, str]]:
    root = Path(repo_path).resolve()
    files = scan_repository(str(root))
    documents = []

    for file_path in files:
        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            print("Could not read {}: {}".format(file_path, exc))
            continue

        documents.append({
            "path": str(file_path.relative_to(root)),
            "content": content,
        })

    return documents
