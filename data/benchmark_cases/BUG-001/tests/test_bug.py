from app.payment import calculate_total

def test_percentage_tax():
    assert calculate_total(100, 0.18) == 118
