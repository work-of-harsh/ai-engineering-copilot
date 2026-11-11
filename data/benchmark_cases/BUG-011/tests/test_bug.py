from app.date_filter import is_date_in_range

def test_start_date_is_included():
    assert is_date_in_range("2026-11-01", "2026-11-01", "2026-11-30") is True

def test_end_date_is_included():
    assert is_date_in_range("2026-11-30", "2026-11-01", "2026-11-30") is True

def test_date_inside_range_is_included():
    assert is_date_in_range("2026-11-15", "2026-11-01", "2026-11-30") is True
