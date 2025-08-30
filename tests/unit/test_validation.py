"""
Unit tests for validation functions
Tests individual functions in isolation
"""

import pytest
from app import validate_email, validate_password, validate_username


@pytest.mark.unit
class TestEmailValidation:
    """Test email validation function"""
    
    def test_valid_emails(self):
        """Test valid email formats"""
        valid_emails = [
            'user@example.com',
            'test.email@domain.co.uk',
            'user+tag@example.org',
            'firstname.lastname@company.com',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            assert validate_email(email) == True, f"Email {email} should be valid"
    
    def test_invalid_emails(self):
        """Test invalid email formats"""
        invalid_emails = [
            '',  # Empty
            'invalid',  # No @ symbol
            '@example.com',  # No local part
            'user@',  # No domain
            'user@.com',  # Invalid domain
            'user@example',  # No TLD
            'user name@example.com',  # Spaces
            'user@exam ple.com',  # Spaces in domain
            'user@@example.com',  # Double @
            'user@example..com',  # Double dots
        ]
        
        for email in invalid_emails:
            assert validate_email(email) == False, f"Email {email} should be invalid"


@pytest.mark.unit
class TestPasswordValidation:
    """Test password validation function"""
    
    def test_valid_passwords(self):
        """Test valid password formats"""
        valid_passwords = [
            'Password123!',
            'MySecure@Pass1',
            'Strong#Password2024',
            'Complex$Pass123',
            'Secure&Password1'
        ]
        
        for password in valid_passwords:
            is_valid, message = validate_password(password)
            assert is_valid == True, f"Password {password} should be valid: {message}"
            assert message == "Password is valid"
    
    def test_invalid_passwords(self):
        """Test invalid password formats"""
        invalid_cases = [
            ('', "Password must be at least 8 characters long"),
            ('short', "Password must be at least 8 characters long"),
            ('nouppercase123!', "Password must contain at least one uppercase letter"),
            ('NOLOWERCASE123!', "Password must contain at least one lowercase letter"),
            ('NoNumbers!', "Password must contain at least one digit"),
            ('NoSpecialChars123', "Password must contain at least one special character"),
        ]
        
        for password, expected_message in invalid_cases:
            is_valid, message = validate_password(password)
            assert is_valid == False, f"Password {password} should be invalid"
            assert message == expected_message, f"Expected message: {expected_message}, got: {message}"
    
    def test_password_edge_cases(self):
        """Test password edge cases"""
        # Exactly 8 characters with all requirements
        password = "Pass123!"
        is_valid, message = validate_password(password)
        assert is_valid == True
        
        # Very long password
        long_password = "A" * 100 + "a1!"
        is_valid, message = validate_password(long_password)
        assert is_valid == True
        
        # All special characters test
        special_chars = "!@#$%^&*(),.?\":{}|<>"
        for char in special_chars:
            test_password = f"Password1{char}"
            is_valid, message = validate_password(test_password)
            assert is_valid == True, f"Password with special char {char} should be valid"


@pytest.mark.unit
class TestUsernameValidation:
    """Test username validation function"""
    
    def test_valid_usernames(self):
        """Test valid username formats"""
        valid_usernames = [
            'user123',
            'test_user',
            'username',
            'user_name_123',
            'TestUser',
            'a' * 20,  # Maximum length
            'abc',     # Minimum length
        ]
        
        for username in valid_usernames:
            is_valid, message = validate_username(username)
            assert is_valid == True, f"Username {username} should be valid: {message}"
            assert message == "Username is valid"
    
    def test_invalid_usernames(self):
        """Test invalid username formats"""
        invalid_cases = [
            ('', "Username must be between 3 and 20 characters"),
            ('ab', "Username must be between 3 and 20 characters"),
            ('a' * 21, "Username must be between 3 and 20 characters"),
            ('user@name', "Username can only contain letters, numbers, and underscores"),
            ('user name', "Username can only contain letters, numbers, and underscores"),
            ('user-name', "Username can only contain letters, numbers, and underscores"),
            ('user.name', "Username can only contain letters, numbers, and underscores"),
            ('user#name', "Username can only contain letters, numbers, and underscores"),
        ]
        
        for username, expected_message in invalid_cases:
            is_valid, message = validate_username(username)
            assert is_valid == False, f"Username {username} should be invalid"
            assert message == expected_message, f"Expected message: {expected_message}, got: {message}"
    
    def test_username_edge_cases(self):
        """Test username edge cases"""
        # Only numbers
        is_valid, message = validate_username('123')
        assert is_valid == True
        
        # Only letters
        is_valid, message = validate_username('abc')
        assert is_valid == True
        
        # Only underscores (edge case)
        is_valid, message = validate_username('___')
        assert is_valid == True
        
        # Mixed case
        is_valid, message = validate_username('UserName123')
        assert is_valid == True


@pytest.mark.unit
class TestValidationIntegration:
    """Test validation functions working together"""
    
    def test_complete_user_data_validation(self):
        """Test validation of complete user registration data"""
        # Valid data
        username = "testuser123"
        email = "test@example.com"
        password = "SecurePass123!"
        
        username_valid, username_msg = validate_username(username)
        email_valid = validate_email(email)
        password_valid, password_msg = validate_password(password)
        
        assert username_valid == True
        assert email_valid == True
        assert password_valid == True
        assert username_msg == "Username is valid"
        assert password_msg == "Password is valid"
    
    def test_invalid_user_data_validation(self):
        """Test validation with invalid data"""
        # Invalid data
        username = "ab"  # Too short
        email = "invalid-email"
        password = "weak"  # Too weak
        
        username_valid, username_msg = validate_username(username)
        email_valid = validate_email(email)
        password_valid, password_msg = validate_password(password)
        
        assert username_valid == False
        assert email_valid == False
        assert password_valid == False
        assert "must be between" in username_msg
        assert "must be at least" in password_msg
    
    @pytest.mark.parametrize("username,email,password,expected_valid", [
        ("validuser", "valid@email.com", "ValidPass123!", True),
        ("ab", "valid@email.com", "ValidPass123!", False),  # Invalid username
        ("validuser", "invalid-email", "ValidPass123!", False),  # Invalid email
        ("validuser", "valid@email.com", "weak", False),  # Invalid password
        ("", "", "", False),  # All invalid
    ])
    def test_parametrized_validation(self, username, email, password, expected_valid):
        """Test validation with parametrized inputs"""
        username_valid, _ = validate_username(username) if username else (False, "")
        email_valid = validate_email(email) if email else False
        password_valid, _ = validate_password(password) if password else (False, "")
        
        all_valid = username_valid and email_valid and password_valid
        assert all_valid == expected_valid
