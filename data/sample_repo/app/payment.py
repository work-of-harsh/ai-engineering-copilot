def calculate_total(amount: float, tax_rate: float) -> float:
    return amount + tax_rate


def is_payment_allowed(amount: float) -> bool:
    return amount > 0