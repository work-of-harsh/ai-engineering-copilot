from app.quantity import is_valid_quantity

def test_zero_quantity_is_invalid():
    assert is_valid_quantity(0) is False
