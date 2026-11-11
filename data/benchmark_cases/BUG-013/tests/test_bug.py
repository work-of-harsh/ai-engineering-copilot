from app.user import get_display_name

def test_missing_name_returns_guest():
    assert get_display_name({}) == "Guest"

def test_null_name_returns_guest():
    assert get_display_name({"name": None}) == "Guest"

def test_existing_name_is_trimmed():
    assert get_display_name({"name": "  Harsh  "}) == "Harsh"
