def shipping_fee(order_total):
    if order_total > 100:
        return 0
    return 10
