"""
Pytest configuration and fixtures for the authentication system tests
"""

import pytest
import os
import tempfile
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import threading
import time
import requests
from app import app, init_db

# Test configuration
TEST_DATABASE = 'test_users.db'
TEST_PORT = 5001
BASE_URL = f'http://localhost:{TEST_PORT}'

@pytest.fixture(scope='session')
def test_app():
    """Create and configure a test Flask application"""
    # Create a temporary database for testing
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['DATABASE'] = TEST_DATABASE
    
    # Override the database path in the app module
    import app as app_module
    app_module.DATABASE = TEST_DATABASE
    
    with app.app_context():
        init_db()
    
    yield app
    
    # Cleanup: Remove test database
    if os.path.exists(TEST_DATABASE):
        os.remove(TEST_DATABASE)

@pytest.fixture(scope='session')
def test_client(test_app):
    """Create a test client for the Flask application"""
    return test_app.test_client()

@pytest.fixture(scope='session')
def live_server(test_app):
    """Start a live server for Selenium tests"""
    from werkzeug.serving import make_server
    
    server = make_server('127.0.0.1', TEST_PORT, test_app, threaded=True)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    max_attempts = 30
    for _ in range(max_attempts):
        try:
            response = requests.get(f'{BASE_URL}/api/health', timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(0.5)
    else:
        pytest.fail("Test server failed to start")
    
    yield BASE_URL
    
    # Shutdown server
    server.shutdown()

@pytest.fixture
def chrome_driver():
    """Create a Chrome WebDriver instance for Selenium tests"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode for CI/CD
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    
    # Use webdriver-manager to automatically download and manage ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.implicitly_wait(10)
    
    yield driver
    
    driver.quit()

@pytest.fixture
def firefox_driver():
    """Create a Firefox WebDriver instance for cross-browser testing"""
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.firefox.service import Service as FirefoxService
    from webdriver_manager.firefox import GeckoDriverManager
    
    firefox_options = FirefoxOptions()
    firefox_options.add_argument('--headless')
    
    try:
        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=firefox_options)
        driver.implicitly_wait(10)
        
        yield driver
        
        driver.quit()
    except Exception as e:
        pytest.skip(f"Firefox driver not available: {e}")

@pytest.fixture
def test_user_data():
    """Test user data for registration and login tests"""
    return {
        'username': 'testuser123',
        'email': 'testuser@example.com',
        'password': 'TestPass123!',
        'invalid_password': 'weak'
    }

@pytest.fixture
def registered_user(test_client, test_user_data):
    """Create a registered user for login tests"""
    # Register the user
    response = test_client.post('/register', data={
        'username': test_user_data['username'],
        'email': test_user_data['email'],
        'password': test_user_data['password'],
        'confirm_password': test_user_data['password']
    })
    
    return test_user_data

@pytest.fixture
def authenticated_session(test_client, registered_user):
    """Create an authenticated session"""
    # Login the user
    response = test_client.post('/login', data={
        'username': registered_user['username'],
        'password': registered_user['password']
    })
    
    return test_client

@pytest.fixture(autouse=True)
def clean_database():
    """Clean the test database before each test"""
    if os.path.exists(TEST_DATABASE):
        conn = sqlite3.connect(TEST_DATABASE)
        conn.execute('DELETE FROM users')
        conn.execute('DELETE FROM login_attempts')
        conn.commit()
        conn.close()

# Pytest markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line("markers", "functional: mark test as functional test")
    config.addinivalue_line("markers", "security: mark test as security test")
    config.addinivalue_line("markers", "performance: mark test as performance test")
    config.addinivalue_line("markers", "ui: mark test as UI test")
    config.addinivalue_line("markers", "api: mark test as API test")
    config.addinivalue_line("markers", "slow: mark test as slow running")

# Test data generators
@pytest.fixture
def invalid_usernames():
    """Generate invalid usernames for testing"""
    return [
        '',  # Empty
        'ab',  # Too short
        'a' * 21,  # Too long
        'user@name',  # Invalid characters
        'user name',  # Spaces
        'user-name',  # Hyphens
        'user.name',  # Dots
        'user#name',  # Hash
    ]

@pytest.fixture
def invalid_emails():
    """Generate invalid emails for testing"""
    return [
        '',  # Empty
        'invalid',  # No @ symbol
        '@example.com',  # No local part
        'user@',  # No domain
        'user@.com',  # Invalid domain
        'user@example',  # No TLD
        'user name@example.com',  # Spaces
    ]

@pytest.fixture
def weak_passwords():
    """Generate weak passwords for testing"""
    return [
        '',  # Empty
        '123',  # Too short
        'password',  # No uppercase, numbers, or special chars
        'PASSWORD',  # No lowercase, numbers, or special chars
        'Password',  # No numbers or special chars
        'Password1',  # No special chars
        'password!',  # No uppercase or numbers
    ]
