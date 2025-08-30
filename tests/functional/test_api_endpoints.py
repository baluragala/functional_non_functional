"""
Functional API tests for the authentication system
Tests API endpoints and backend functionality
"""

import pytest
import json
from flask import url_for


@pytest.mark.functional
@pytest.mark.api
class TestAPIEndpoints:
    """Test API endpoints functionality"""
    
    def test_health_check_endpoint(self, test_client):
        """Test the health check API endpoint"""
        response = test_client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert 'version' in data
    
    def test_user_count_endpoint_empty(self, test_client):
        """Test user count endpoint with no users"""
        response = test_client.get('/api/users/count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_count'] == 0
    
    def test_user_count_endpoint_with_users(self, test_client, test_user_data):
        """Test user count endpoint after registering users"""
        # Register a user first
        test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        
        response = test_client.get('/api/users/count')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data['user_count'] == 1
    
    def test_login_attempts_endpoint_nonexistent_user(self, test_client):
        """Test login attempts endpoint for non-existent user"""
        response = test_client.get('/api/login-attempts/nonexistent')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_login_attempts_endpoint_with_attempts(self, test_client, registered_user):
        """Test login attempts endpoint after login attempts"""
        # Make a failed login attempt
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })
        
        # Make a successful login attempt
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        response = test_client.get(f'/api/login-attempts/{registered_user["username"]}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert isinstance(data, list)
        assert len(data) >= 2  # At least failed and successful attempts
        
        # Check data structure
        for attempt in data:
            assert 'username' in attempt
            assert 'ip_address' in attempt
            assert 'success' in attempt
            assert 'timestamp' in attempt


@pytest.mark.functional
@pytest.mark.api
class TestUserRegistrationAPI:
    """Test user registration through form submission"""
    
    def test_successful_registration(self, test_client, test_user_data):
        """Test successful user registration"""
        response = test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        
        # Should redirect to login page
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_registration_missing_fields(self, test_client):
        """Test registration with missing required fields"""
        response = test_client.post('/register', data={
            'username': '',
            'email': '',
            'password': ''
        })
        
        # Should return to registration page with error
        assert response.status_code == 200
        assert b'All fields are required' in response.data
    
    def test_registration_invalid_email(self, test_client, invalid_emails):
        """Test registration with invalid email formats"""
        for invalid_email in invalid_emails:
            response = test_client.post('/register', data={
                'username': 'testuser',
                'email': invalid_email,
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            
            assert response.status_code == 200
            assert b'Invalid email format' in response.data
    
    def test_registration_invalid_username(self, test_client, invalid_usernames):
        """Test registration with invalid usernames"""
        for invalid_username in invalid_usernames:
            response = test_client.post('/register', data={
                'username': invalid_username,
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            
            assert response.status_code == 200
            # Should contain username validation error
            assert (b'Username must be between' in response.data or 
                   b'Username can only contain' in response.data)
    
    def test_registration_weak_password(self, test_client, weak_passwords):
        """Test registration with weak passwords"""
        for weak_password in weak_passwords:
            response = test_client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': weak_password,
                'confirm_password': weak_password
            })
            
            assert response.status_code == 200
            # Should contain password validation error
            assert (b'Password must' in response.data or 
                   b'All fields are required' in response.data)
    
    def test_registration_password_mismatch(self, test_client):
        """Test registration with mismatched passwords"""
        response = test_client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'DifferentPass123!'
        })
        
        assert response.status_code == 200
        assert b'Passwords do not match' in response.data
    
    def test_registration_duplicate_username(self, test_client, registered_user):
        """Test registration with existing username"""
        response = test_client.post('/register', data={
            'username': registered_user['username'],
            'email': 'different@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data
    
    def test_registration_duplicate_email(self, test_client, registered_user):
        """Test registration with existing email"""
        response = test_client.post('/register', data={
            'username': 'differentuser',
            'email': registered_user['email'],
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })
        
        assert response.status_code == 200
        assert b'already exists' in response.data


@pytest.mark.functional
@pytest.mark.api
class TestUserLoginAPI:
    """Test user login through form submission"""
    
    def test_successful_login(self, test_client, registered_user):
        """Test successful user login"""
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Should redirect to dashboard
        assert response.status_code == 302
        assert '/dashboard' in response.location
    
    def test_login_missing_credentials(self, test_client):
        """Test login with missing credentials"""
        response = test_client.post('/login', data={
            'username': '',
            'password': ''
        })
        
        assert response.status_code == 200
        assert b'Username and password are required' in response.data
    
    def test_login_invalid_username(self, test_client):
        """Test login with non-existent username"""
        response = test_client.post('/login', data={
            'username': 'nonexistent',
            'password': 'anypassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_invalid_password(self, test_client, registered_user):
        """Test login with wrong password"""
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_login_account_locking(self, test_client, registered_user):
        """Test account locking after multiple failed attempts"""
        # Make 5 failed login attempts
        for _ in range(5):
            response = test_client.post('/login', data={
                'username': registered_user['username'],
                'password': 'wrongpassword'
            })
            assert response.status_code == 200
        
        # 6th attempt should show account locked message
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 200
        assert b'Account is temporarily locked' in response.data
        
        # Even correct password should be rejected when locked
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        assert response.status_code == 200
        assert b'Account is temporarily locked' in response.data


@pytest.mark.functional
@pytest.mark.api
class TestSessionManagement:
    """Test session management functionality"""
    
    def test_dashboard_requires_authentication(self, test_client):
        """Test that dashboard requires authentication"""
        response = test_client.get('/dashboard')
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_authenticated_dashboard_access(self, test_client, registered_user):
        """Test dashboard access after authentication"""
        # Login first
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Access dashboard
        response = test_client.get('/dashboard')
        
        assert response.status_code == 200
        assert registered_user['username'].encode() in response.data
    
    def test_logout_functionality(self, test_client, registered_user):
        """Test logout functionality"""
        # Login first
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Verify we can access dashboard
        response = test_client.get('/dashboard')
        assert response.status_code == 200
        
        # Logout
        response = test_client.get('/logout')
        
        # Should redirect to home page
        assert response.status_code == 302
        assert response.location.endswith('/')
        
        # Should no longer be able to access dashboard
        response = test_client.get('/dashboard')
        assert response.status_code == 302
        assert '/login' in response.location


@pytest.mark.functional
@pytest.mark.api
class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_404_error_page(self, test_client):
        """Test 404 error handling"""
        response = test_client.get('/nonexistent-page')
        
        assert response.status_code == 404
        assert b'Page not found' in response.data
    
    def test_method_not_allowed(self, test_client):
        """Test method not allowed errors"""
        # Try GET on POST-only endpoint
        response = test_client.get('/register', 
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
        
        # Should return the form page (GET is allowed for displaying form)
        assert response.status_code == 200
        
        # Try unsupported method
        response = test_client.put('/register')
        assert response.status_code == 405
    
    def test_large_input_handling(self, test_client):
        """Test handling of unusually large inputs"""
        large_string = 'x' * 10000
        
        response = test_client.post('/register', data={
            'username': large_string,
            'email': f'{large_string}@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })
        
        # Should handle gracefully (likely validation error)
        assert response.status_code == 200
        assert b'Username must be between' in response.data
    
    def test_special_characters_in_input(self, test_client):
        """Test handling of special characters in input"""
        special_chars = "!@#$%^&*()[]{}|\\:;\"'<>?,./"
        
        response = test_client.post('/register', data={
            'username': special_chars,
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })
        
        assert response.status_code == 200
        assert b'Username can only contain' in response.data
    
    def test_sql_injection_prevention(self, test_client):
        """Test SQL injection prevention"""
        malicious_input = "'; DROP TABLE users; --"
        
        response = test_client.post('/login', data={
            'username': malicious_input,
            'password': 'anypassword'
        })
        
        # Should handle safely without crashing
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
        
        # Verify users table still exists by checking health endpoint
        health_response = test_client.get('/api/health')
        assert health_response.status_code == 200


@pytest.mark.functional
@pytest.mark.api
class TestDataPersistence:
    """Test data persistence and database operations"""
    
    def test_user_data_persistence(self, test_client, test_user_data):
        """Test that user data persists across requests"""
        # Register user
        test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        
        # Verify user count increased
        response = test_client.get('/api/users/count')
        data = json.loads(response.data)
        assert data['user_count'] == 1
        
        # Login with registered credentials
        response = test_client.post('/login', data={
            'username': test_user_data['username'],
            'password': test_user_data['password']
        })
        
        assert response.status_code == 302
        assert '/dashboard' in response.location
    
    def test_login_attempts_logging(self, test_client, registered_user):
        """Test that login attempts are properly logged"""
        # Make login attempts
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })
        
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Check login attempts were logged
        response = test_client.get(f'/api/login-attempts/{registered_user["username"]}')
        data = json.loads(response.data)
        
        assert len(data) >= 2
        
        # Check we have both success and failure
        success_attempts = [a for a in data if a['success']]
        failed_attempts = [a for a in data if not a['success']]
        
        assert len(success_attempts) >= 1
        assert len(failed_attempts) >= 1
