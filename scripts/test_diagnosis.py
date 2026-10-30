
from app.ingestion.diagnostics import diagnose_test_failure


result = diagnose_test_failure(
    test_name="test_calculate_total_applies_percentage_tax",
    error_output="""
    Expected: 118
    Actual: 100.18

    AssertionError:
    assert calculate_total(100, 0.18) == 118
    """,
)

print("\nTEST NAME:")
print(result["test_name"])

print("\nAI DIAGNOSIS:")
print(result["diagnosis"])

print("\nRETRIEVED SOURCES:")
for source in result["sources"]:
    print(
        "{}:{}-{}".format(
            source["path"],
            source["start_line"],
            source["end_line"],
        )
    )
