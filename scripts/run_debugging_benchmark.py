import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.patch_generator import generate_fix_patch
from app.ingestion.fix_validator import validate_fix


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATASET_FILE = (
    PROJECT_ROOT / "data" / "debugging_benchmark.json"
)

REPORT_FILE = (
    PROJECT_ROOT / "reports" / "debugging_benchmark_latest.json"
)


def run_case(case):
    case_id = case["id"]
    fixture_root = (
        PROJECT_ROOT / case["fixture_path"]
    ).resolve()

    print("\n" + "=" * 60)
    print("Running:", case_id, "-", case["name"])
    print("=" * 60)

    try:
        # Generate a patch using the AI Copilot.
        patch = generate_fix_patch(
            test_name=case["test_name"],
            error_output=case["error_output"],
            file_path=case["file_path"],
            repo_root=fixture_root
        )

        print("Patch generated.")
        print("Summary:", patch["summary"])
        print("Confidence:", patch["confidence"])

        # Validate the AI-generated replacement.
        validation = validate_fix(
            file_path=case["file_path"],
            new_content=patch["proposed_content"],
            repo_root=fixture_root
        )

        # Build the expected corrected source for comparison.
        original_file = (
            fixture_root / case["file_path"]
        )

        original_content = original_file.read_text(
            encoding="utf-8"
        )

        expected_old_text = case["expected_old_text"]
        expected_new_text = case["expected_new_text"]

        if original_content.count(expected_old_text) != 1:
            raise ValueError(
                "Expected bug text does not occur exactly once."
            )

        expected_content = original_content.replace(
            expected_old_text,
            expected_new_text,
            1
        )

        exact_match = (
            patch["proposed_content"] == expected_content
        )

        tests_passed = validation["passed"]

        status = "PASS" if tests_passed else "FAIL"

        print("Test validation:", status)
        print("Exact expected source match:", exact_match)

        return {
            "id": case_id,
            "name": case["name"],
            "status": status,
            "patch_generated": True,
            "tests_passed": tests_passed,
            "exact_match": exact_match,
            "summary": patch["summary"],
            "confidence": patch["confidence"],
            "old_text": patch["old_text"],
            "new_text": patch["new_text"],
            "validation": validation,
            "sources": patch.get("sources", []),
            "error": None
        }

    except Exception as exc:
        print("ERROR:", str(exc))

        return {
            "id": case_id,
            "name": case["name"],
            "status": "ERROR",
            "patch_generated": False,
            "tests_passed": False,
            "exact_match": False,
            "error": type(exc).__name__ + ": " + str(exc)
        }


def main():
    parser = argparse.ArgumentParser(
        description="Run the AI debugging benchmark."
    )

    parser.add_argument(
        "--case",
        help="Run only one case, for example BUG-001."
    )

    parser.add_argument(
        "--limit",
        type=int,
        help="Run only the first N cases."
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
            print("Unknown benchmark case:", args.case)
            return

    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be at least 1.")

        cases = cases[:args.limit]

    results = []

    for case in cases:
        results.append(run_case(case))

    total = len(results)

    patch_generated = sum(
        1 for result in results
        if result["patch_generated"]
    )

    tests_passed = sum(
        1 for result in results
        if result["tests_passed"]
    )

    exact_matches = sum(
        1 for result in results
        if result["exact_match"]
    )

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "benchmark_type": (
            "AI-generated patch with test-based validation"
        ),
        "summary": {
            "total_cases": total,
            "patches_generated": patch_generated,
            "tests_passed": tests_passed,
            "exact_matches": exact_matches,
            "success_rate_percent": (
                round(tests_passed * 100 / total, 2)
                if total else 0
            )
        },
        "results": results
    }

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    REPORT_FILE.write_text(
        json.dumps(report, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)
    print("Total cases:", total)
    print("Patches generated:", patch_generated)
    print("Tests passed:", tests_passed)
    print("Exact expected matches:", exact_matches)
    print("Success rate:", report["summary"]["success_rate_percent"], "%")
    print("Report saved to:", REPORT_FILE)


if __name__ == "__main__":
    main()