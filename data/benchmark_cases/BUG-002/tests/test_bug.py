from app.discount import apply_discount

def test_discount_percentage():
    assert apply_discount(100, 0.20) == 80
