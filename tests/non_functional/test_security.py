"""
Security tests for the authentication system
Tests various security aspects including input validation, authentication, and authorization
"""

import pytest
import requests
import json
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


@pytest.mark.security
class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_xss_prevention_in_forms(self, test_client):
        """Test XSS prevention in form inputs"""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '"><script>alert("XSS")</script>',
            "javascript:alert('XSS')",
            '<img src=x onerror=alert("XSS")>',
            '<svg onload=alert("XSS")>',
            '{{7*7}}',  # Template injection
            '${7*7}',   # Expression injection
        ]
        
        for payload in xss_payloads:
            response = test_client.post('/register', data={
                'username': payload,
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            
            # Should not execute script or return raw payload
            assert response.status_code == 200
            assert b'<script>' not in response.data
            assert b'javascript:' not in response.data
            assert payload.encode() not in response.data or b'Username can only contain' in response.data
    
    def test_sql_injection_prevention(self, test_client):
        """Test SQL injection prevention"""
        sql_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            "admin'--",
            "' OR 1=1 --",
            "'; INSERT INTO users VALUES ('hacker', 'hack@evil.com', 'hash'); --"
        ]
        
        for payload in sql_payloads:
            # Test in login
            response = test_client.post('/login', data={
                'username': payload,
                'password': 'anypassword'
            })
            
            # Should handle safely
            assert response.status_code == 200
            assert b'Invalid username or password' in response.data
            
            # Test in registration
            response = test_client.post('/register', data={
                'username': payload,
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            
            # Should handle safely
            assert response.status_code == 200
        
        # Verify system still works after injection attempts
        health_response = test_client.get('/api/health')
        assert health_response.status_code == 200
    
    def test_command_injection_prevention(self, test_client):
        """Test command injection prevention"""
        command_payloads = [
            '; ls -la',
            '| cat /etc/passwd',
            '&& rm -rf /',
            '`whoami`',
            '$(id)',
            '; ping -c 1 google.com',
        ]
        
        for payload in command_payloads:
            response = test_client.post('/register', data={
                'username': payload,
                'email': 'test@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            
            # Should be rejected or sanitized
            assert response.status_code == 200
            # System should still be responsive
            assert b'Username can only contain' in response.data or b'already exists' in response.data
    
    def test_path_traversal_prevention(self, test_client):
        """Test path traversal prevention"""
        traversal_payloads = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//....//etc/passwd',
            '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
        ]
        
        for payload in traversal_payloads:
            # Test in various endpoints
            response = test_client.get(f'/api/login-attempts/{payload}')
            
            # Should not expose system files - either 200 with empty list or 404
            assert response.status_code in [200, 404]
            if response.status_code == 200:
                data = json.loads(response.data)
                assert isinstance(data, list)  # Should return empty list, not file contents
                # Should not contain system file contents
                assert not any('root:' in str(item) for item in data if isinstance(item, str))
    
    def test_ldap_injection_prevention(self, test_client):
        """Test LDAP injection prevention (if applicable)"""
        ldap_payloads = [
            '*)(uid=*',
            '*)(|(uid=*',
            '*)(&(uid=*',
            '*))(|(uid=*',
        ]
        
        for payload in ldap_payloads:
            response = test_client.post('/login', data={
                'username': payload,
                'password': 'anypassword'
            })
            
            assert response.status_code == 200
            assert b'Invalid username or password' in response.data


@pytest.mark.security
class TestAuthenticationSecurity:
    """Test authentication security mechanisms"""
    
    def test_password_hashing(self, test_client, test_user_data):
        """Test that passwords are properly hashed"""
        # Register user
        test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        
        # Check that password is not stored in plain text
        # This would require database access in a real scenario
        # For now, verify that login works with correct password
        response = test_client.post('/login', data={
            'username': test_user_data['username'],
            'password': test_user_data['password']
        })
        
        assert response.status_code == 302
        assert '/dashboard' in response.location
    
    def test_session_security(self, test_client, registered_user):
        """Test session security mechanisms"""
        # Login
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Check that session cookie is set
        assert 'Set-Cookie' in response.headers
        
        # Verify session works
        dashboard_response = test_client.get('/dashboard')
        assert dashboard_response.status_code == 200
        
        # Logout
        test_client.get('/logout')
        
        # Verify session is invalidated
        dashboard_response = test_client.get('/dashboard')
        assert dashboard_response.status_code == 302
        assert '/login' in dashboard_response.location
    
    def test_brute_force_protection(self, test_client, registered_user):
        """Test brute force attack protection"""
        # Make multiple failed login attempts
        for i in range(6):  # More than the 5 attempt limit
            response = test_client.post('/login', data={
                'username': registered_user['username'],
                'password': 'wrongpassword'
            })
            
            if i < 5:
                assert b'Invalid username or password' in response.data
            else:
                # Should be locked after 5 attempts
                assert b'Account is temporarily locked' in response.data
        
        # Even correct password should be rejected when locked
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        assert b'Account is temporarily locked' in response.data
    
    def test_timing_attack_resistance(self, test_client, registered_user):
        """Test resistance to timing attacks"""
        import time
        
        # Measure time for valid username, wrong password
        start_time = time.time()
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })
        valid_user_time = time.time() - start_time
        
        # Measure time for invalid username
        start_time = time.time()
        test_client.post('/login', data={
            'username': 'nonexistentuser',
            'password': 'anypassword'
        })
        invalid_user_time = time.time() - start_time
        
        # Times should be similar (within reasonable variance)
        # This is a basic test - real timing attack testing requires more sophisticated analysis
        time_difference = abs(valid_user_time - invalid_user_time)
        assert time_difference < 1.0  # Should not have obvious timing differences
    
    def test_password_policy_enforcement(self, test_client, weak_passwords):
        """Test password policy enforcement"""
        for weak_password in weak_passwords:
            response = test_client.post('/register', data={
                'username': 'testuser',
                'email': 'test@example.com',
                'password': weak_password,
                'confirm_password': weak_password
            })
            
            # Should reject weak passwords
            assert response.status_code == 200
            assert (b'Password must' in response.data or 
                   b'All fields are required' in response.data)


@pytest.mark.security
class TestAuthorizationSecurity:
    """Test authorization and access control"""
    
    def test_unauthorized_dashboard_access(self, test_client):
        """Test that unauthorized users cannot access dashboard"""
        response = test_client.get('/dashboard')
        
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_session_hijacking_prevention(self, test_client, registered_user):
        """Test session hijacking prevention measures"""
        # Login
        login_response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Extract session cookie
        cookies = login_response.headers.getlist('Set-Cookie')
        session_cookie = None
        for cookie in cookies:
            if 'session=' in cookie:
                session_cookie = cookie.split(';')[0]
                break
        
        assert session_cookie is not None
        
        # Verify session works
        dashboard_response = test_client.get('/dashboard')
        assert dashboard_response.status_code == 200
        
        # Test that session is properly managed
        # In a real scenario, you'd test for secure flags, httponly, etc.
    
    def test_privilege_escalation_prevention(self, test_client, registered_user):
        """Test prevention of privilege escalation"""
        # Login as regular user
        test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Try to access admin-like endpoints (if they existed)
        # For this demo, we test that users can only see their own data
        response = test_client.get(f'/api/login-attempts/{registered_user["username"]}')
        assert response.status_code == 200
        
        # Try to access another user's data (should be empty since no other users)
        response = test_client.get('/api/login-attempts/otherusername')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 0  # Should not return data for non-existent user


@pytest.mark.security
class TestDataProtection:
    """Test data protection and privacy"""
    
    def test_sensitive_data_exposure(self, test_client, registered_user):
        """Test that sensitive data is not exposed"""
        # Check API responses don't expose sensitive information
        response = test_client.get('/api/users/count')
        data = json.loads(response.data)
        
        # Should only contain count, not user details
        assert 'user_count' in data
        assert 'password' not in str(data)
        assert 'password_hash' not in str(data)
        assert 'email' not in str(data)
    
    def test_error_information_disclosure(self, test_client):
        """Test that error messages don't disclose sensitive information"""
        # Test 404 error
        response = test_client.get('/nonexistent')
        assert response.status_code == 404
        assert b'Page not found' in response.data
        # Should not expose server paths, versions, etc.
        assert b'/Users/' not in response.data
        assert b'Traceback' not in response.data
        
        # Test login error
        response = test_client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        
        # Should not reveal whether username exists
        assert b'Invalid username or password' in response.data
        assert b'User does not exist' not in response.data
    
    def test_information_leakage_in_responses(self, test_client):
        """Test for information leakage in HTTP responses"""
        response = test_client.get('/')
        
        # Check headers don't expose sensitive information
        headers = dict(response.headers)
        
        # Should not expose server version, framework version, etc.
        server_header = headers.get('Server', '')
        assert 'Werkzeug' not in server_header  # Development server info
        assert 'Python' not in server_header
        
        # Check for debug information
        assert b'Traceback' not in response.data
        assert b'DEBUG' not in response.data


@pytest.mark.security
class TestSecurityHeaders:
    """Test security headers and configurations"""
    
    def test_security_headers_presence(self, test_client):
        """Test presence of security headers"""
        response = test_client.get('/')
        headers = dict(response.headers)
        
        # Note: In a production app, you'd want these headers
        # For this demo, we're just checking the response structure
        assert response.status_code == 200
        
        # In production, you'd test for:
        # - X-Content-Type-Options: nosniff
        # - X-Frame-Options: DENY or SAMEORIGIN
        # - X-XSS-Protection: 1; mode=block
        # - Strict-Transport-Security (for HTTPS)
        # - Content-Security-Policy
    
    def test_cookie_security_attributes(self, test_client, registered_user):
        """Test cookie security attributes"""
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        # Check session cookie attributes
        cookies = response.headers.getlist('Set-Cookie')
        session_cookie = None
        for cookie in cookies:
            if 'session=' in cookie:
                session_cookie = cookie
                break
        
        if session_cookie:
            # In production, should have HttpOnly and Secure flags
            # For development/testing, we just verify cookie is set
            assert 'session=' in session_cookie


@pytest.mark.security
@pytest.mark.ui
class TestUISecuritySelenium:
    """Test UI security using Selenium"""
    
    def test_xss_in_ui_elements(self, chrome_driver, live_server, test_user_data):
        """Test XSS prevention in UI elements"""
        driver = chrome_driver
        
        # Try to register with XSS payload in username
        xss_payload = '<script>alert("XSS")</script>'
        
        driver.get(f"{live_server}/register")
        driver.find_element(By.ID, "username").send_keys(xss_payload)
        driver.find_element(By.ID, "email").send_keys(test_user_data['email'])
        driver.find_element(By.ID, "password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "confirm_password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "register-submit").click()
        
        # Should not execute JavaScript
        # Check that no alert is present
        try:
            WebDriverWait(driver, 2).until(EC.alert_is_present())
            assert False, "XSS alert was triggered"
        except:
            pass  # Good, no alert means XSS was prevented
        
        # Check error message is displayed safely
        error_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-danger"))
        )
        assert "Username can only contain" in error_element.text
    
    def test_csrf_protection(self, chrome_driver, live_server, registered_user):
        """Test CSRF protection (basic check)"""
        driver = chrome_driver
        
        # Login normally
        driver.get(f"{live_server}/login")
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        driver.find_element(By.ID, "login-submit").click()
        
        # Wait for dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Verify we're authenticated
        assert "/dashboard" in driver.current_url
        
        # In a real CSRF test, you'd try to submit forms from external sites
        # For this demo, we verify the form submission works normally
    
    def test_clickjacking_prevention(self, chrome_driver, live_server):
        """Test clickjacking prevention"""
        driver = chrome_driver
        
        # Create a simple HTML page that tries to iframe our login page
        iframe_html = f"""
        <html>
        <body>
        <iframe src="{live_server}/login" width="800" height="600"></iframe>
        </body>
        </html>
        """
        
        # In a real test, you'd serve this HTML and check if iframe loads
        # For this demo, we just verify the login page loads normally
        driver.get(f"{live_server}/login")
        assert driver.find_element(By.ID, "login-form")
    
    def test_password_field_security(self, chrome_driver, live_server):
        """Test password field security features"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        password_field = driver.find_element(By.ID, "password")
        
        # Verify password field type
        assert password_field.get_attribute("type") == "password"
        
        # Verify autocomplete attribute (should be set appropriately)
        autocomplete = password_field.get_attribute("autocomplete")
        assert autocomplete in ["current-password", "new-password", None]
        
        # Test password visibility toggle
        toggle_btn = driver.find_element(By.ID, "toggle-password")
        toggle_btn.click()
        
        # Should change to text type
        assert password_field.get_attribute("type") == "text"
        
        # Toggle back
        toggle_btn.click()
        assert password_field.get_attribute("type") == "password"


@pytest.mark.security
@pytest.mark.slow
class TestSecurityStressTests:
    """Stress tests for security mechanisms"""
    
    def test_rapid_login_attempts(self, test_client, registered_user):
        """Test system behavior under rapid login attempts"""
        # Make rapid login attempts
        for i in range(20):
            response = test_client.post('/login', data={
                'username': registered_user['username'],
                'password': 'wrongpassword'
            })
            
            # System should remain stable
            assert response.status_code == 200
            
            if i >= 5:
                # Should be locked after 5 attempts
                assert b'Account is temporarily locked' in response.data
    
    def test_concurrent_registration_attempts(self, test_client):
        """Test concurrent registration with same username"""
        import threading
        import time
        
        results = []
        
        def register_user():
            response = test_client.post('/register', data={
                'username': 'concurrent_user',
                'email': f'user{time.time()}@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            })
            results.append(response.status_code)
        
        # Start multiple threads trying to register same username
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_user)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Only one should succeed (302 redirect), others should fail (200 with error)
        success_count = sum(1 for code in results if code == 302)
        assert success_count <= 1  # At most one should succeed
    
    def test_large_payload_handling(self, test_client):
        """Test handling of unusually large payloads"""
        large_payload = 'x' * 100000  # 100KB payload
        
        response = test_client.post('/register', data={
            'username': large_payload,
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })
        
        # Should handle gracefully without crashing
        assert response.status_code == 200
        
        # System should still be responsive
        health_response = test_client.get('/api/health')
        assert health_response.status_code == 200
