
import json

from app.ingestion.retriever import search_repository


def main():
    with open("data/evaluation.json", "r", encoding="utf-8") as file:
        cases = json.load(file)

    if not cases:
        print("No evaluation questions found.")
        return

    hit_at_1 = 0
    hit_at_3 = 0
    reciprocal_rank_sum = 0.0

    for number, case in enumerate(cases, start=1):
        results = search_repository(case["question"], top_k=3)

        retrieved_paths = [
            item["path"].replace("\\", "/")
            for item in results
                            ]
        expected_source = case["expected_source"].replace("\\", "/")

        rank = None
        for position, path in enumerate(retrieved_paths, start=1):
            if path == expected_source:
                rank = position
                break

        if retrieved_paths and retrieved_paths[0] == expected_source:
            hit_at_1 += 1

        if rank is not None:
            hit_at_3 += 1
            reciprocal_rank_sum += 1.0 / rank

        print("\nQuestion {}: {}".format(number, case["question"]))
        print("Expected source:", expected_source)

        for position, result in enumerate(results, start=1):
            print(
                "  {}. {} | similarity={:.4f}".format(
                    position,
                    result["path"],
                    result["score"],
                )
            )

        if rank is None:
            print("Result: MISS")
        else:
            print("Result: HIT at rank {}".format(rank))

    total = len(cases)

    print("\n--- Retrieval Evaluation Summary ---")
    print("Questions:", total)
    print("Hit Rate@1: {:.2%}".format(hit_at_1 / total))
    print("Hit Rate@3: {:.2%}".format(hit_at_3 / total))
    print("MRR: {:.4f}".format(reciprocal_rank_sum / total))


if __name__ == "__main__":
    main()
