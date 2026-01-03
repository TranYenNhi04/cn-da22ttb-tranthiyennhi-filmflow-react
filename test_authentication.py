"""
Test authentication system
Run this to verify registration and login work correctly
"""
import requests
import json

API_BASE = "http://localhost:8000"

def test_register():
    """Test user registration"""
    print("\n" + "="*50)
    print("TEST 1: User Registration")
    print("="*50)
    
    payload = {
        "name": "Test User",
        "email": "testuser@example.com",
        "password": "password123"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/register", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
            return response.json()
        elif response.status_code == 400:
            print("ℹ️  User already exists (this is expected if you ran this before)")
            return None
        else:
            print("❌ Registration failed!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_login(email, password):
    """Test user login"""
    print("\n" + "="*50)
    print("TEST 2: User Login")
    print("="*50)
    
    payload = {
        "email": email,
        "password": password
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 200:
            print("✅ Login successful!")
            return response.json()
        else:
            print("❌ Login failed!")
            return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_wrong_password(email):
    """Test login with wrong password"""
    print("\n" + "="*50)
    print("TEST 3: Login with Wrong Password")
    print("="*50)
    
    payload = {
        "email": email,
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 401:
            print("✅ Correctly rejected wrong password!")
            return True
        else:
            print("❌ Should have rejected wrong password!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_nonexistent_user():
    """Test login with non-existent email"""
    print("\n" + "="*50)
    print("TEST 4: Login with Non-existent Email")
    print("="*50)
    
    payload = {
        "email": "nonexistent@example.com",
        "password": "anypassword"
    }
    
    try:
        response = requests.post(f"{API_BASE}/auth/login", json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 404:
            print("✅ Correctly reported email not found!")
            return True
        else:
            print("❌ Should have reported email not found!")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Authentication System Test")
    print("=" * 50)
    print(f"API Base URL: {API_BASE}")
    print("Make sure backend is running at http://localhost:8000")
    print()
    
    # Test 1: Register
    register_result = test_register()
    
    # Test 2: Login with correct password
    test_login("testuser@example.com", "password123")
    
    # Test 3: Login with wrong password
    test_wrong_password("testuser@example.com")
    
    # Test 4: Login with non-existent email
    test_nonexistent_user()
    
    print("\n" + "="*50)
    print("All Tests Completed!")
    print("="*50)
    print("\nYou can now:")
    print("1. Open http://localhost:3000 in browser")
    print("2. Try registering a new account")
    print("3. Login with your registered account")
    print("4. Test that wrong password is rejected")
