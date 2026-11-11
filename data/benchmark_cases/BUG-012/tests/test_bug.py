from app.orders import should_create_order

def test_existing_order_is_rejected():
    assert should_create_order(["ORD-101", "ORD-102"], "ORD-101") is False

def test_new_order_is_allowed():
    assert should_create_order(["ORD-101", "ORD-102"], "ORD-103") is True

def test_order_is_allowed_when_list_is_empty():
    assert should_create_order([], "ORD-101") is True
