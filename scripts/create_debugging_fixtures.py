import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CASES_DIR = ROOT / "data" / "benchmark_cases"
DATASET_FILE = ROOT / "data" / "debugging_benchmark.json"


CASES = [
    {
        "id": "BUG-001",
        "name": "Percentage tax calculation",
        "file": "app/payment.py",
        "module": """def calculate_total(amount, tax_rate):
    return amount + tax_rate
""",
        "test": """from app.payment import calculate_total

def test_percentage_tax():
    assert calculate_total(100, 0.18) == 118
""",
        "failure": "Expected 118 but got 100.18",
        "old": "return amount + tax_rate",
        "new": "return amount + (amount * tax_rate)",
    },
    {
        "id": "BUG-002",
        "name": "Incorrect discount calculation",
        "file": "app/discount.py",
        "module": """def apply_discount(price, discount_rate):
    return price - discount_rate
""",
        "test": """from app.discount import apply_discount

def test_discount_percentage():
    assert apply_discount(100, 0.20) == 80
""",
        "failure": "Expected 80 but got 99.8",
        "old": "return price - discount_rate",
        "new": "return price - (price * discount_rate)",
    },
    {
        "id": "BUG-003",
        "name": "Free shipping threshold boundary",
        "file": "app/shipping.py",
        "module": """def shipping_fee(order_total):
    if order_total > 100:
        return 0
    return 10
""",
        "test": """from app.shipping import shipping_fee

def test_free_shipping_at_threshold():
    assert shipping_fee(100) == 0
""",
        "failure": "Expected free shipping at 100 but got 10",
        "old": "if order_total > 100:",
        "new": "if order_total >= 100:",
    },
    {
        "id": "BUG-004",
        "name": "Retry count off by one",
        "file": "app/retry.py",
        "module": """def total_attempts(retry_count):
    attempts = 0
    for _ in range(retry_count):
        attempts += 1
    return attempts
""",
        "test": """from app.retry import total_attempts

def test_retry_count_includes_initial_attempt():
    assert total_attempts(3) == 4

def test_zero_retries_still_has_initial_attempt():
    assert total_attempts(0) == 1

def test_one_retry_has_two_total_attempts():
    assert total_attempts(1) == 2
""",
        "failure": "Expected 4 attempts but got 3",
        "old": "range(retry_count)",
        "new": "range(retry_count + 1)",
    },
    {
        "id": "BUG-005",
        "name": "Timeout configuration ignored",
        "file": "app/timeout.py",
        "module": """def get_timeout(config):
    return 30
""",
        "test": """from app.timeout import get_timeout

def test_timeout_uses_configuration():
    assert get_timeout({"timeout_seconds": 10}) == 10

def test_timeout_uses_configured_large_value():
    assert get_timeout({"timeout_seconds": 60}) == 60

def test_timeout_defaults_when_configuration_is_missing():
    assert get_timeout({}) == 30
""",
        "failure": "Expected configured timeout 10 but got 30",
        "old": "return 30",
        "new": 'return config.get("timeout_seconds", 30)',
    },
    {
        "id": "BUG-006",
        "name": "Zero quantity accepted",
        "file": "app/quantity.py",
        "module": """def is_valid_quantity(quantity):
    return quantity >= 0
""",
        "test": """from app.quantity import is_valid_quantity

def test_zero_quantity_is_invalid():
    assert is_valid_quantity(0) is False
""",
        "failure": "Expected zero quantity to be invalid",
        "old": "return quantity >= 0",
        "new": "return quantity > 0",
    },
    {
        "id": "BUG-007",
        "name": "Incorrect currency rounding",
        "file": "app/currency.py",
        "module": """def round_currency(amount):
    return round(amount, 1)
""",
        "test": """from app.currency import round_currency

def test_currency_rounds_to_two_decimal_places():
    assert round_currency(10.126) == 10.13
""",
        "failure": "Expected 10.13 but got 10.1",
        "old": "round(amount, 1)",
        "new": "round(amount, 2)",
    },
    {
        "id": "BUG-008",
        "name": "Case-sensitive email validation",
        "file": "app/email_validation.py",
        "module": """def is_company_email(email):
    return email.endswith("@example.com")
""",
        "test": """from app.email_validation import is_company_email

def test_email_validation_is_case_insensitive():
    assert is_company_email("USER@EXAMPLE.COM") is True
""",
        "failure": "Expected uppercase company email to be accepted",
        "old": 'email.endswith("@example.com")',
        "new": 'email.lower().endswith("@example.com")',
    },
    {
        "id": "BUG-009",
        "name": "Out-of-stock item accepted",
        "file": "app/inventory.py",
        "module": """def can_fulfill_order(stock):
    return stock >= 0
""",
        "test": """from app.inventory import can_fulfill_order

def test_out_of_stock_item_cannot_be_fulfilled():
    assert can_fulfill_order(0) is False
""",
        "failure": "Expected unavailable item to be rejected",
        "old": "return stock >= 0",
        "new": "return stock > 0",
    },
    {
        "id": "BUG-010",
        "name": "Negative payment amount accepted",
        "file": "app/payment_validation.py",
        "module": """def is_valid_payment(amount):
    return amount != 0
""",
        "test": """from app.payment_validation import is_valid_payment

def test_negative_payment_is_rejected():
    assert is_valid_payment(-5) is False
""",
        "failure": "Expected negative payment to be rejected",
        "old": "return amount != 0",
        "new": "return amount > 0",
    },
]


def create_fixtures():
    benchmark_data = []

    for case in CASES:
        case_dir = CASES_DIR / case["id"]
        app_dir = case_dir / "app"
        tests_dir = case_dir / "tests"

        app_dir.mkdir(parents=True, exist_ok=True)
        tests_dir.mkdir(parents=True, exist_ok=True)

        (app_dir / "__init__.py").write_text(
            "", encoding="utf-8"
        )

        module_path = case_dir / case["file"]
        module_path.parent.mkdir(parents=True, exist_ok=True)
        module_path.write_text(
            case["module"], encoding="utf-8"
        )

        (tests_dir / "test_bug.py").write_text(
            case["test"], encoding="utf-8"
        )

        benchmark_data.append({
            "id": case["id"],
            "name": case["name"],
            "test_name": case["test"].split("def ")[1].split("(")[0],
            "error_output": case["failure"],
            "file_path": case["file"],
            "expected_source": case["file"],
            "expected_old_text": case["old"],
            "expected_new_text": case["new"],
            "fixture_path": "data/benchmark_cases/" + case["id"],
        })

    DATASET_FILE.write_text(
        json.dumps(benchmark_data, indent=4),
        encoding="utf-8",
    )

    print("Created", len(CASES), "benchmark fixtures.")
    print("Dataset:", DATASET_FILE)
    print("Fixtures:", CASES_DIR)


if __name__ == "__main__":
    create_fixtures()