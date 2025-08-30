# Flask Authentication System - Functional & Non-Functional Testing Demo

A comprehensive demonstration of functional and non-functional testing in Python using a Flask web application with user registration and login functionality. This project showcases testing best practices, security testing, performance testing, and CI/CD integration with both local and Azure Pipeline support.

## 🎯 Project Overview

This project demonstrates:

- **Functional Testing**: API endpoints, UI interactions, user workflows
- **Non-Functional Testing**: Security, performance, load testing, input validation
- **CI/CD Integration**: Azure Pipelines and GitHub Actions
- **Containerized Testing**: Docker-based test execution
- **Cross-browser Testing**: Chrome and Firefox support
- **Security Testing**: XSS, SQL injection, brute force protection
- **Performance Testing**: Response times, load testing with Locust

## 🏗️ Architecture

```
├── app.py                          # Main Flask application
├── templates/                      # HTML templates
│   ├── base.html                  # Base template
│   ├── index.html                 # Home page
│   ├── login.html                 # Login page
│   ├── register.html              # Registration page
│   ├── dashboard.html             # User dashboard
│   └── error.html                 # Error pages
├── tests/                         # Test suite
│   ├── conftest.py               # Pytest configuration and fixtures
│   ├── functional/               # Functional tests
│   │   ├── test_api_endpoints.py # API testing
│   │   └── test_ui_selenium.py   # UI testing with Selenium
│   └── non_functional/           # Non-functional tests
│       ├── test_security.py      # Security testing
│       ├── test_performance.py   # Performance testing
│       └── test_load_locust.py    # Load testing with Locust
├── scripts/                      # Utility scripts
│   └── run_tests.sh             # Test runner script
├── Dockerfile                    # Multi-stage Docker configuration
├── docker-compose.yml           # Docker Compose for different test scenarios
├── azure-pipelines.yml          # Azure DevOps pipeline
├── .github/workflows/ci.yml      # GitHub Actions workflow
└── requirements.txt              # Python dependencies
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized testing)
- Chrome browser (for Selenium tests)

### Local Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd function-non-functional-testing
   ```

2. **Create virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

### Running Tests

#### Using the Test Runner Script (Recommended)

```bash
# Run all tests
./scripts/run_tests.sh all

# Run specific test types
./scripts/run_tests.sh functional -v -h
./scripts/run_tests.sh security --coverage
./scripts/run_tests.sh performance
./scripts/run_tests.sh load

# Run tests in Docker
./scripts/run_tests.sh all --docker
```

#### Manual Test Execution

```bash
# All tests
pytest tests/ -v

# Functional tests only
pytest tests/functional/ -v

# Security tests only
pytest tests/non_functional/test_security.py -v

# Performance tests only
pytest tests/non_functional/test_performance.py -v

# With coverage report
pytest tests/ --cov=app --cov-report=html

# Parallel execution
pytest tests/ -n auto
```

#### Load Testing with Locust

```bash
# Interactive load testing
locust -f tests/non_functional/test_load_locust.py --host=http://localhost:5000

# Headless load testing
locust -f tests/non_functional/test_load_locust.py --host=http://localhost:5000 --headless -u 10 -r 2 -t 60s
```

## 🐳 Docker Usage

### Build and Run Application

```bash
# Build application image
docker build -t flask-auth-system --target app .

# Run application
docker run -p 5000:5000 flask-auth-system
```

### Run Tests in Docker

```bash
# All tests
docker-compose --profile test up --build test

# Functional tests only
docker-compose --profile test up --build test-functional

# Security tests only
docker-compose --profile test up --build test-security

# Performance tests only
docker-compose --profile test up --build test-performance

# Load testing
docker-compose --profile load-test up --build load-test-headless
```

### Development Mode

```bash
# Run in development mode with hot reload
docker-compose --profile dev up --build app-dev
```

## 🧪 Test Categories

### Functional Tests

#### API Tests (`tests/functional/test_api_endpoints.py`)

- User registration and validation
- Login authentication
- Session management
- API endpoint functionality
- Error handling
- Data persistence

#### UI Tests (`tests/functional/test_ui_selenium.py`)

- User interface interactions
- Form validation
- Navigation testing
- Cross-browser compatibility
- Responsive design
- Accessibility features

### Non-Functional Tests

#### Security Tests (`tests/non_functional/test_security.py`)

- **Input Validation**: XSS, SQL injection, command injection prevention
- **Authentication Security**: Password hashing, session security, brute force protection
- **Authorization**: Access control, privilege escalation prevention
- **Data Protection**: Sensitive data exposure, information disclosure
- **Security Headers**: CSRF protection, clickjacking prevention

#### Performance Tests (`tests/non_functional/test_performance.py`)

- **Response Times**: Page load times, API response times
- **Throughput**: Concurrent request handling
- **Resource Usage**: Memory and CPU usage monitoring
- **Scalability**: Performance under increasing load
- **Database Performance**: Query efficiency testing

#### Load Tests (`tests/non_functional/test_load_locust.py`)

- **User Simulation**: Multiple user behavior patterns
- **Stress Testing**: High-load scenarios
- **Endurance Testing**: Sustained load over time
- **Spike Testing**: Sudden load increases
- **Security Load Testing**: Brute force attack simulation

## 🔧 Configuration

### Environment Variables

```bash
FLASK_ENV=production|development|testing
SECRET_KEY=your-secret-key
DATABASE=path-to-database-file
```

### Test Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
markers =
    functional: functional tests
    security: security tests
    performance: performance tests
    ui: UI tests with Selenium
    api: API tests
    slow: slow running tests
```

### Docker Configuration

The project uses multi-stage Dockerfile:

- **base**: Python environment with dependencies
- **app**: Production application
- **test**: Testing environment with Chrome/Firefox
- **ci**: CI/CD optimized with additional tools

## 🔄 CI/CD Integration

### Azure Pipelines

The `azure-pipelines.yml` provides:

- Multi-stage pipeline with parallel execution
- Separate jobs for different test types
- Docker-based testing
- Test result publishing
- Code coverage reporting
- Security scanning with Bandit
- Load testing integration

**Pipeline Stages:**

1. **Build**: Linting, unit tests, artifact creation
2. **Functional Tests**: API and UI testing
3. **Security Tests**: Security scanning and testing
4. **Performance Tests**: Performance and load testing
5. **Docker Tests**: Containerized testing
6. **Integration**: End-to-end integration testing

### GitHub Actions

The `.github/workflows/ci.yml` provides similar functionality for GitHub-hosted projects with:

- Parallel job execution
- Cross-platform testing
- Artifact management
- Test reporting
- Coverage integration with Codecov

## 📊 Test Reports

### HTML Reports

```bash
pytest tests/ --html=test-results/report.html --self-contained-html
```

### Coverage Reports

```bash
pytest tests/ --cov=app --cov-report=html:htmlcov
```

### JUnit XML (for CI/CD)

```bash
pytest tests/ --junitxml=test-results/junit.xml
```

### Load Test Reports

Locust generates HTML reports with:

- Request statistics
- Response time distributions
- Failure analysis
- Real-time monitoring

## 🛡️ Security Features

### Application Security

- **Password Policy**: Strong password requirements
- **Account Locking**: Brute force protection
- **Session Management**: Secure session handling
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Parameterized queries
- **XSS Prevention**: Output encoding and validation

### Security Testing

- **Automated Security Scanning**: Bandit integration
- **Penetration Testing**: Automated security test suite
- **Vulnerability Assessment**: Input validation testing
- **Authentication Testing**: Session and access control testing

## 📈 Performance Monitoring

### Metrics Tracked

- Response times (p50, p95, p99)
- Throughput (requests per second)
- Error rates
- Resource utilization
- Database query performance

### Performance Thresholds

- API responses: < 100ms average
- Page loads: < 1 second
- Login process: < 2 seconds
- Registration: < 3 seconds

## 🔍 Troubleshooting

### Common Issues

#### Selenium Tests Failing

```bash
# Install Chrome and ChromeDriver
# For Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# For headless testing:
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
```

#### Database Issues

```bash
# Reset test database
rm -f test_users.db users.db
python -c "import app; app.init_db()"
```

#### Docker Issues

```bash
# Clean up Docker resources
docker system prune -f
docker-compose down --volumes
```

### Debug Mode

Enable debug logging:

```bash
export FLASK_DEBUG=1
export PYTEST_ADDOPTS="-v -s --log-cli-level=DEBUG"
```

## 📚 Learning Resources

### Testing Concepts Demonstrated

1. **Test Pyramid**: Unit → Integration → E2E
2. **Test Types**: Functional vs Non-functional
3. **Security Testing**: OWASP Top 10 coverage
4. **Performance Testing**: Load, stress, volume testing
5. **CI/CD Integration**: Automated testing pipelines
6. **Containerized Testing**: Docker-based test execution

### Best Practices Implemented

- **Test Isolation**: Independent test execution
- **Test Data Management**: Fixtures and factories
- **Page Object Model**: Selenium test organization
- **Parallel Execution**: Faster test runs
- **Comprehensive Reporting**: Multiple report formats
- **Security-First**: Security testing integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Development Workflow

```bash
# Setup development environment
./scripts/run_tests.sh all -v -c

# Run specific test categories
./scripts/run_tests.sh security --coverage
./scripts/run_tests.sh performance --html

# Docker development
docker-compose --profile dev up --build app-dev
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋‍♂️ Support

For questions or issues:

1. Check the troubleshooting section
2. Review test logs in `test-results/`
3. Run tests with verbose output: `-v` flag
4. Check Docker logs: `docker-compose logs`

---

**Happy Testing! 🎉**

This project demonstrates comprehensive testing strategies that can be applied to any Python web application. Use it as a reference for implementing robust testing practices in your own projects.
