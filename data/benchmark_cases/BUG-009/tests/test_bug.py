from app.inventory import can_fulfill_order

def test_out_of_stock_item_cannot_be_fulfilled():
    assert can_fulfill_order(0) is False
