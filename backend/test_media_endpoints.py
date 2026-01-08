#!/usr/bin/env python3
"""
Simple script to test media endpoints
"""

import requests
import json
import io

BASE_URL = "http://localhost:5001/api"

def register_and_login():
    """Register a test user and get JWT token"""
    print("Setting up test user...")
    
    # Register user
    user_data = {
        "firstName": "Test",
        "lastName": "User",
        "email": "testuser@example.com",
        "password": "password123"
    }
    
    try:
        # Try to register (might fail if user already exists)
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code not in [201, 409]:  # 409 = user already exists
            print(f"Registration failed: {response.json()}")
            return None
    except Exception as e:
        print(f"Registration error: {e}")
    
    # Login to get token
    login_data = {
        "email": "testuser@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token = response.json()['accessToken']
            print("✅ User authenticated successfully!")
            return token
        else:
            print(f"❌ Login failed: {response.json()}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_media_upload(token):
    """Test media file upload"""
    print("\nTesting media upload...")
    
    # Create a test file
    test_file_content = b"This is a test image file content"
    test_file = io.BytesIO(test_file_content)
    
    files = {
        'file': ('test_image.jpg', test_file, 'image/jpeg')
    }
    
    data = {
        'title': 'Test Image Upload'
    }
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.post(f"{BASE_URL}/media/upload", files=files, data=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Media upload successful!")
            return response.json()
        else:
            print("❌ Media upload failed!")
            return None
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return None

def test_get_media(token):
    """Test getting media list"""
    print("\nTesting get media list...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/media", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Get media list successful!")
            return response.json()
        else:
            print("❌ Get media list failed!")
            return None
            
    except Exception as e:
        print(f"❌ Get media error: {e}")
        return None

def test_toggle_favorite(token, media_id):
    """Test toggling favorite status"""
    print(f"\nTesting toggle favorite for media {media_id}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'isFavorite': True
    }
    
    try:
        response = requests.patch(f"{BASE_URL}/media/{media_id}/favorite", json=data, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Toggle favorite successful!")
            return True
        else:
            print("❌ Toggle favorite failed!")
            return False
            
    except Exception as e:
        print(f"❌ Toggle favorite error: {e}")
        return False

def test_get_favorites(token):
    """Test getting favorites"""
    print("\nTesting get favorites...")
    
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    try:
        response = requests.get(f"{BASE_URL}/media?favorites=true", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Get favorites successful!")
            return response.json()
        else:
            print("❌ Get favorites failed!")
            return None
            
    except Exception as e:
        print(f"❌ Get favorites error: {e}")
        return None

if __name__ == "__main__":
    print("🚀 Testing MediaCloud Media Endpoints\n")
    
    # Get authentication token
    token = register_and_login()
    if not token:
        print("❌ Failed to authenticate. Exiting.")
        exit(1)
    
    # Test media upload
    uploaded_media = test_media_upload(token)
    if not uploaded_media:
        print("❌ Upload test failed. Exiting.")
        exit(1)
    
    media_id = uploaded_media.get('id')
    
    # Test get media list
    media_list = test_get_media(token)
    if not media_list:
        print("❌ Get media test failed.")
    
    # Test toggle favorite
    if media_id:
        test_toggle_favorite(token, media_id)
        
        # Test get favorites
        test_get_favorites(token)
    
    print("\n🎉 All media endpoint tests completed!")