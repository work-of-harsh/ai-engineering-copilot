
from app.ingestion.retriever import search_repository


def main():
    query = input("Ask a question about the sample repository: ").strip()

    if not query:
        print("Please enter a question.")
        return

    results = search_repository(query, top_k=3)

    print("\n--- Search Results ---")

    for number, result in enumerate(results, start=1):
        print("\nResult {} | Similarity: {:.4f}".format(
            number, result["score"]
        ))
        print("File: {}".format(result["path"]))
        print("Lines: {}-{}".format(
            result["start_line"],
            result["end_line"],
        ))
        print(result["content"])


if __name__ == "__main__":
    main()
