
import json
from pathlib import Path

from app.ingestion.reader import read_repository
from app.ingestion.chunker import chunk_document
from app.ingestion.embeddings import embed_text


def main():
    repository_path = "data/sample_repo"
    index_path = Path("data/index.json")

    documents = read_repository(repository_path)
    all_chunks = []

    for document in documents:
        chunks = chunk_document(
            path=document["path"],
            content=document["content"],
        )
        all_chunks.extend(chunks)

    print("Files read:", len(documents))
    print("Chunks to embed:", len(all_chunks))

    indexed_chunks = []

    for number, chunk in enumerate(all_chunks, start=1):
        print("Embedding chunk {} of {}...".format(
            number, len(all_chunks)
        ))

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

    index_path.parent.mkdir(parents=True, exist_ok=True)

    with index_path.open("w", encoding="utf-8") as file:
        json.dump(indexed_chunks, file)

    print()
    print("Index saved to:", index_path)
    print("Indexed chunks:", len(indexed_chunks))


if __name__ == "__main__":
    main()
