
import json
from pathlib import Path

from app.ingestion.qa import answer_question


def main():
    evaluation_path = Path("data/answer_evaluation.json")

    with evaluation_path.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    passed = 0

    for index, case in enumerate(cases, start=1):
        question = case["question"]
        expected_fact = case["expected_fact"].lower()

        print("\n" + "=" * 60)
        print("Question {}: {}".format(index, question))

        result = answer_question(question)
        answer = result["answer"]

        print("Expected fact: {}".format(case["expected_fact"]))
        print("Generated answer: {}".format(answer))

        # Baseline heuristic, not a semantic correctness judge.
        normalized_answer = " ".join(answer.lower().split())
        normalized_fact = " ".join(expected_fact.split())
        fact_words = [
            word for word in normalized_fact.split()
            if len(word) > 2
        ]

        matched = sum(
            1 for word in fact_words if word in normalized_answer
        )

        coverage = matched / len(fact_words) if fact_words else 0.0
        case_passed = coverage >= 0.7

        print("Keyword coverage: {:.0%}".format(coverage))
        print("Result: {}".format(
            "PASS" if case_passed else "REVIEW"
        ))

        if case_passed:
            passed += 1

    print("\n" + "=" * 60)
    print("Cases passed heuristic: {}/{}".format(passed, len(cases)))
    print(
        "Important: keyword coverage is only a rough screening "
        "metric, not proof of factual correctness."
    )


if __name__ == "__main__":
    main()
