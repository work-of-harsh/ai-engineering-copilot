def total_attempts(retry_count):
    attempts = 0
    for _ in range(retry_count):
        attempts += 1
    return attempts
