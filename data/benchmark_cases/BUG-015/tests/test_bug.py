from app.discount import calculate_discount

def test_discount_respects_maximum_cap():
    assert calculate_discount(200, 0.50, 60) == 60

def test_discount_below_cap_is_unchanged():
    assert calculate_discount(100, 0.20, 60) == 20

def test_discount_equal_to_cap_is_unchanged():
    assert calculate_discount(100, 0.60, 60) == 60
