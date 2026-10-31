from scripts.evaluate_debugging_workflow import (
    normalize_text,
    contains_expected,
    percentage,
)


def test_normalize_text_ignores_extra_whitespace():
    assert normalize_text(
        "return amount +\n    (amount * tax_rate)"
    ) == "return amount + (amount * tax_rate)"


def test_contains_expected_ignores_whitespace():
    actual = "return amount +\n    (amount * tax_rate)"

    expected = "return amount + (amount * tax_rate)"

    assert contains_expected(actual, expected)


def test_contains_expected_returns_false_for_wrong_fix():
    assert not contains_expected(
        "return amount + 999",
        "return amount + (amount * tax_rate)",
    )


def test_percentage_calculation():
    assert percentage(3, 4) == 75.0


def test_percentage_handles_zero_cases():
    assert percentage(0, 0) == 0.0