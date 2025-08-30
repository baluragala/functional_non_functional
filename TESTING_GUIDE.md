# Testing Guide - Functional & Non-Functional Testing

This comprehensive guide explains the testing strategies, methodologies, and best practices implemented in this Flask Authentication System project.

## 📚 Table of Contents

1. [Testing Overview](#testing-overview)
2. [Functional Testing](#functional-testing)
3. [Non-Functional Testing](#non-functional-testing)
4. [Test Execution Strategies](#test-execution-strategies)
5. [CI/CD Integration](#cicd-integration)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)

## 🎯 Testing Overview

### Testing Pyramid

This project implements a comprehensive testing pyramid:

```
    /\
   /  \     E2E Tests (UI + Integration)
  /____\
 /      \   Integration Tests (API + Database)
/________\  Unit Tests (Functions + Classes)
```

### Test Categories

| Category        | Purpose                          | Tools                | Coverage                         |
| --------------- | -------------------------------- | -------------------- | -------------------------------- |
| **Functional**  | Verify features work as expected | Pytest, Selenium     | User workflows, API endpoints    |
| **Security**    | Identify vulnerabilities         | Custom tests, Bandit | Input validation, authentication |
| **Performance** | Measure system performance       | Pytest, Locust       | Response times, throughput       |
| **Load**        | Test under high load             | Locust               | Concurrent users, stress testing |
| **Integration** | Test component interactions      | Pytest               | Database, external services      |

## 🔧 Functional Testing

### API Testing (`test_api_endpoints.py`)

#### Test Structure

```python
@pytest.mark.functional
@pytest.mark.api
class TestAPIEndpoints:
    """Test API endpoints functionality"""
```

#### Key Test Areas

**1. Health Check Endpoint**

```python
def test_health_check_endpoint(self, test_client):
    """Test the health check API endpoint"""
    response = test_client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
```

**2. User Registration**

```python
def test_successful_registration(self, test_client, test_user_data):
    """Test successful user registration"""
    response = test_client.post('/register', data={
        'username': test_user_data['username'],
        'email': test_user_data['email'],
        'password': test_user_data['password'],
        'confirm_password': test_user_data['password']
    })
    assert response.status_code == 302  # Redirect to login
```

**3. Input Validation**

```python
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
```

#### API Testing Best Practices

1. **Test All HTTP Methods**: GET, POST, PUT, DELETE
2. **Validate Response Codes**: 200, 302, 400, 401, 404, 500
3. **Check Response Content**: JSON structure, error messages
4. **Test Edge Cases**: Empty inputs, large payloads, special characters
5. **Verify State Changes**: Database updates, session management

### UI Testing (`test_ui_selenium.py`)

#### Test Structure

```python
@pytest.mark.functional
@pytest.mark.ui
class TestUserInterface:
    """Test the web user interface functionality"""
```

#### Key Test Areas

**1. Page Navigation**

```python
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
```

**2. Form Interactions**

```python
def test_password_strength_indicator(self, chrome_driver, live_server):
    """Test real-time password strength validation"""
    driver = chrome_driver
    driver.get(f"{live_server}/register")

    password_field = driver.find_element(By.ID, "password")
    password_field.send_keys("StrongPass123!")
    time.sleep(0.5)

    # Check validation indicators
    length_check = driver.find_element(By.ID, "length-check")
    assert "green" in length_check.get_attribute("style")
```

**3. Cross-Browser Testing**

```python
def test_basic_functionality_firefox(self, firefox_driver, live_server):
    """Test basic functionality in Firefox"""
    driver = firefox_driver
    driver.get(live_server)
    assert "User Authentication System" in driver.title
```

#### UI Testing Best Practices

1. **Use Page Object Model**: Separate page logic from tests
2. **Explicit Waits**: Use WebDriverWait instead of sleep()
3. **Stable Locators**: Prefer ID and data attributes over XPath
4. **Cross-Browser Testing**: Test on Chrome, Firefox, Safari
5. **Responsive Testing**: Test different screen sizes
6. **Accessibility Testing**: Check ARIA labels, keyboard navigation

### Integration Testing

#### Database Integration

```python
def test_user_data_persistence(self, test_client, test_user_data):
    """Test that user data persists across requests"""
    # Register user
    test_client.post('/register', data=test_user_data)

    # Verify user count increased
    response = test_client.get('/api/users/count')
    data = json.loads(response.data)
    assert data['user_count'] == 1
```

#### Session Management

```python
def test_session_security(self, test_client, registered_user):
    """Test session security mechanisms"""
    # Login
    response = test_client.post('/login', data=registered_user)
    assert 'Set-Cookie' in response.headers

    # Verify session works
    dashboard_response = test_client.get('/dashboard')
    assert dashboard_response.status_code == 200
```

## 🛡️ Non-Functional Testing

### Security Testing (`test_security.py`)

#### Input Validation Testing

**1. XSS Prevention**

```python
def test_xss_prevention_in_forms(self, test_client):
    """Test XSS prevention in form inputs"""
    xss_payloads = [
        '<script>alert("XSS")</script>',
        '"><script>alert("XSS")</script>',
        "javascript:alert('XSS')",
        '<img src=x onerror=alert("XSS")>'
    ]

    for payload in xss_payloads:
        response = test_client.post('/register', data={
            'username': payload,
            'email': 'test@example.com',
            'password': 'ValidPass123!',
            'confirm_password': 'ValidPass123!'
        })

        assert b'<script>' not in response.data
        assert b'javascript:' not in response.data
```

**2. SQL Injection Prevention**

```python
def test_sql_injection_prevention(self, test_client):
    """Test SQL injection prevention"""
    sql_payloads = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "' UNION SELECT * FROM users --"
    ]

    for payload in sql_payloads:
        response = test_client.post('/login', data={
            'username': payload,
            'password': 'anypassword'
        })

        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
```

#### Authentication Security Testing

**1. Brute Force Protection**

```python
def test_brute_force_protection(self, test_client, registered_user):
    """Test brute force attack protection"""
    # Make multiple failed login attempts
    for i in range(6):
        response = test_client.post('/login', data={
            'username': registered_user['username'],
            'password': 'wrongpassword'
        })

        if i >= 5:
            assert b'Account is temporarily locked' in response.data
```

**2. Session Security**

```python
def test_session_hijacking_prevention(self, test_client, registered_user):
    """Test session hijacking prevention measures"""
    login_response = test_client.post('/login', data=registered_user)

    # Extract and verify session cookie
    cookies = login_response.headers.getlist('Set-Cookie')
    session_cookie = None
    for cookie in cookies:
        if 'session=' in cookie:
            session_cookie = cookie.split(';')[0]
            break

    assert session_cookie is not None
```

#### Security Testing Best Practices

1. **OWASP Top 10 Coverage**: Test for common vulnerabilities
2. **Input Fuzzing**: Test with malformed, oversized, and malicious inputs
3. **Authentication Testing**: Verify all authentication mechanisms
4. **Authorization Testing**: Test access controls and permissions
5. **Data Protection**: Ensure sensitive data is properly protected
6. **Security Headers**: Verify security headers are present

### Performance Testing (`test_performance.py`)

#### Response Time Testing

**1. API Performance**

```python
def test_api_health_response_time(self, test_client):
    """Test API health endpoint response time"""
    times = []

    for _ in range(10):
        start_time = time.time()
        response = test_client.get('/api/health')
        end_time = time.time()

        assert response.status_code == 200
        times.append(end_time - start_time)

    avg_time = statistics.mean(times)
    assert avg_time < 0.1  # Average under 100ms
```

**2. Database Performance**

```python
def test_database_query_efficiency(self, test_client, registered_user):
    """Test database query efficiency"""
    start_time = time.time()

    response = test_client.post('/login', data=registered_user)

    end_time = time.time()
    assert response.status_code == 302
    assert end_time - start_time < 1.0  # Complete within 1 second
```

#### Throughput Testing

**1. Concurrent Requests**

```python
def test_concurrent_health_checks(self, live_server):
    """Test concurrent health check requests"""
    def make_request():
        response = requests.get(f'{live_server}/api/health', timeout=5)
        return response.status_code == 200

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [future.result() for future in as_completed(futures)]

    success_rate = sum(results) / len(results)
    assert success_rate >= 0.9  # 90% success rate
```

#### Resource Usage Testing

**1. Memory Usage**

```python
def test_memory_usage_under_load(self, live_server):
    """Test memory usage doesn't grow excessively under load"""
    import psutil

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Generate load
    for _ in range(100):
        requests.get(f'{live_server}/api/health', timeout=2)

    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory

    assert memory_increase < 50 * 1024 * 1024  # Less than 50MB
```

#### Performance Testing Best Practices

1. **Baseline Measurements**: Establish performance baselines
2. **Load Patterns**: Test with realistic load patterns
3. **Resource Monitoring**: Monitor CPU, memory, disk, network
4. **Scalability Testing**: Test performance under increasing load
5. **Bottleneck Identification**: Identify and document bottlenecks

### Load Testing (`test_load_locust.py`)

#### User Simulation

**1. Authentication User**

```python
class AuthenticationUser(HttpUser):
    """Simulates a user interacting with the authentication system"""

    wait_time = between(1, 3)

    @task(3)
    def check_health(self):
        """Check API health endpoint"""
        self.client.get("/api/health")

    @task(1)
    def register_user(self):
        """Register a new user"""
        username = self.generate_username()
        self.client.post("/register", data={
            'username': username,
            'email': f"{username}@loadtest.com",
            'password': self.password,
            'confirm_password': self.password
        })
```

**2. Brute Force Attacker**

```python
class BruteForceAttacker(HttpUser):
    """Simulates brute force attack attempts"""

    wait_time = between(0.1, 0.5)
    weight = 1  # Lower weight than normal users

    @task
    def brute_force_login(self):
        """Attempt brute force login"""
        password = random.choice(self.passwords)
        self.client.post("/login", data={
            'username': self.target_username,
            'password': password
        })
```

#### Load Testing Scenarios

1. **Normal Load**: Typical user behavior
2. **Peak Load**: High traffic periods
3. **Stress Testing**: Beyond normal capacity
4. **Spike Testing**: Sudden load increases
5. **Endurance Testing**: Sustained load over time
6. **Security Load Testing**: Attack simulation

#### Load Testing Best Practices

1. **Realistic Scenarios**: Model actual user behavior
2. **Gradual Ramp-up**: Increase load gradually
3. **Monitor System Resources**: Track server performance
4. **Test Different Patterns**: Various load distributions
5. **Failure Analysis**: Understand failure modes

## 🚀 Test Execution Strategies

### Local Testing

#### Quick Test Run

```bash
# Run all tests
pytest tests/ -v

# Run specific categories
pytest tests/functional/ -v
pytest tests/non_functional/test_security.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

#### Parallel Execution

```bash
# Run tests in parallel
pytest tests/ -n auto

# Limit parallel workers
pytest tests/ -n 4
```

#### Test Selection

```bash
# Run by markers
pytest -m "functional and not slow"
pytest -m "security"
pytest -m "performance"

# Run by keywords
pytest -k "test_login"
pytest -k "security and not ui"
```

### Docker Testing

#### Containerized Test Execution

```bash
# All tests in Docker
docker-compose --profile test up --build test

# Specific test categories
docker-compose --profile test up --build test-security
docker-compose --profile test up --build test-performance
```

#### Benefits of Docker Testing

1. **Consistent Environment**: Same environment across machines
2. **Isolation**: Tests don't affect host system
3. **Scalability**: Easy to scale test execution
4. **CI/CD Ready**: Same containers in development and CI

### CI/CD Testing

#### Azure Pipelines Strategy

```yaml
stages:
  - stage: Build
    jobs:
      - job: UnitTests
      - job: Linting

  - stage: FunctionalTests
    jobs:
      - job: APITests
      - job: UITests

  - stage: NonFunctionalTests
    jobs:
      - job: SecurityTests
      - job: PerformanceTests
      - job: LoadTests
```

#### GitHub Actions Strategy

```yaml
jobs:
  unit-tests:
    runs-on: ubuntu-latest

  api-tests:
    needs: unit-tests
    runs-on: ubuntu-latest

  security-tests:
    needs: unit-tests
    runs-on: ubuntu-latest
```

## 📊 Test Reporting

### HTML Reports

```bash
# Generate HTML report
pytest tests/ --html=test-results/report.html --self-contained-html
```

### Coverage Reports

```bash
# Generate coverage report
pytest tests/ --cov=app --cov-report=html:htmlcov --cov-report=xml:coverage.xml
```

### JUnit XML Reports

```bash
# Generate JUnit XML for CI/CD
pytest tests/ --junitxml=test-results/junit.xml
```

### Load Test Reports

```bash
# Locust HTML report
locust -f test_load_locust.py --host=http://localhost:5000 --headless -u 10 -r 2 -t 60s --html load-report.html
```

## 🎯 Best Practices

### Test Design Principles

1. **FIRST Principles**

   - **Fast**: Tests should run quickly
   - **Independent**: Tests should not depend on each other
   - **Repeatable**: Tests should produce consistent results
   - **Self-Validating**: Tests should have clear pass/fail criteria
   - **Timely**: Tests should be written at the right time

2. **Test Pyramid**

   - **Many Unit Tests**: Fast, isolated, focused
   - **Some Integration Tests**: Test component interactions
   - **Few E2E Tests**: Test complete user workflows

3. **AAA Pattern**
   - **Arrange**: Set up test data and conditions
   - **Act**: Execute the code being tested
   - **Assert**: Verify the expected outcome

### Code Quality

1. **Test Naming**: Use descriptive test names
2. **Test Documentation**: Document complex test scenarios
3. **Test Data Management**: Use fixtures and factories
4. **Test Organization**: Group related tests in classes
5. **Test Maintenance**: Keep tests up-to-date with code changes

### Security Testing

1. **OWASP Coverage**: Test for OWASP Top 10 vulnerabilities
2. **Input Validation**: Test all input vectors
3. **Authentication Testing**: Verify all auth mechanisms
4. **Authorization Testing**: Test access controls
5. **Data Protection**: Ensure sensitive data security

### Performance Testing

1. **Baseline Establishment**: Set performance baselines
2. **Realistic Load**: Use realistic user patterns
3. **Resource Monitoring**: Monitor system resources
4. **Bottleneck Identification**: Find performance bottlenecks
5. **Scalability Testing**: Test under increasing load

## 🔍 Troubleshooting

### Common Issues

#### Test Failures

```bash
# Run with verbose output
pytest tests/ -v -s

# Run specific failing test
pytest tests/functional/test_ui_selenium.py::TestUserInterface::test_login -v -s

# Debug with pdb
pytest tests/ --pdb
```

#### Selenium Issues

```bash
# Check Chrome version
google-chrome --version

# Update ChromeDriver
pip install --upgrade webdriver-manager

# Run in headless mode
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
```

#### Performance Issues

```bash
# Run tests in parallel
pytest tests/ -n auto

# Skip slow tests
pytest tests/ -m "not slow"

# Profile test execution
pytest tests/ --durations=10
```

### Debugging Strategies

1. **Logging**: Add logging to understand test flow
2. **Screenshots**: Capture screenshots for UI test failures
3. **Test Data**: Verify test data setup and cleanup
4. **Environment**: Check environment variables and configuration
5. **Dependencies**: Verify all dependencies are installed

---

**Happy Testing! 🧪**

This guide provides comprehensive coverage of testing strategies implemented in this project. Use it as a reference for implementing robust testing practices in your own applications.
