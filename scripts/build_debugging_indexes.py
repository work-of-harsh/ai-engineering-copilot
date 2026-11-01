import argparse
import json
from pathlib import Path

from app.ingestion.reader import read_repository
from app.ingestion.chunker import chunk_document
from app.ingestion.embeddings import embed_text
from app.ingestion.repo_paths import (
    resolve_supported_repo_root,
    get_repository_index_path,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_FILE = (
    PROJECT_ROOT / "data" / "debugging_benchmark.json"
)


def build_case_index(case):
    case_id = case["id"]

    fixture_root = resolve_supported_repo_root(
        PROJECT_ROOT / case["fixture_path"]
    )

    print("\nBuilding index:", case_id)

    documents = read_repository(str(fixture_root))

    all_chunks = []

    for document in documents:
        chunks = chunk_document(
            path=document["path"],
            content=document["content"],
        )

        all_chunks.extend(chunks)

    if not all_chunks:
        raise ValueError(
            "No chunks found for " + case_id
        )

    indexed_chunks = []

    for number, chunk in enumerate(
        all_chunks,
        start=1
    ):
        print(
            "Embedding {}: {} of {}".format(
                case_id,
                number,
                len(all_chunks)
            )
        )

        vector = embed_text(
            chunk["content"],
            task_type="RETRIEVAL_DOCUMENT",
        )

        indexed_chunks.append({
            "path": chunk["path"],
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "content": chunk["content"],
            "embedding": vector,
        })

    index_path = get_repository_index_path(
        fixture_root
    )

    index_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with index_path.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(indexed_chunks, file)

    print("Files read:", len(documents))
    print("Chunks indexed:", len(indexed_chunks))
    print("Index saved:", index_path)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--case",
        help="Build only one fixture index, e.g. BUG-001."
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Build indexes for the first N cases."
    )

    args = parser.parse_args()

    cases = json.loads(
        DATASET_FILE.read_text(encoding="utf-8")
    )

    if args.case:
        cases = [
            case for case in cases
            if case["id"] == args.case
        ]

        if not cases:
            parser.error("Unknown benchmark case.")

    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be at least 1.")

        cases = cases[:args.limit]

    for case in cases:
        build_case_index(case)

    print("\nBenchmark index building completed.")


if __name__ == "__main__":
    main()