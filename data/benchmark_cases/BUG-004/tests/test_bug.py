from app.retry import total_attempts

def test_retry_count_includes_initial_attempt():
    assert total_attempts(3) == 4
