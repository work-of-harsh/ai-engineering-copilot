from app.timeout import get_timeout

def test_timeout_uses_configuration():
    assert get_timeout({"timeout_seconds": 10}) == 10

def test_timeout_uses_configured_large_value():
    assert get_timeout({"timeout_seconds": 60}) == 60

def test_timeout_defaults_when_configuration_is_missing():
    assert get_timeout({}) == 30
