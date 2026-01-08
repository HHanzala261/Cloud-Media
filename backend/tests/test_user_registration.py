"""
Property-based tests for user registration functionality
**Feature: mediacloud-mvp, Property 1: User registration creates valid accounts**
"""

import pytest
from hypothesis import given, strategies as st, settings
from models.user import User
from utils.security import hash_password, verify_password
from extensions import mongo
import bcrypt

# Test data generators
@st.composite
def valid_user_data(draw):
    """Generate valid user registration data"""
    first_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))).filter(lambda x: x.strip()))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))).filter(lambda x: x.strip()))
    
    # Generate unique email with timestamp to avoid duplicates - ASCII only
    import time
    import random
    username = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    domain = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    timestamp = str(int(time.time() * 1000000))  # microsecond timestamp
    random_suffix = str(random.randint(1000, 9999))
    email = f"{username}{timestamp}{random_suffix}@{domain}.{tld}".lower()
    
    password = draw(st.text(min_size=6, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Po'))))
    
    return {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': password
    }

class TestUserRegistration:
    """Property-based tests for user registration"""
    
    def setup_method(self):
        """Set up test database"""
        # Clear test database before each test
        try:
            mongo.db.users.delete_many({})
        except Exception:
            pass  # Database might not be available
    
    @given(user_data=valid_user_data())
    @settings(max_examples=20, deadline=None)
    def test_user_registration_creates_valid_accounts(self, user_data):
        """
        **Feature: mediacloud-mvp, Property 1: User registration creates valid accounts**
        
        For any valid user registration data (firstName, lastName, email, password),
        submitting through the registration endpoint should create a user account 
        in the database with a bcrypt-hashed password
        """
        # Arrange
        first_name = user_data['firstName']
        last_name = user_data['lastName']
        email = user_data['email']
        password = user_data['password']
        
        # Act - Hash password and create user
        password_hash = hash_password(password)
        user = User(
            firstName=first_name,
            lastName=last_name,
            email=email,
            passwordHash=password_hash
        )
        
        # Save user to database
        user.save()
        
        # Assert - Verify user was created correctly
        saved_user = User.find_by_email(email)
        
        assert saved_user is not None, "User should be saved to database"
        assert saved_user.firstName == first_name, "First name should match"
        assert saved_user.lastName == last_name, "Last name should match"
        assert saved_user.email == email.lower(), "Email should be stored in lowercase"
        assert saved_user.passwordHash is not None, "Password hash should be stored"
        assert saved_user.passwordHash != password, "Password should not be stored in plain text"
        
        # Verify password hash is bcrypt format
        assert saved_user.passwordHash.startswith('$2b$'), "Password should be bcrypt hashed"
        
        # Verify password can be verified
        assert verify_password(password, saved_user.passwordHash), "Password should be verifiable"
        
        # Verify user has creation timestamp
        assert saved_user.createdAt is not None, "User should have creation timestamp"
    
    @given(user_data=valid_user_data())
    @settings(max_examples=10, deadline=None)
    def test_password_hashing_security(self, user_data):
        """
        Test that password hashing is secure and consistent
        """
        password = user_data['password']
        
        # Hash the same password multiple times
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different (due to salt)
        assert hash1 != hash2, "Password hashes should be different due to salt"
        
        # Both hashes should verify the original password
        assert verify_password(password, hash1), "First hash should verify password"
        assert verify_password(password, hash2), "Second hash should verify password"
        
        # Wrong password should not verify
        wrong_password = password + "wrong"
        assert not verify_password(wrong_password, hash1), "Wrong password should not verify"
    
    @given(user_data=valid_user_data())
    @settings(max_examples=10, deadline=None)
    def test_email_normalization(self, user_data):
        """
        Test that email addresses are consistently normalized to lowercase
        """
        # Create email with mixed case
        original_email = user_data['email']
        mixed_case_email = ''.join(
            c.upper() if i % 2 == 0 else c.lower() 
            for i, c in enumerate(original_email)
        )
        
        password_hash = hash_password(user_data['password'])
        user = User(
            firstName=user_data['firstName'],
            lastName=user_data['lastName'],
            email=mixed_case_email,
            passwordHash=password_hash
        )
        
        user.save()
        
        # Verify email is stored in lowercase
        saved_user = User.find_by_email(mixed_case_email)
        assert saved_user.email == original_email.lower(), "Email should be normalized to lowercase"
        
        # Verify we can find user with any case variation
        found_user = User.find_by_email(mixed_case_email.upper())
        assert found_user is not None, "Should find user regardless of email case"
    
    def test_user_validation(self):
        """Test user data validation"""
        # Test valid data
        is_valid, errors = User.validate_user_data("John", "Doe", "john@example.com", "password123")
        assert is_valid, "Valid data should pass validation"
        assert len(errors) == 0, "Valid data should have no errors"
        
        # Test invalid data
        is_valid, errors = User.validate_user_data("", "", "invalid-email", "123")
        assert not is_valid, "Invalid data should fail validation"
        assert len(errors) > 0, "Invalid data should have errors"
    
    def test_email_validation(self):
        """Test email validation"""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org"
        ]
        
        invalid_emails = [
            "",
            "invalid",
            "@example.com",
            "user@",
            "user@.com"
        ]
        
        for email in valid_emails:
            assert User.validate_email(email), f"Email {email} should be valid"
        
        for email in invalid_emails:
            assert not User.validate_email(email), f"Email {email} should be invalid"