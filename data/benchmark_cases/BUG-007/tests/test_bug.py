from app.currency import round_currency

def test_currency_rounds_to_two_decimal_places():
    assert round_currency(10.126) == 10.13
