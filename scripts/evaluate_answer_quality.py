
import json
from pathlib import Path

from app.ingestion.qa import answer_question


def normalize_path(path):
    return str(path).replace("\\", "/").lower()


def calculate_fact_coverage(answer, expected_fact):
    answer_words = set(answer.lower().split())

    fact_words = [
        word.strip(".,!?():;")
        for word in expected_fact.lower().split()
    ]

    fact_words = [word for word in fact_words if len(word) > 2]

    if not fact_words:
        return 0.0

    matched = sum(
        1 for word in fact_words if word in answer_words
    )

    return matched / len(fact_words)


def main():
    evaluation_path = Path("data/answer_evaluation.json")

    with evaluation_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    fact_passed = 0
    source_passed = 0
    total = len(cases)

    for index, case in enumerate(cases, start=1):
        print("\n" + "=" * 60)
        print("Question {}: {}".format(index, case["question"]))

        result = answer_question(case["question"])

        answer = result["answer"]
        expected_fact = case["expected_fact"]
        expected_source = normalize_path(case["expected_source"])

        sources = result.get("sources", [])

        retrieved_paths = [
            normalize_path(source["path"])
            for source in sources
        ]

        coverage = calculate_fact_coverage(
            answer, expected_fact
        )

        fact_ok = coverage >= 0.7
        source_ok = expected_source in retrieved_paths

        if fact_ok:
            fact_passed += 1

        if source_ok:
            source_passed += 1

        print("Expected fact: {}".format(expected_fact))
        print("Generated answer: {}".format(answer))
        print("Fact keyword coverage: {:.0%}".format(coverage))
        print("Fact check: {}".format(
            "PASS" if fact_ok else "REVIEW"
        ))
        print("Expected source: {}".format(expected_source))
        print("Retrieved sources: {}".format(retrieved_paths))
        print("Source check: {}".format(
            "PASS" if source_ok else "REVIEW"
        ))

    print("\n" + "=" * 60)
    print("ANSWER QUALITY SUMMARY")
    print("Fact checks: {}/{}".format(fact_passed, total))
    print("Source checks: {}/{}".format(source_passed, total))

    print(
        "\nNote: These are heuristic checks. "
        "Keyword coverage does not prove factual correctness, "
        "and retrieving the expected file does not prove that "
        "every answer claim is supported by it."
    )


if __name__ == "__main__":
    main()
