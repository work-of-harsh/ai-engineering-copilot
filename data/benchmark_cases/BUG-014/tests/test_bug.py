from app.pagination import get_page_offset

def test_first_page_starts_at_zero():
    assert get_page_offset(1, 10) == 0

def test_third_page_has_correct_offset():
    assert get_page_offset(3, 10) == 20

def test_second_page_has_correct_offset():
    assert get_page_offset(2, 25) == 25
