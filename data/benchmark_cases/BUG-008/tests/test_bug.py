from app.email_validation import is_company_email

def test_email_validation_is_case_insensitive():
    assert is_company_email("USER@EXAMPLE.COM") is True
