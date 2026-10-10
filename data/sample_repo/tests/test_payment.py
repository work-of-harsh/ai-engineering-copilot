from app.payment import calculate_total, is_payment_allowed


def test_calculate_total_applies_percentage_tax():
    assert calculate_total(100, 0.18) == 118


def test_payment_allowed_for_positive_amount():
    assert is_payment_allowed(100) is True


def test_payment_rejected_for_zero_amount():
    assert is_payment_allowed(0) is False