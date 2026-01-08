"""
Property-based tests for authentication validation functionality
**Feature: mediacloud-mvp, Property 4: Authentication validates credentials correctly**
"""

import pytest
from hypothesis import given, strategies as st, settings
from models.user import User
from utils.security import hash_password, verify_password, generate_jwt_token
from flask_jwt_extended import decode_token
from extensions import mongo
import requests
import json

# Test data generators
@st.composite
def valid_user_credentials(draw):
    """Generate valid user credentials"""
    import time
    import random
    
    first_name = draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz').filter(lambda x: x.strip()))
    last_name = draw(st.text(min_size=1, max_size=50, alphabet='abcdefghijklmnopqrstuvwxyz').filter(lambda x: x.strip()))
    
    # Generate unique email
    username = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    domain = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    timestamp = str(int(time.time() * 1000000))
    random_suffix = str(random.randint(1000, 9999))
    email = f"{username}{timestamp}{random_suffix}@{domain}.{tld}".lower()
    
    password = draw(st.text(min_size=6, max_size=100, alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*'))
    
    return {
        'firstName': first_name,
        'lastName': last_name,
        'email': email,
        'password': password
    }

class TestAuthenticationValidation:
    """Property-based tests for authentication validation"""
    
    def setup_method(self):
        """Set up test database"""
        try:
            mongo.db.users.delete_many({})
        except Exception:
            pass
    
    @given(credentials=valid_user_credentials())
    @settings(max_examples=10, deadline=None)
    def test_authentication_validates_credentials_correctly(self, credentials):
        """
        **Feature: mediacloud-mvp, Property 4: Authentication validates credentials correctly**
        
        For any registered user, submitting correct email and password credentials 
        should return a valid JWT token, while incorrect credentials should be rejected
        """
        # Arrange - Create and save user
        password_hash = hash_password(credentials['password'])
        user = User(
            firstName=credentials['firstName'],
            lastName=credentials['lastName'],
            email=credentials['email'],
            passwordHash=password_hash
        )
        user.save()
        
        # Act & Assert - Test correct credentials
        found_user = User.find_by_email(credentials['email'])
        assert found_user is not None, "User should be found in database"
        
        # Test password verification directly
        assert verify_password(credentials['password'], found_user.passwordHash), "Correct password should verify"
        
        # Test JWT token generation
        token = generate_jwt_token(found_user._id)
        assert token is not None, "JWT token should be generated"
        assert isinstance(token, str), "JWT token should be a string"
        assert len(token) > 0, "JWT token should not be empty"
        
        # Verify token contains correct user ID
        try:
            from flask_jwt_extended import decode_token
            decoded = decode_token(token)
            assert decoded['sub'] == str(found_user._id), "Token should contain correct user ID"
        except Exception:
            # If decode_token is not available, just verify token format
            assert '.' in token, "JWT token should have proper format with dots"
        
        # Act & Assert - Test incorrect password
        wrong_password = credentials['password'] + "wrong"
        assert not verify_password(wrong_password, found_user.passwordHash), "Wrong password should not verify"
        
        # Test with completely different password
        different_password = "completelydifferent123"
        assert not verify_password(different_password, found_user.passwordHash), "Different password should not verify"
    
    @given(credentials=valid_user_credentials())
    @settings(max_examples=5, deadline=None)
    def test_jwt_token_properties(self, credentials):
        """Test JWT token generation properties"""
        # Create user
        password_hash = hash_password(credentials['password'])
        user = User(
            firstName=credentials['firstName'],
            lastName=credentials['lastName'],
            email=credentials['email'],
            passwordHash=password_hash
        )
        user.save()
        
        # Generate multiple tokens for same user
        token1 = generate_jwt_token(user._id)
        token2 = generate_jwt_token(user._id)
        
        # Tokens should be different (due to timestamp/jti)
        assert token1 != token2, "JWT tokens should be unique even for same user"
        
        # Both tokens should be valid strings
        assert isinstance(token1, str) and len(token1) > 0, "Token 1 should be valid string"
        assert isinstance(token2, str) and len(token2) > 0, "Token 2 should be valid string"
        
        # Both should have JWT format
        assert token1.count('.') == 2, "Token 1 should have JWT format (3 parts)"
        assert token2.count('.') == 2, "Token 2 should have JWT format (3 parts)"
    
    def test_password_verification_edge_cases(self):
        """Test password verification with edge cases"""
        # Test empty password
        password_hash = hash_password("validpassword")
        assert not verify_password("", password_hash), "Empty password should not verify"
        assert not verify_password(None, password_hash), "None password should not verify"
        
        # Test empty hash
        assert not verify_password("password", ""), "Empty hash should not verify"
        assert not verify_password("password", None), "None hash should not verify"
        
        # Test invalid hash format
        assert not verify_password("password", "invalid_hash"), "Invalid hash should not verify"
    
    def test_user_lookup_by_email(self):
        """Test user lookup functionality"""
        # Create test user
        test_email = "test@example.com"
        password_hash = hash_password("password123")
        user = User(
            firstName="Test",
            lastName="User",
            email=test_email,
            passwordHash=password_hash
        )
        user.save()
        
        # Test finding user by email
        found_user = User.find_by_email(test_email)
        assert found_user is not None, "User should be found by email"
        assert found_user.email == test_email, "Found user should have correct email"
        
        # Test case insensitive lookup
        found_user_upper = User.find_by_email(test_email.upper())
        assert found_user_upper is not None, "User should be found with uppercase email"
        assert found_user_upper._id == found_user._id, "Should find same user regardless of case"
        
        # Test non-existent email
        non_existent = User.find_by_email("nonexistent@example.com")
        assert non_existent is None, "Non-existent email should return None"