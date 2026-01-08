"""
Property-based tests for email uniqueness functionality
**Feature: mediacloud-mvp, Property 2: Email uniqueness is enforced**
"""

import pytest
from hypothesis import given, strategies as st, settings
from models.user import User
from utils.security import hash_password
from extensions import mongo

# Test data generators
@st.composite
def valid_email(draw):
    """Generate valid email address"""
    import time
    import random
    username = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz0123456789'))
    domain = draw(st.text(min_size=1, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))
    tld = draw(st.sampled_from(['com', 'org', 'net', 'edu', 'gov']))
    timestamp = str(int(time.time() * 1000000))
    random_suffix = str(random.randint(1000, 9999))
    return f"{username}{timestamp}{random_suffix}@{domain}.{tld}".lower()

class TestEmailUniqueness:
    """Property-based tests for email uniqueness"""
    
    def setup_method(self):
        """Set up test database"""
        try:
            mongo.db.users.delete_many({})
        except Exception:
            pass
    
    @given(email=valid_email())
    @settings(max_examples=20, deadline=None)
    def test_email_uniqueness_is_enforced(self, email):
        """
        **Feature: mediacloud-mvp, Property 2: Email uniqueness is enforced**
        
        For any email address, attempting to register multiple users with the same email 
        should result in only the first registration succeeding, with subsequent attempts being rejected
        """
        # Arrange - Create first user with the email
        password_hash1 = hash_password("password123")
        user1 = User(
            firstName="John",
            lastName="Doe",
            email=email,
            passwordHash=password_hash1
        )
        
        # Act - Save first user (should succeed)
        user1.save()
        
        # Verify first user was saved
        saved_user1 = User.find_by_email(email)
        assert saved_user1 is not None, "First user should be saved successfully"
        
        # Arrange - Create second user with same email
        password_hash2 = hash_password("differentpassword")
        user2 = User(
            firstName="Jane",
            lastName="Smith",
            email=email,
            passwordHash=password_hash2
        )
        
        # Act & Assert - Attempt to save second user (should fail)
        with pytest.raises(ValueError, match="Email address already exists"):
            user2.save()
        
        # Verify only one user exists with this email
        all_users_with_email = list(mongo.db.users.find({'email': email.lower()}))
        assert len(all_users_with_email) == 1, "Only one user should exist with this email"
        
        # Verify the first user's data is intact
        final_user = User.find_by_email(email)
        assert final_user.firstName == "John", "First user's data should be preserved"
        assert final_user.lastName == "Doe", "First user's data should be preserved"
    
    def test_email_exists_check(self):
        """Test the email_exists utility method"""
        test_email = "test@example.com"
        
        # Initially email should not exist
        assert not User.email_exists(test_email), "Email should not exist initially"
        
        # Create user
        password_hash = hash_password("password123")
        user = User(
            firstName="Test",
            lastName="User",
            email=test_email,
            passwordHash=password_hash
        )
        user.save()
        
        # Now email should exist
        assert User.email_exists(test_email), "Email should exist after user creation"
        
        # Test case insensitive check
        assert User.email_exists(test_email.upper()), "Email check should be case insensitive"
    
    @given(email=valid_email())
    @settings(max_examples=10, deadline=None)
    def test_case_insensitive_uniqueness(self, email):
        """Test that email uniqueness is case insensitive"""
        # Create user with lowercase email
        password_hash = hash_password("password123")
        user1 = User(
            firstName="John",
            lastName="Doe",
            email=email.lower(),
            passwordHash=password_hash
        )
        user1.save()
        
        # Try to create user with uppercase email (should fail)
        user2 = User(
            firstName="Jane",
            lastName="Smith",
            email=email.upper(),
            passwordHash=password_hash
        )
        
        with pytest.raises(ValueError, match="Email address already exists"):
            user2.save()
        
        # Try with mixed case (should also fail)
        mixed_case_email = ''.join(
            c.upper() if i % 2 == 0 else c.lower() 
            for i, c in enumerate(email)
        )
        
        user3 = User(
            firstName="Bob",
            lastName="Wilson",
            email=mixed_case_email,
            passwordHash=password_hash
        )
        
        with pytest.raises(ValueError, match="Email address already exists"):
            user3.save()