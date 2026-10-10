
from app.ingestion.reader import read_repository
from app.ingestion.chunker import chunk_document


def main():
    repository_path = "data/sample_repo"

    documents = read_repository(repository_path)
    all_chunks = []

    for document in documents:
        chunks = chunk_document(
            path=document["path"],
            content=document["content"],
        )
        all_chunks.extend(chunks)

    print("Files read:", len(documents))
    print("Chunks created:", len(all_chunks))
    print()

    for chunk in all_chunks:
        print(
            "{} | lines {}-{}".format(
                chunk["path"],
                chunk["start_line"],
                chunk["end_line"],
            )
        )

    print()
    print("First chunk preview:")

    if all_chunks:
        print(all_chunks[0]["content"][:300])


if __name__ == "__main__":
    main()
