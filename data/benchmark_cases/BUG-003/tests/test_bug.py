from app.shipping import shipping_fee

def test_free_shipping_at_threshold():
    assert shipping_fee(100) == 0
