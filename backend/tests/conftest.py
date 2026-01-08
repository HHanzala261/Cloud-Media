"""
Test configuration for MediaCloud backend tests
"""

import pytest
from app import create_app
from extensions import mongo
import os

@pytest.fixture(scope='session')
def app():
    """Create test Flask application"""
    # Set test environment variables
    os.environ['MONGO_URI'] = 'mongodb://localhost:27017/mediacloud_test'
    os.environ['DB_NAME'] = 'mediacloud_test'
    os.environ['JWT_SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        yield app

@pytest.fixture(scope='function')
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture(scope='function', autouse=True)
def clean_database(app):
    """Clean database before each test"""
    with app.app_context():
        # Clear all collections
        try:
            mongo.db.users.delete_many({})
            mongo.db.media.delete_many({})
        except Exception:
            pass  # Database might not be available
        yield
        # Clean up after test
        try:
            mongo.db.users.delete_many({})
            mongo.db.media.delete_many({})
        except Exception:
            pass  # Database might not be available