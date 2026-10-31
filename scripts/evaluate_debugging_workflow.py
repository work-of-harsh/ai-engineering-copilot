import json
import re
from datetime import datetime
from pathlib import Path

from app.ingestion.fix_validator import validate_fix
from app.ingestion.patch_generator import generate_fix_patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]

BENCHMARK_FILE = (
    PROJECT_ROOT / "data" / "debugging_benchmark.json"
)

REPORT_FILE = (
    PROJECT_ROOT / "reports" / "debugging_benchmark_latest.json"
)


def normalize_text(value):
    """Normalize whitespace for comparison."""

    return re.sub(r"\s+", " ", value or "").strip()


def contains_expected(actual, expected):
    """Check whether expected text is present, ignoring whitespace."""

    return normalize_text(expected) in normalize_text(actual)


def percentage(passed, total):
    if total == 0:
        return 0.0

    return round((passed / total) * 100, 2)


def run_benchmark():
    with open(BENCHMARK_FILE, "r", encoding="utf-8") as file:
        cases = json.load(file)

    results = []

    for case in cases:
        print("\nEvaluating:", case["id"], case["name"])

        row = {
            "id": case["id"],
            "name": case["name"],
            "generation_succeeded": False,
            "source_retrieved": False,
            "correct_target_file": False,
            "old_code_matched": False,
            "expected_fix_present": False,
            "tests_passed": False,
            "workflow_success": False,
            "error": None,
        }

        try:
            # 1. Generate a patch using the actual RAG + Gemini pipeline.
            patch = generate_fix_patch(
                test_name=case["test_name"],
                error_output=case["error_output"],
                file_path=case["file_path"],
            )

            row["generation_succeeded"] = True

            # 2. Check whether retrieval found the expected file.
            sources = patch.get("sources", [])

            row["source_retrieved"] = any(
                normalize_text(source.get("path", "")).replace("\\", "/")
                == case["expected_source"].replace("\\", "/")
                for source in sources
            )

            # 3. Check the target file.
            row["correct_target_file"] = (
                patch.get("file_path") == case["file_path"]
            )

            # 4. Check whether the generated patch identifies
            #    the faulty code and proposes the expected correction.
            row["old_code_matched"] = contains_expected(
                patch.get("old_text", ""),
                case["expected_old_text"],
            )

            row["expected_fix_present"] = contains_expected(
                patch.get("new_text", ""),
                case["expected_new_text"],
            )

            # 5. Run the proposed complete file in the temporary copy.
            validation = validate_fix(
                file_path=patch["file_path"],
                new_content=patch["proposed_content"],
            )

            row["tests_passed"] = validation["passed"]
            row["timed_out"] = validation.get("timed_out", False)
            row["test_output"] = validation.get("stdout", "")
            row["test_error"] = validation.get("stderr", "")

            # 6. All conditions must be satisfied for a workflow success.
            row["workflow_success"] = all([
                row["generation_succeeded"],
                row["source_retrieved"],
                row["correct_target_file"],
                row["old_code_matched"],
                row["expected_fix_present"],
                row["tests_passed"],
            ])

        except Exception as exc:
            row["error"] = str(exc)
            print("ERROR:", exc)

        results.append(row)

        print("Retrieval:", row["source_retrieved"])
        print("Correct target:", row["correct_target_file"])
        print("Expected fix:", row["expected_fix_present"])
        print("Tests passed:", row["tests_passed"])
        print("Workflow success:", row["workflow_success"])

    total = len(results)

    report = {
        "evaluated_at": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "total_cases": total,
        "metrics": {
            "generation_success_rate": percentage(
                sum(r["generation_succeeded"] for r in results),
                total,
            ),
            "retrieval_success_rate": percentage(
                sum(r["source_retrieved"] for r in results),
                total,
            ),
            "correct_target_rate": percentage(
                sum(r["correct_target_file"] for r in results),
                total,
            ),
            "expected_fix_rate": percentage(
                sum(
                    r["old_code_matched"] and r["expected_fix_present"]
                    for r in results
                ),
                total,
            ),
            "test_pass_rate": percentage(
                sum(r["tests_passed"] for r in results),
                total,
            ),
            "end_to_end_success_rate": percentage(
                sum(r["workflow_success"] for r in results),
                total,
            ),
        },
        "results": results,
    }

    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(REPORT_FILE, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n========== BENCHMARK SUMMARY ==========")
    print("Total cases:", total)

    for metric, value in report["metrics"].items():
        print(metric + ":", str(value) + "%")

    print("\nReport saved to:", REPORT_FILE)

    return report


if __name__ == "__main__":
    run_benchmark()