#!/usr/bin/env python3
"""
Integration test script for MediaCloud MVP
Tests the complete user workflow: registration → login → upload → organize
"""

import requests
import json
import time
import os
import sys
from io import BytesIO

# Configuration
BACKEND_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:4200"

class MediaCloudIntegrationTest:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_user = {
            "firstName": "Test",
            "lastName": "User",
            "email": "test@example.com",
            "password": "testpassword123"
        }
        self.uploaded_media_id = None
        
    def log(self, message):
        print(f"[TEST] {message}")
        
    def test_backend_health(self):
        """Test backend health endpoint"""
        self.log("Testing backend health...")
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('ok') and data.get('database') == 'connected':
                    self.log("✓ Backend is healthy and database is connected")
                    return True
                else:
                    self.log("✗ Backend health check failed - database not connected")
                    return False
            else:
                self.log(f"✗ Backend health check failed - status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Backend health check failed - {str(e)}")
            return False
    
    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        self.log("Testing frontend accessibility...")
        try:
            response = requests.get(FRONTEND_URL, timeout=5)
            if response.status_code == 200:
                self.log("✓ Frontend is accessible")
                return True
            else:
                self.log(f"✗ Frontend not accessible - status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Frontend not accessible - {str(e)}")
            return False
    
    def test_user_registration(self):
        """Test user registration workflow"""
        self.log("Testing user registration...")
        try:
            # First, try to clean up any existing test user
            self.cleanup_test_user()
            
            # Use a unique email for each test run
            import time
            unique_email = f"test{int(time.time())}@example.com"
            test_user_data = self.test_user.copy()
            test_user_data["email"] = unique_email
            
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/register",
                json=test_user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                if 'accessToken' in data and 'user' in data:
                    self.access_token = data['accessToken']
                    # Update test user email for subsequent tests
                    self.test_user["email"] = unique_email
                    self.log("✓ User registration successful")
                    self.log(f"  - User ID: {data['user']['id']}")
                    self.log(f"  - Email: {data['user']['email']}")
                    return True
                else:
                    self.log("✗ Registration response missing required fields")
                    return False
            else:
                self.log(f"✗ Registration failed - status {response.status_code}")
                if response.content:
                    self.log(f"  - Error: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Registration failed - {str(e)}")
            return False
    
    def test_user_login(self):
        """Test user login workflow"""
        self.log("Testing user login...")
        try:
            login_data = {
                "email": self.test_user["email"],
                "password": self.test_user["password"]
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'accessToken' in data and 'user' in data:
                    self.access_token = data['accessToken']
                    self.log("✓ User login successful")
                    return True
                else:
                    self.log("✗ Login response missing required fields")
                    return False
            else:
                self.log(f"✗ Login failed - status {response.status_code}")
                if response.content:
                    self.log(f"  - Error: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Login failed - {str(e)}")
            return False
    
    def test_protected_route_access(self):
        """Test protected route access with JWT token"""
        self.log("Testing protected route access...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = self.session.get(
                f"{BACKEND_URL}/api/auth/me",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'user' in data:
                    self.log("✓ Protected route access successful")
                    return True
                else:
                    self.log("✗ Protected route response missing user data")
                    return False
            else:
                self.log(f"✗ Protected route access failed - status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Protected route access failed - {str(e)}")
            return False
    
    def test_unauthorized_access(self):
        """Test that protected routes reject unauthorized access"""
        self.log("Testing unauthorized access rejection...")
        try:
            response = self.session.get(
                f"{BACKEND_URL}/api/media",
                timeout=10
            )
            
            if response.status_code == 401:
                self.log("✓ Unauthorized access properly rejected")
                return True
            else:
                self.log(f"✗ Unauthorized access not rejected - status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Unauthorized access test failed - {str(e)}")
            return False
    
    def create_test_file(self, filename, content, content_type):
        """Create a test file for upload"""
        return (filename, BytesIO(content.encode()), content_type)
    
    def test_media_upload(self):
        """Test media file upload"""
        self.log("Testing media upload...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Create a minimal PNG image (1x1 pixel transparent PNG)
            png_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82'
            
            files = {
                'file': ('test-image.png', BytesIO(png_data), 'image/png')
            }
            data = {
                'title': 'Test Image Upload'
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/media/upload",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 201:
                media_data = response.json()
                if 'id' in media_data and 'title' in media_data:
                    self.uploaded_media_id = media_data['id']
                    self.log("✓ Media upload successful")
                    self.log(f"  - Media ID: {media_data['id']}")
                    self.log(f"  - Title: {media_data['title']}")
                    self.log(f"  - Type: {media_data.get('type', 'unknown')}")
                    return True
                else:
                    self.log("✗ Upload response missing required fields")
                    return False
            else:
                self.log(f"✗ Media upload failed - status {response.status_code}")
                if response.content:
                    self.log(f"  - Error: {response.text}")
                return False
        except Exception as e:
            self.log(f"✗ Media upload failed - {str(e)}")
            return False
    
    def test_media_retrieval(self):
        """Test media retrieval and filtering"""
        self.log("Testing media retrieval...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test getting all media
            response = self.session.get(
                f"{BACKEND_URL}/api/media",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and isinstance(data['items'], list):
                    self.log(f"✓ Media retrieval successful - found {len(data['items'])} items")
                    
                    # Verify our uploaded media is in the list
                    if self.uploaded_media_id:
                        found_media = any(item['id'] == self.uploaded_media_id for item in data['items'])
                        if found_media:
                            self.log("✓ Uploaded media found in retrieval")
                        else:
                            self.log("✗ Uploaded media not found in retrieval")
                            return False
                    
                    return True
                else:
                    self.log("✗ Media retrieval response missing items array")
                    return False
            else:
                self.log(f"✗ Media retrieval failed - status {response.status_code}")
                return False
        except Exception as e:
            self.log(f"✗ Media retrieval failed - {str(e)}")
            return False
    
    def test_media_organization(self):
        """Test media organization features (favorite, trash)"""
        if not self.uploaded_media_id:
            self.log("⚠ Skipping media organization test - no uploaded media")
            return True
            
        self.log("Testing media organization...")
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            # Test favorite toggle
            response = self.session.patch(
                f"{BACKEND_URL}/api/media/{self.uploaded_media_id}/favorite",
                json={"isFavorite": True},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✓ Favorite toggle successful")
            else:
                self.log(f"✗ Favorite toggle failed - status {response.status_code}")
                return False
            
            # Test trash toggle
            response = self.session.patch(
                f"{BACKEND_URL}/api/media/{self.uploaded_media_id}/trash",
                json={"isDeleted": True},
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✓ Trash toggle successful")
                return True
            else:
                self.log(f"✗ Trash toggle failed - status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"✗ Media organization failed - {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test error handling scenarios"""
        self.log("Testing error handling...")
        try:
            # Test duplicate registration
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/register",
                json=self.test_user,
                timeout=10
            )
            
            if response.status_code == 409:  # Conflict for duplicate email
                self.log("✓ Duplicate registration properly rejected")
            else:
                self.log(f"⚠ Duplicate registration handling unexpected - status {response.status_code}")
            
            # Test invalid login
            invalid_login = {
                "email": self.test_user["email"],
                "password": "wrongpassword"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/auth/login",
                json=invalid_login,
                timeout=10
            )
            
            if response.status_code == 401:
                self.log("✓ Invalid login properly rejected")
                return True
            else:
                self.log(f"✗ Invalid login not properly rejected - status {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"✗ Error handling test failed - {str(e)}")
            return False
    
    def cleanup_test_user(self):
        """Clean up test user (best effort)"""
        try:
            # This is a simple cleanup - in a real scenario you might need admin endpoints
            pass
        except:
            pass
    
    def run_all_tests(self):
        """Run all integration tests"""
        self.log("Starting MediaCloud MVP Integration Tests")
        self.log("=" * 50)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Protected Route Access", self.test_protected_route_access),
            ("Unauthorized Access Rejection", self.test_unauthorized_access),
            ("Media Upload", self.test_media_upload),
            ("Media Retrieval", self.test_media_retrieval),
            ("Media Organization", self.test_media_organization),
            ("Error Handling", self.test_error_handling),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"✗ {test_name} failed with exception: {str(e)}")
                failed += 1
        
        self.log("\n" + "=" * 50)
        self.log(f"Integration Test Results:")
        self.log(f"✓ Passed: {passed}")
        self.log(f"✗ Failed: {failed}")
        self.log(f"Total: {passed + failed}")
        
        if failed == 0:
            self.log("🎉 All integration tests passed!")
            return True
        else:
            self.log("❌ Some integration tests failed!")
            return False

if __name__ == "__main__":
    tester = MediaCloudIntegrationTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)