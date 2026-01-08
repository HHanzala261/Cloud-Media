#!/usr/bin/env python3
"""
Simple script to test authentication endpoints
"""

import requests
import json

BASE_URL = "http://localhost:5001/api/auth"

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    user_data = {
        "firstName": "John",
        "lastName": "Doe", 
        "email": "john.doe@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/register", json=user_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 201:
            print("✅ Registration successful!")
            return response.json()
        else:
            print("❌ Registration failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return None

def test_login():
    """Test user login"""
    print("\nTesting user login...")
    
    login_data = {
        "email": "john.doe@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json()
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\nTesting get current user...")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/me", headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Get current user successful!")
            return True
        else:
            print("❌ Get current user failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error getting current user: {e}")
        return False

def test_health_endpoint():
    """Test health endpoint"""
    print("Testing health endpoint...")
    
    try:
        response = requests.get("http://localhost:5001/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Health check successful!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error during health check: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing MediaCloud Authentication Endpoints\n")
    
    # Test health endpoint first
    if not test_health_endpoint():
        print("❌ Server is not responding. Make sure the backend is running on port 5001.")
        exit(1)
    
    # Test registration
    reg_response = test_registration()
    if not reg_response:
        exit(1)
    
    # Test login
    login_response = test_login()
    if not login_response:
        exit(1)
    
    # Test get current user with token from login
    token = login_response.get('accessToken')
    if token:
        test_get_current_user(token)
    
    print("\n🎉 All authentication tests completed!")