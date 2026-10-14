
import json

from app.ingestion.qa import answer_question


def main():
    with open(
        "data/answer_evaluation.json",
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    if not cases:
        print("No evaluation cases found.")
        return

    source_hits = 0
    fact_hits = 0

    for number, case in enumerate(cases, start=1):
        print("\n--- Case {} ---".format(number))
        print("Question:", case["question"])

        try:
            result = answer_question(case["question"])
        except Exception as exc:
            print("ERROR:", str(exc))
            continue

        answer = result["answer"]
        sources = result["sources"]

        expected_source = case["expected_source"]
        expected_fact = case["expected_fact"]

        source_found = any(
            source["path"].replace("\\", "/") == expected_source
            for source in sources
        )

        # A simple diagnostic, not a semantic correctness test.
        key_terms = [
            term.lower()
            for term in expected_fact.split()
            if len(term) >= 5
        ]
        matched_terms = sum(
            1 for term in key_terms if term in answer.lower()
        )
        fact_coverage = (
            matched_terms / len(key_terms) if key_terms else 0
        )

        source_hits += int(source_found)
        fact_hits += int(fact_coverage >= 0.5)

        print("Expected source:", expected_source)
        print("Source retrieved:", source_found)
        print("Expected fact:", expected_fact)
        print("Answer:", answer)
        print("Keyword coverage: {:.0%}".format(fact_coverage))
        print("Sources:", [s["path"] for s in sources])

    total = len(cases)

    print("\n--- Grounding Diagnostics ---")
    print("Cases:", total)
    print("Expected source retrieved: {}/{}".format(source_hits, total))
    print("Answers passing keyword heuristic: {}/{}".format(
        fact_hits, total
    ))
    print(
        "Source retrieval rate: {:.2%}".format(source_hits / total)
    )
    print(
        "Keyword heuristic pass rate: {:.2%}".format(fact_hits / total)
    )
    print(
        "\nReview answers manually. Keyword coverage does not prove "
        "factual correctness or groundedness."
    )


if __name__ == "__main__":
    main()
