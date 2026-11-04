from app.retry import total_attempts

def test_retry_count_includes_initial_attempt():
    assert total_attempts(3) == 4

def test_zero_retries_still_has_initial_attempt():
    assert total_attempts(0) == 1

def test_one_retry_has_two_total_attempts():
    assert total_attempts(1) == 2
