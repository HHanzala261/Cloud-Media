"""
Integration tests for complete user workflows in MediaCloud MVP
Tests end-to-end registration → login → upload → organize workflows
"""

import pytest
import json
import io
from flask import Flask
from app import create_app
from extensions import mongo
from models.user import User
from models.media import Media


class TestUserWorkflowIntegration:
    """Test complete user workflows from registration to media management"""
    
    @pytest.fixture
    def app(self):
        """Create test app instance"""
        app = create_app()
        app.config['TESTING'] = True
        app.config['DB_NAME'] = 'mediacloud_test'
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def clean_db(self, app):
        """Clean database before each test"""
        with app.app_context():
            # Clean up test data
            mongo.db.users.delete_many({'email': {'$regex': 'test.*@example.com'}})
            mongo.db.media.delete_many({})
        yield
        with app.app_context():
            # Clean up after test
            mongo.db.users.delete_many({'email': {'$regex': 'test.*@example.com'}})
            mongo.db.media.delete_many({})
    
    def test_complete_registration_login_workflow(self, client, clean_db):
        """Test complete registration → login workflow"""
        # Test user data
        user_data = {
            'firstName': 'Integration',
            'lastName': 'Test',
            'email': 'test.integration@example.com',
            'password': 'testpassword123'
        }
        
        # Step 1: Register user
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        
        assert response.status_code == 201
        register_data = json.loads(response.data)
        assert 'accessToken' in register_data
        assert 'user' in register_data
        assert register_data['user']['email'] == user_data['email']
        assert register_data['user']['firstName'] == user_data['firstName']
        
        registration_token = register_data['accessToken']
        user_id = register_data['user']['id']
        
        # Step 2: Verify token works for protected routes
        headers = {'Authorization': f'Bearer {registration_token}'}
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        me_data = json.loads(response.data)
        assert me_data['user']['id'] == user_id
        
        # Step 3: Login with same credentials
        login_data = {
            'email': user_data['email'],
            'password': user_data['password']
        }
        
        response = client.post('/api/auth/login',
                             json=login_data,
                             content_type='application/json')
        
        assert response.status_code == 200
        login_response = json.loads(response.data)
        assert 'accessToken' in login_response
        assert login_response['user']['id'] == user_id
        
        login_token = login_response['accessToken']
        
        # Step 4: Verify login token works
        headers = {'Authorization': f'Bearer {login_token}'}
        response = client.get('/api/auth/me', headers=headers)
        
        assert response.status_code == 200
        me_data = json.loads(response.data)
        assert me_data['user']['id'] == user_id
    
    def test_file_upload_and_organization_workflow(self, client, clean_db):
        """Test file upload → organize → retrieve workflow"""
        # Step 1: Register and login user
        user_data = {
            'firstName': 'Upload',
            'lastName': 'Test',
            'email': 'test.upload@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        assert response.status_code == 201
        
        auth_data = json.loads(response.data)
        token = auth_data['accessToken']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 2: Upload a test image
        # Create minimal PNG image data
        png_data = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x06\\x00\\x00\\x00\\x1f\\x15\\xc4\\x89\\x00\\x00\\x00\\nIDATx\\x9cc\\x00\\x01\\x00\\x00\\x05\\x00\\x01\\r\\n-\\xdb\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82'
        
        data = {
            'file': (io.BytesIO(png_data), 'test-image.png', 'image/png'),
            'title': 'Integration Test Image'
        }
        
        response = client.post('/api/media/upload',
                             data=data,
                             headers=headers,
                             content_type='multipart/form-data')
        
        assert response.status_code == 201
        upload_data = json.loads(response.data)
        assert 'id' in upload_data
        assert upload_data['title'] == 'Integration Test Image'
        assert upload_data['type'] == 'photo'
        assert upload_data['isFavorite'] == False
        assert upload_data['isDeleted'] == False
        
        media_id = upload_data['id']
        
        # Step 3: Retrieve media list
        response = client.get('/api/media', headers=headers)
        assert response.status_code == 200
        
        media_list = json.loads(response.data)
        assert 'items' in media_list
        assert len(media_list['items']) == 1
        assert media_list['items'][0]['id'] == media_id
        
        # Step 4: Mark as favorite
        response = client.patch(f'/api/media/{media_id}/favorite',
                              json={'isFavorite': True},
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 200
        favorite_data = json.loads(response.data)
        assert favorite_data['success'] == True
        
        # Step 5: Verify favorite status in media list
        response = client.get('/api/media?favorites=true', headers=headers)
        assert response.status_code == 200
        
        favorites_list = json.loads(response.data)
        assert len(favorites_list['items']) == 1
        assert favorites_list['items'][0]['id'] == media_id
        assert favorites_list['items'][0]['isFavorite'] == True
        
        # Step 6: Move to trash
        response = client.patch(f'/api/media/{media_id}/trash',
                              json={'isDeleted': True},
                              headers=headers,
                              content_type='application/json')
        
        assert response.status_code == 200
        trash_data = json.loads(response.data)
        assert trash_data['success'] == True
        
        # Step 7: Verify item is in trash
        response = client.get('/api/media?trash=true', headers=headers)
        assert response.status_code == 200
        
        trash_list = json.loads(response.data)
        assert len(trash_list['items']) == 1
        assert trash_list['items'][0]['id'] == media_id
        assert trash_list['items'][0]['isDeleted'] == True
        
        # Step 8: Verify item is not in regular media list
        response = client.get('/api/media', headers=headers)
        assert response.status_code == 200
        
        regular_list = json.loads(response.data)
        assert len(regular_list['items']) == 0
        
        # Step 9: Permanently delete
        response = client.delete(f'/api/media/{media_id}', headers=headers)
        assert response.status_code == 200
        
        delete_data = json.loads(response.data)
        assert delete_data['success'] == True
        
        # Step 10: Verify item is completely gone
        response = client.get('/api/media?trash=true', headers=headers)
        assert response.status_code == 200
        
        final_list = json.loads(response.data)
        assert len(final_list['items']) == 0
    
    def test_authentication_persistence_and_route_protection(self, client, clean_db):
        """Test authentication persistence and route protection"""
        # Step 1: Test unauthorized access is blocked
        response = client.get('/api/media')
        assert response.status_code == 401
        
        response = client.get('/api/auth/me')
        assert response.status_code == 401
        
        response = client.post('/api/media/upload',
                             data={'file': (io.BytesIO(b'test'), 'test.txt')})
        assert response.status_code == 401
        
        # Step 2: Register user and get token
        user_data = {
            'firstName': 'Auth',
            'lastName': 'Test',
            'email': 'test.auth@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        assert response.status_code == 201
        
        auth_data = json.loads(response.data)
        valid_token = auth_data['accessToken']
        
        # Step 3: Test valid token grants access
        headers = {'Authorization': f'Bearer {valid_token}'}
        
        response = client.get('/api/auth/me', headers=headers)
        assert response.status_code == 200
        
        response = client.get('/api/media', headers=headers)
        assert response.status_code == 200
        
        # Step 4: Test invalid token is rejected
        invalid_headers = {'Authorization': 'Bearer invalid.token.here'}
        
        response = client.get('/api/auth/me', headers=invalid_headers)
        assert response.status_code in [401, 422]  # JWT library may return 422 for malformed tokens
        
        response = client.get('/api/media', headers=invalid_headers)
        assert response.status_code in [401, 422]
        
        # Step 5: Test malformed authorization header
        malformed_headers = {'Authorization': 'InvalidFormat'}
        
        response = client.get('/api/auth/me', headers=malformed_headers)
        assert response.status_code in [401, 422]
    
    def test_media_filtering_and_search_workflow(self, client, clean_db):
        """Test media filtering by type and search functionality"""
        # Step 1: Setup authenticated user
        user_data = {
            'firstName': 'Filter',
            'lastName': 'Test',
            'email': 'test.filter@example.com',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        assert response.status_code == 201
        
        auth_data = json.loads(response.data)
        token = auth_data['accessToken']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Step 2: Upload different types of media
        # Upload image
        png_data = b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\x08\\x06\\x00\\x00\\x00\\x1f\\x15\\xc4\\x89\\x00\\x00\\x00\\nIDATx\\x9cc\\x00\\x01\\x00\\x00\\x05\\x00\\x01\\r\\n-\\xdb\\x00\\x00\\x00\\x00IEND\\xaeB`\\x82'
        
        image_data = {
            'file': (io.BytesIO(png_data), 'test-photo.png', 'image/png'),
            'title': 'Test Photo'
        }
        
        response = client.post('/api/media/upload',
                             data=image_data,
                             headers=headers,
                             content_type='multipart/form-data')
        assert response.status_code == 201
        photo_id = json.loads(response.data)['id']
        
        # Upload audio (simulated with proper MIME type)
        audio_data = {
            'file': (io.BytesIO(b'fake audio data'), 'test-audio.mp3', 'audio/mpeg'),
            'title': 'Test Audio'
        }
        
        response = client.post('/api/media/upload',
                             data=audio_data,
                             headers=headers,
                             content_type='multipart/form-data')
        assert response.status_code == 201
        audio_id = json.loads(response.data)['id']
        
        # Step 3: Test filtering by type
        # Get all media
        response = client.get('/api/media', headers=headers)
        assert response.status_code == 200
        all_media = json.loads(response.data)
        assert len(all_media['items']) == 2
        
        # Filter by photo type
        response = client.get('/api/media?type=photo', headers=headers)
        assert response.status_code == 200
        photos = json.loads(response.data)
        assert len(photos['items']) == 1
        assert photos['items'][0]['type'] == 'photo'
        assert photos['items'][0]['id'] == photo_id
        
        # Filter by audio type
        response = client.get('/api/media?type=audio', headers=headers)
        assert response.status_code == 200
        audio = json.loads(response.data)
        assert len(audio['items']) == 1
        assert audio['items'][0]['type'] == 'audio'
        assert audio['items'][0]['id'] == audio_id
        
        # Filter by video type (should be empty)
        response = client.get('/api/media?type=video', headers=headers)
        assert response.status_code == 200
        videos = json.loads(response.data)
        assert len(videos['items']) == 0
        
        # Step 4: Test favorites filtering
        # Mark photo as favorite
        response = client.patch(f'/api/media/{photo_id}/favorite',
                              json={'isFavorite': True},
                              headers=headers,
                              content_type='application/json')
        assert response.status_code == 200
        
        # Get favorites
        response = client.get('/api/media?favorites=true', headers=headers)
        assert response.status_code == 200
        favorites = json.loads(response.data)
        assert len(favorites['items']) == 1
        assert favorites['items'][0]['id'] == photo_id
        assert favorites['items'][0]['isFavorite'] == True
    
    def test_error_handling_workflow(self, client, clean_db):
        """Test error handling throughout the workflow"""
        # Step 1: Test duplicate registration
        user_data = {
            'firstName': 'Error',
            'lastName': 'Test',
            'email': 'test.error@example.com',
            'password': 'testpassword123'
        }
        
        # First registration should succeed
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        assert response.status_code == 201
        
        # Second registration should fail
        response = client.post('/api/auth/register', 
                             json=user_data,
                             content_type='application/json')
        assert response.status_code == 409
        error_data = json.loads(response.data)
        assert 'error' in error_data
        assert 'already exists' in error_data['error'].lower()
        
        # Step 2: Test invalid login credentials
        invalid_login = {
            'email': user_data['email'],
            'password': 'wrongpassword'
        }
        
        response = client.post('/api/auth/login',
                             json=invalid_login,
                             content_type='application/json')
        assert response.status_code == 401
        error_data = json.loads(response.data)
        assert 'error' in error_data
        
        # Step 3: Test invalid email format in registration
        invalid_user = {
            'firstName': 'Invalid',
            'lastName': 'Email',
            'email': 'not-an-email',
            'password': 'testpassword123'
        }
        
        response = client.post('/api/auth/register', 
                             json=invalid_user,
                             content_type='application/json')
        assert response.status_code == 400
        
        # Step 4: Test missing required fields
        incomplete_user = {
            'firstName': 'Incomplete',
            'email': 'incomplete@example.com'
            # Missing lastName and password
        }
        
        response = client.post('/api/auth/register', 
                             json=incomplete_user,
                             content_type='application/json')
        assert response.status_code == 400
        
        # Step 5: Test operations on non-existent media
        # First get a valid token
        response = client.post('/api/auth/login',
                             json={'email': user_data['email'], 'password': user_data['password']},
                             content_type='application/json')
        assert response.status_code == 200
        
        auth_data = json.loads(response.data)
        token = auth_data['accessToken']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Try to operate on non-existent media
        fake_media_id = '507f1f77bcf86cd799439011'  # Valid ObjectId format but doesn't exist
        
        response = client.patch(f'/api/media/{fake_media_id}/favorite',
                              json={'isFavorite': True},
                              headers=headers,
                              content_type='application/json')
        assert response.status_code == 404
        
        response = client.delete(f'/api/media/{fake_media_id}', headers=headers)
        assert response.status_code == 404


if __name__ == '__main__':
    pytest.main([__file__, '-v'])