import json
import sys
from pathlib import Path

from app.ingestion.fix_validator import validate_fix


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_FILE = PROJECT_ROOT / "data" / "debugging_benchmark.json"


def main():
    cases = json.loads(
        DATASET_FILE.read_text(encoding="utf-8")
    )

    passed_count = 0
    failed_cases = []

    print("Checking debugging benchmark fixtures...")
    print("=" * 60)

    for case in cases:
        case_id = case["id"]
        case_name = case["name"]

        fixture_root = (
            PROJECT_ROOT / case["fixture_path"]
        ).resolve()

        target_file = (
            fixture_root / case["file_path"]
        ).resolve()

        try:
            target_file.relative_to(fixture_root)
        except ValueError:
            print(case_id, "INVALID FILE PATH")
            failed_cases.append(case_id)
            continue

        if not target_file.is_file():
            print(case_id, "TARGET FILE MISSING")
            failed_cases.append(case_id)
            continue

        original_content = target_file.read_text(
            encoding="utf-8"
        )

        old_text = case["expected_old_text"]
        new_text = case["expected_new_text"]

        if original_content.count(old_text) != 1:
            print(case_id, "EXPECTED BUG TEXT NOT UNIQUE")
            failed_cases.append(case_id)
            continue

        # First verify that the original bug fails.
        baseline = validate_fix(
            case["file_path"],
            original_content,
            repo_root=fixture_root
        )

        # Apply the known correct replacement in memory.
        corrected_content = original_content.replace(
            old_text,
            new_text,
            1
        )

        # Then verify that the corrected code passes.
        corrected = validate_fix(
            case["file_path"],
            corrected_content,
            repo_root=fixture_root
        )

        baseline_ok = not baseline["passed"]
        correction_ok = corrected["passed"]

        if baseline_ok and correction_ok:
            print(
                case_id,
                "| PASS |",
                case_name,
                "| original fails, correction passes"
            )
            passed_count += 1
        else:
            print(
                case_id,
                "| FAIL |",
                case_name
            )

            print(
                "  Original test passed unexpectedly:",
                baseline["passed"]
            )

            print(
                "  Corrected test passed:",
                corrected["passed"]
            )

            print("  Baseline output:")
            print(baseline["stdout"])

            print("  Corrected output:")
            print(corrected["stdout"])

            failed_cases.append(case_id)

    print("=" * 60)
    print("Total cases:", len(cases))
    print("Verified:", passed_count)
    print("Failed:", len(failed_cases))

    if failed_cases:
        print("Cases needing attention:", failed_cases)
        sys.exit(1)

    print("All benchmark fixtures verified successfully.")


if __name__ == "__main__":
    main()