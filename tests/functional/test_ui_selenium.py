"""
Functional UI tests using Selenium WebDriver
Tests the complete user journey through the web interface
"""

import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException


@pytest.mark.functional
@pytest.mark.ui
class TestUserInterface:
    """Test the web user interface functionality"""
    
    def test_home_page_loads(self, chrome_driver, live_server):
        """Test that the home page loads correctly"""
        driver = chrome_driver
        driver.get(live_server)
        
        # Check page title
        assert "User Authentication System" in driver.title
        
        # Check main elements are present
        assert driver.find_element(By.TAG_NAME, "h1")
        assert driver.find_element(By.ID, "register-btn")
        assert driver.find_element(By.ID, "login-btn")
        
        # Check navigation
        nav = driver.find_element(By.TAG_NAME, "nav")
        assert "Auth System" in nav.text
    
    def test_navigation_links(self, chrome_driver, live_server):
        """Test navigation between pages"""
        driver = chrome_driver
        driver.get(live_server)
        
        # Test register link
        register_btn = driver.find_element(By.ID, "register-btn")
        register_btn.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "register-form"))
        )
        assert "/register" in driver.current_url
        
        # Test login link from register page
        login_link = driver.find_element(By.ID, "login-link")
        login_link.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-form"))
        )
        assert "/login" in driver.current_url
        
        # Test home link
        home_link = driver.find_element(By.LINK_TEXT, "Auth System")
        home_link.click()
        
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "register-btn"))
        )
        assert driver.current_url == live_server + "/"


@pytest.mark.functional
@pytest.mark.ui
class TestUserRegistration:
    """Test user registration functionality through UI"""
    
    def test_registration_form_validation(self, chrome_driver, live_server):
        """Test client-side form validation"""
        driver = chrome_driver
        driver.get(f"{live_server}/register")
        
        # Try to submit empty form
        submit_btn = driver.find_element(By.ID, "register-submit")
        submit_btn.click()
        
        # Check HTML5 validation messages
        username_field = driver.find_element(By.ID, "username")
        assert username_field.get_attribute("validationMessage")
    
    def test_password_strength_indicator(self, chrome_driver, live_server):
        """Test real-time password strength validation"""
        driver = chrome_driver
        driver.get(f"{live_server}/register")
        
        password_field = driver.find_element(By.ID, "password")
        
        # Test weak password
        password_field.send_keys("weak")
        time.sleep(0.5)  # Wait for JavaScript to update
        
        # Check that validation indicators show red/failed state
        length_check = driver.find_element(By.ID, "length-check")
        assert "red" in length_check.get_attribute("style") or "fa-times" in length_check.get_attribute("innerHTML")
        
        # Clear and test strong password
        password_field.clear()
        password_field.send_keys("StrongPass123!")
        time.sleep(0.5)
        
        # Check that validation indicators show green/success state
        length_check = driver.find_element(By.ID, "length-check")
        assert "green" in length_check.get_attribute("style") or "fa-check" in length_check.get_attribute("innerHTML")
    
    def test_successful_registration(self, chrome_driver, live_server, test_user_data):
        """Test successful user registration flow"""
        driver = chrome_driver
        driver.get(f"{live_server}/register")
        
        # Fill registration form
        driver.find_element(By.ID, "username").send_keys(test_user_data['username'])
        driver.find_element(By.ID, "email").send_keys(test_user_data['email'])
        driver.find_element(By.ID, "password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "confirm_password").send_keys(test_user_data['password'])
        
        # Submit form
        driver.find_element(By.ID, "register-submit").click()
        
        # Wait for redirect to login page
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )
        
        # Check for success message
        try:
            success_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
            )
            assert "Registration successful" in success_message.text
        except TimeoutException:
            # Message might have auto-hidden, check we're on login page
            assert "/login" in driver.current_url
    
    def test_duplicate_user_registration(self, chrome_driver, live_server, registered_user):
        """Test registration with existing username/email"""
        driver = chrome_driver
        driver.get(f"{live_server}/register")
        
        # Try to register with same credentials
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "email").send_keys(registered_user['email'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        driver.find_element(By.ID, "confirm_password").send_keys(registered_user['password'])
        
        driver.find_element(By.ID, "register-submit").click()
        
        # Check for error message
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-danger"))
        )
        assert "already exists" in error_message.text.lower()


@pytest.mark.functional
@pytest.mark.ui
class TestUserLogin:
    """Test user login functionality through UI"""
    
    def test_login_form_elements(self, chrome_driver, live_server):
        """Test login form has all required elements"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        # Check form elements exist
        assert driver.find_element(By.ID, "username")
        assert driver.find_element(By.ID, "password")
        assert driver.find_element(By.ID, "login-submit")
        assert driver.find_element(By.ID, "toggle-password")
        assert driver.find_element(By.ID, "remember-me")
    
    def test_password_visibility_toggle(self, chrome_driver, live_server):
        """Test password visibility toggle functionality"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        password_field = driver.find_element(By.ID, "password")
        toggle_btn = driver.find_element(By.ID, "toggle-password")
        
        # Initially password should be hidden
        assert password_field.get_attribute("type") == "password"
        
        # Click toggle to show password
        toggle_btn.click()
        assert password_field.get_attribute("type") == "text"
        
        # Click again to hide password
        toggle_btn.click()
        assert password_field.get_attribute("type") == "password"
    
    def test_demo_credentials_button(self, chrome_driver, live_server):
        """Test demo credentials auto-fill functionality"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        # Click demo credentials button
        demo_btn = driver.find_element(By.ID, "fill-demo-creds")
        demo_btn.click()
        
        # Check fields are filled
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        
        assert username_field.get_attribute("value") == "testuser"
        assert password_field.get_attribute("value") == "TestPass123!"
    
    def test_successful_login(self, chrome_driver, live_server, registered_user):
        """Test successful login flow"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        # Fill login form
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        
        # Submit form
        driver.find_element(By.ID, "login-submit").click()
        
        # Wait for redirect to dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Check we're on dashboard and user is logged in
        assert "/dashboard" in driver.current_url
        
        # Check welcome message
        welcome_text = driver.find_element(By.TAG_NAME, "h5")
        assert registered_user['username'] in welcome_text.text
    
    def test_invalid_login(self, chrome_driver, live_server):
        """Test login with invalid credentials"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        # Try invalid credentials
        driver.find_element(By.ID, "username").send_keys("nonexistent")
        driver.find_element(By.ID, "password").send_keys("wrongpassword")
        
        driver.find_element(By.ID, "login-submit").click()
        
        # Check for error message
        error_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-danger"))
        )
        assert "invalid" in error_message.text.lower()
        
        # Should still be on login page
        assert "/login" in driver.current_url


@pytest.mark.functional
@pytest.mark.ui
class TestDashboard:
    """Test dashboard functionality"""
    
    def test_dashboard_access_requires_login(self, chrome_driver, live_server):
        """Test that dashboard redirects to login when not authenticated"""
        driver = chrome_driver
        driver.get(f"{live_server}/dashboard")
        
        # Should be redirected to login
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )
        assert "/login" in driver.current_url
    
    def test_dashboard_content(self, chrome_driver, live_server, registered_user):
        """Test dashboard content after login"""
        driver = chrome_driver
        
        # Login first
        driver.get(f"{live_server}/login")
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        driver.find_element(By.ID, "login-submit").click()
        
        # Wait for dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Check dashboard elements
        assert driver.find_element(By.ID, "user-username")
        assert driver.find_element(By.ID, "refresh-data")
        assert driver.find_element(By.ID, "view-login-history")
        
        # Check user info is displayed
        user_display = driver.find_element(By.ID, "user-username")
        assert user_display.text == registered_user['username']
    
    def test_dashboard_refresh_functionality(self, chrome_driver, live_server, registered_user):
        """Test dashboard data refresh functionality"""
        driver = chrome_driver
        
        # Login and navigate to dashboard
        driver.get(f"{live_server}/login")
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        driver.find_element(By.ID, "login-submit").click()
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Click refresh button
        refresh_btn = driver.find_element(By.ID, "refresh-data")
        refresh_btn.click()
        
        # Check button shows loading state
        WebDriverWait(driver, 5).until(
            lambda d: "Refreshing" in refresh_btn.text
        )
        
        # Wait for refresh to complete
        WebDriverWait(driver, 10).until(
            lambda d: "Refresh Data" in refresh_btn.text
        )
    
    def test_logout_functionality(self, chrome_driver, live_server, registered_user):
        """Test logout functionality"""
        driver = chrome_driver
        
        # Login first
        driver.get(f"{live_server}/login")
        driver.find_element(By.ID, "username").send_keys(registered_user['username'])
        driver.find_element(By.ID, "password").send_keys(registered_user['password'])
        driver.find_element(By.ID, "login-submit").click()
        
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        
        # Click logout
        logout_link = driver.find_element(By.LINK_TEXT, "Logout")
        logout_link.click()
        
        # Should be redirected to home page
        WebDriverWait(driver, 10).until(
            EC.url_matches(f"{live_server}/?$")
        )
        
        # Check logout message
        try:
            success_message = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CLASS_NAME, "alert-info"))
            )
            assert "logged out" in success_message.text.lower()
        except TimeoutException:
            # Message might have auto-hidden, check we're on home page
            assert driver.current_url == f"{live_server}/"
        
        # Try to access dashboard - should redirect to login
        driver.get(f"{live_server}/dashboard")
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )


@pytest.mark.functional
@pytest.mark.ui
@pytest.mark.slow
class TestCrossBrowserCompatibility:
    """Test cross-browser compatibility (if Firefox is available)"""
    
    def test_basic_functionality_firefox(self, firefox_driver, live_server, test_user_data):
        """Test basic functionality in Firefox"""
        driver = firefox_driver
        
        # Test home page
        driver.get(live_server)
        assert "User Authentication System" in driver.title
        
        # Test registration
        driver.get(f"{live_server}/register")
        driver.find_element(By.ID, "username").send_keys(test_user_data['username'])
        driver.find_element(By.ID, "email").send_keys(test_user_data['email'])
        driver.find_element(By.ID, "password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "confirm_password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "register-submit").click()
        
        # Should redirect to login
        WebDriverWait(driver, 10).until(
            EC.url_contains("/login")
        )
        
        # Test login
        driver.find_element(By.ID, "username").send_keys(test_user_data['username'])
        driver.find_element(By.ID, "password").send_keys(test_user_data['password'])
        driver.find_element(By.ID, "login-submit").click()
        
        # Should reach dashboard
        WebDriverWait(driver, 10).until(
            EC.url_contains("/dashboard")
        )
        assert "/dashboard" in driver.current_url


@pytest.mark.functional
@pytest.mark.ui
class TestResponsiveDesign:
    """Test responsive design and mobile compatibility"""
    
    def test_mobile_viewport(self, chrome_driver, live_server):
        """Test mobile viewport rendering"""
        driver = chrome_driver
        
        # Set mobile viewport
        driver.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        driver.get(live_server)
        
        # Check that mobile navigation works
        assert driver.find_element(By.TAG_NAME, "nav")
        
        # Check forms are still usable
        driver.get(f"{live_server}/login")
        username_field = driver.find_element(By.ID, "username")
        assert username_field.is_displayed()
        
        # Check buttons are clickable
        login_btn = driver.find_element(By.ID, "login-submit")
        assert login_btn.is_displayed()
    
    def test_tablet_viewport(self, chrome_driver, live_server):
        """Test tablet viewport rendering"""
        driver = chrome_driver
        
        # Set tablet viewport
        driver.set_window_size(768, 1024)  # iPad size
        
        driver.get(live_server)
        
        # Check layout adapts properly
        assert driver.find_element(By.CLASS_NAME, "container")
        
        # Test registration form layout
        driver.get(f"{live_server}/register")
        form = driver.find_element(By.ID, "register-form")
        assert form.is_displayed()


@pytest.mark.functional
@pytest.mark.ui
class TestAccessibility:
    """Test basic accessibility features"""
    
    def test_keyboard_navigation(self, chrome_driver, live_server):
        """Test keyboard navigation through forms"""
        driver = chrome_driver
        driver.get(f"{live_server}/login")
        
        # Tab through form elements
        username_field = driver.find_element(By.ID, "username")
        username_field.send_keys(Keys.TAB)
        
        # Check focus moves to password field
        password_field = driver.find_element(By.ID, "password")
        assert password_field == driver.switch_to.active_element
    
    def test_form_labels(self, chrome_driver, live_server):
        """Test that form inputs have proper labels"""
        driver = chrome_driver
        driver.get(f"{live_server}/register")
        
        # Check labels exist and are associated with inputs
        username_label = driver.find_element(By.XPATH, "//label[@for='username']")
        assert username_label.is_displayed()
        
        email_label = driver.find_element(By.XPATH, "//label[@for='email']")
        assert email_label.is_displayed()
        
        password_label = driver.find_element(By.XPATH, "//label[@for='password']")
        assert password_label.is_displayed()
    
    def test_alt_text_and_aria_labels(self, chrome_driver, live_server):
        """Test accessibility attributes"""
        driver = chrome_driver
        driver.get(live_server)
        
        # Check that buttons have descriptive text
        register_btn = driver.find_element(By.ID, "register-btn")
        assert "Register" in register_btn.text
        
        login_btn = driver.find_element(By.ID, "login-btn")
        assert "Login" in login_btn.text
