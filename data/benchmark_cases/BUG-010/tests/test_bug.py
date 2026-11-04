from app.payment_validation import is_valid_payment

def test_negative_payment_is_rejected():
    assert is_valid_payment(-5) is False
