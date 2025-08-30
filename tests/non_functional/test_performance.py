"""
Performance tests for the authentication system
Tests response times, throughput, and system behavior under load
"""

import pytest
import time
import threading
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from selenium.webdriver.common.by import By


@pytest.mark.performance
class TestResponseTimes:
    """Test response time performance"""
    
    def test_home_page_response_time(self, test_client):
        """Test home page response time"""
        start_time = time.time()
        response = test_client.get('/')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_api_health_response_time(self, test_client):
        """Test API health endpoint response time"""
        times = []
        
        # Test multiple times to get average
        for _ in range(10):
            start_time = time.time()
            response = test_client.get('/api/health')
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        assert avg_time < 0.1  # Average should be under 100ms
        assert max_time < 0.5   # Max should be under 500ms
    
    def test_login_response_time(self, test_client, registered_user):
        """Test login response time"""
        start_time = time.time()
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 302
        assert response_time < 2.0  # Should complete within 2 seconds
    
    def test_registration_response_time(self, test_client, test_user_data):
        """Test registration response time"""
        start_time = time.time()
        response = test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 302
        assert response_time < 3.0  # Should complete within 3 seconds (includes password hashing)
    
    def test_dashboard_response_time(self, test_client, authenticated_session):
        """Test dashboard response time for authenticated users"""
        start_time = time.time()
        response = authenticated_session.get('/dashboard')
        end_time = time.time()
        
        response_time = end_time - start_time
        
        assert response.status_code == 200
        assert response_time < 1.0  # Should respond within 1 second


@pytest.mark.performance
class TestThroughput:
    """Test system throughput under load"""
    
    def test_concurrent_health_checks(self, live_server):
        """Test concurrent health check requests"""
        def make_request():
            try:
                response = requests.get(f'{live_server}/api/health', timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # All requests should succeed
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.9  # At least 90% success rate
    
    def test_concurrent_user_registrations(self, live_server):
        """Test concurrent user registrations"""
        def register_user(user_id):
            try:
                response = requests.post(f'{live_server}/register', data={
                    'username': f'user{user_id}',
                    'email': f'user{user_id}@example.com',
                    'password': 'ValidPass123!',
                    'confirm_password': 'ValidPass123!'
                }, timeout=10)
                return response.status_code in [200, 302]
            except:
                return False
        
        # Test with 5 concurrent registrations
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_user, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # Most should succeed (some might fail due to timing)
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8  # At least 80% success rate
    
    def test_mixed_workload_performance(self, live_server, registered_user):
        """Test performance under mixed workload"""
        def health_check():
            try:
                response = requests.get(f'{live_server}/api/health', timeout=5)
                return response.status_code == 200
            except:
                return False
        
        def user_count():
            try:
                response = requests.get(f'{live_server}/api/users/count', timeout=5)
                return response.status_code == 200
            except:
                return False
        
        def login_attempt():
            try:
                response = requests.post(f'{live_server}/login', data={
                    'username': registered_user['username'],
                    'password': registered_user['password']
                }, timeout=10)
                return response.status_code in [200, 302]
            except:
                return False
        
        # Mix of different operations
        operations = [health_check] * 5 + [user_count] * 3 + [login_attempt] * 2
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(op) for op in operations]
            results = [future.result() for future in as_completed(futures)]
        
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.8  # At least 80% success rate under mixed load


@pytest.mark.performance
@pytest.mark.slow
class TestLoadTesting:
    """Load testing with higher volumes"""
    
    def test_sustained_load_health_endpoint(self, live_server):
        """Test sustained load on health endpoint"""
        def make_requests(duration_seconds=10):
            end_time = time.time() + duration_seconds
            request_count = 0
            success_count = 0
            
            while time.time() < end_time:
                try:
                    response = requests.get(f'{live_server}/api/health', timeout=2)
                    request_count += 1
                    if response.status_code == 200:
                        success_count += 1
                except:
                    request_count += 1
                
                time.sleep(0.1)  # 10 requests per second
            
            return request_count, success_count
        
        request_count, success_count = make_requests(10)
        
        assert request_count > 50  # Should handle at least 50 requests in 10 seconds
        success_rate = success_count / request_count if request_count > 0 else 0
        assert success_rate >= 0.95  # 95% success rate
    
    def test_memory_usage_under_load(self, live_server):
        """Test memory usage doesn't grow excessively under load"""
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        def make_requests():
            for _ in range(50):
                try:
                    requests.get(f'{live_server}/api/health', timeout=2)
                    requests.get(f'{live_server}/api/users/count', timeout=2)
                except:
                    pass
        
        # Run load test
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=make_requests)
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Check memory usage after load
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024  # 50MB
    
    def test_database_performance_under_load(self, live_server):
        """Test database performance under concurrent access"""
        def register_and_login(user_id):
            session = requests.Session()
            
            # Register
            register_response = session.post(f'{live_server}/register', data={
                'username': f'loadtest{user_id}',
                'email': f'loadtest{user_id}@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            }, timeout=10)
            
            if register_response.status_code == 302:
                # Login
                login_response = session.post(f'{live_server}/login', data={
                    'username': f'loadtest{user_id}',
                    'password': 'ValidPass123!'
                }, timeout=10)
                
                return login_response.status_code == 302
            
            return False
        
        # Test with multiple concurrent users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_and_login, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        success_rate = sum(results) / len(results) if results else 0
        assert success_rate >= 0.5  # At least 50% should succeed (relaxed for testing)


@pytest.mark.performance
class TestResourceUsage:
    """Test resource usage efficiency"""
    
    def test_cpu_usage_during_operations(self, test_client, test_user_data):
        """Test CPU usage during typical operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Measure CPU usage during registration
        cpu_before = process.cpu_percent()
        
        response = test_client.post('/register', data={
            'username': test_user_data['username'],
            'email': test_user_data['email'],
            'password': test_user_data['password'],
            'confirm_password': test_user_data['password']
        })
        
        time.sleep(0.1)  # Allow CPU measurement to stabilize
        cpu_after = process.cpu_percent()
        
        assert response.status_code == 302
        # CPU usage should be reasonable (this is a basic check)
        assert cpu_after < 90  # Should not max out CPU
    
    def test_response_size_efficiency(self, test_client):
        """Test that responses are reasonably sized"""
        # Test home page
        response = test_client.get('/')
        assert response.status_code == 200
        assert len(response.data) < 100000  # Less than 100KB
        
        # Test API responses
        response = test_client.get('/api/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(json.dumps(data)) < 1000  # Less than 1KB
        
        # Test login page
        response = test_client.get('/login')
        assert response.status_code == 200
        assert len(response.data) < 50000  # Less than 50KB
    
    def test_database_query_efficiency(self, test_client, registered_user):
        """Test database query efficiency"""
        # This is a basic test - in a real scenario you'd monitor actual DB queries
        
        start_time = time.time()
        
        # Login (involves database queries)
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': registered_user['password']
        })
        
        end_time = time.time()
        
        assert response.status_code == 302
        assert end_time - start_time < 1.0  # Should complete quickly
        
        # Check user count (database query)
        start_time = time.time()
        response = test_client.get('/api/users/count')
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 0.5  # Should be very fast


@pytest.mark.performance
class TestScalability:
    """Test system scalability characteristics"""
    
    def test_user_growth_impact(self, live_server):
        """Test impact of increasing user count on performance"""
        # Register multiple users and measure response times
        response_times = []
        
        for i in range(10):
            # Register user
            start_time = time.time()
            response = requests.post(f'{live_server}/register', data={
                'username': f'scaletest{i}',
                'email': f'scaletest{i}@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            }, timeout=10)
            end_time = time.time()
            
            if response.status_code == 302:
                response_times.append(end_time - start_time)
        
        # Response times should not degrade significantly
        if len(response_times) >= 5:
            early_avg = statistics.mean(response_times[:3])
            late_avg = statistics.mean(response_times[-3:])
            
            # Later registrations shouldn't be more than 2x slower
            assert late_avg < early_avg * 2
    
    def test_session_scalability(self, live_server):
        """Test handling of multiple concurrent sessions"""
        def create_session_and_login(user_id):
            session = requests.Session()
            
            # Register
            register_response = session.post(f'{live_server}/register', data={
                'username': f'session{user_id}',
                'email': f'session{user_id}@example.com',
                'password': 'ValidPass123!',
                'confirm_password': 'ValidPass123!'
            }, timeout=10)
            
            if register_response.status_code != 302:
                return False
            
            # Login
            login_response = session.post(f'{live_server}/login', data={
                'username': f'session{user_id}',
                'password': 'ValidPass123!'
            }, timeout=10)
            
            if login_response.status_code != 302:
                return False
            
            # Access dashboard
            dashboard_response = session.get(f'{live_server}/dashboard', timeout=10)
            return dashboard_response.status_code == 200
        
        # Test multiple concurrent sessions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_session_and_login, i) for i in range(8)]
            results = [future.result() for future in as_completed(futures)]
        
        success_rate = sum(results) / len(results) if results else 0
        assert success_rate >= 0.5  # At least 50% should succeed (relaxed for testing)


@pytest.mark.performance
@pytest.mark.ui
class TestUIPerformance:
    """Test UI performance using Selenium"""
    
    def test_page_load_times(self, chrome_driver, live_server):
        """Test page load times in browser"""
        driver = chrome_driver
        
        # Test home page
        start_time = time.time()
        driver.get(live_server)
        # Wait for page to be fully loaded
        driver.implicitly_wait(10)
        end_time = time.time()
        
        home_load_time = end_time - start_time
        assert home_load_time < 5.0  # Should load within 5 seconds
        
        # Test login page
        start_time = time.time()
        driver.get(f'{live_server}/login')
        driver.implicitly_wait(10)
        end_time = time.time()
        
        login_load_time = end_time - start_time
        assert login_load_time < 5.0  # Should load within 5 seconds
    
    def test_form_submission_performance(self, chrome_driver, live_server, test_user_data):
        """Test form submission performance"""
        driver = chrome_driver
        driver.get(f'{live_server}/register')
        
        # Fill form
        driver.find_element(By.ID, 'username').send_keys(test_user_data['username'])
        driver.find_element(By.ID, 'email').send_keys(test_user_data['email'])
        driver.find_element(By.ID, 'password').send_keys(test_user_data['password'])
        driver.find_element(By.ID, 'confirm_password').send_keys(test_user_data['password'])
        
        # Submit and measure time
        start_time = time.time()
        driver.find_element(By.ID, 'register-submit').click()
        
        # Wait for redirect
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        WebDriverWait(driver, 10).until(
            EC.url_contains('/login')
        )
        end_time = time.time()
        
        submission_time = end_time - start_time
        assert submission_time < 10.0  # Should complete within 10 seconds
    
    def test_javascript_performance(self, chrome_driver, live_server):
        """Test JavaScript performance"""
        driver = chrome_driver
        driver.get(f'{live_server}/register')
        
        # Test password validation JavaScript
        password_field = driver.find_element(By.ID, 'password')
        
        start_time = time.time()
        password_field.send_keys('TestPassword123!')
        time.sleep(0.5)  # Wait for JavaScript to process
        end_time = time.time()
        
        js_response_time = end_time - start_time
        assert js_response_time < 2.0  # JavaScript should respond quickly
