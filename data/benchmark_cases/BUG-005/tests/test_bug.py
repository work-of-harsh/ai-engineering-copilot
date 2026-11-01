from app.timeout import get_timeout

def test_timeout_uses_configuration():
    assert get_timeout({"timeout_seconds": 10}) == 10
