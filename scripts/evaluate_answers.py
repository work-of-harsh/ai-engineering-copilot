
import json

from app.ingestion.qa import answer_question


def main():
    with open(
        "data/answer_evaluation.json",
        "r",
        encoding="utf-8",
    ) as file:
        cases = json.load(file)

    for number, case in enumerate(cases, start=1):
        print("\n" + "=" * 60)
        print("Evaluation question:", number)
        print("Question:", case["question"])

        try:
            result = answer_question(case["question"])
        except Exception as exc:
            print("Evaluation error:", str(exc))
            continue

        print("\nExpected source:", case["expected_source"])
        print("Expected fact:", case["expected_fact"])
        print("\nGenerated answer:")
        print(result["answer"])

        print("\nRetrieved sources:")
        for source in result["sources"]:
            print(
                "- {} (lines {}-{})".format(
                    source["path"],
                    source["start_line"],
                    source["end_line"],
                )
            )

        input("\nReview this answer, then press Enter to continue...")


if __name__ == "__main__":
    main()
