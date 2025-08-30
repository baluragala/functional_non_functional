# Setup Guide - Flask Authentication System Testing

This guide provides step-by-step instructions for setting up the Flask Authentication System testing environment on different platforms.

## 📋 Prerequisites

### System Requirements

- **Operating System**: Windows 10+, macOS 10.14+, or Ubuntu 18.04+
- **Python**: Version 3.11 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for load testing)
- **Storage**: At least 2GB free space
- **Network**: Internet connection for downloading dependencies

### Required Software

- Python 3.11+
- Git
- Chrome browser (for Selenium tests)
- Docker (optional, for containerized testing)

## 🖥️ Platform-Specific Setup

### Windows Setup

#### 1. Install Python

```powershell
# Download Python from python.org or use Microsoft Store
# Verify installation
python --version
pip --version
```

#### 2. Install Git

```powershell
# Download from git-scm.com
# Verify installation
git --version
```

#### 3. Install Chrome

```powershell
# Download from google.com/chrome
# ChromeDriver will be managed automatically by webdriver-manager
```

#### 4. Clone and Setup Project

```powershell
# Clone repository
git clone <repository-url>
cd function-non-functional-testing

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "import app; app.init_db()"

# Run application
python app.py
```

#### 5. Install Docker (Optional)

```powershell
# Download Docker Desktop from docker.com
# Enable WSL 2 if prompted
# Verify installation
docker --version
docker-compose --version
```

### macOS Setup

#### 1. Install Python using Homebrew

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Verify installation
python3 --version
pip3 --version
```

#### 2. Install Git

```bash
# Usually pre-installed, or install via Homebrew
brew install git

# Verify installation
git --version
```

#### 3. Install Chrome

```bash
# Download from google.com/chrome or use Homebrew
brew install --cask google-chrome
```

#### 4. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd function-non-functional-testing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "import app; app.init_db()"

# Run application
python app.py
```

#### 5. Install Docker (Optional)

```bash
# Download Docker Desktop from docker.com or use Homebrew
brew install --cask docker

# Verify installation
docker --version
docker-compose --version
```

### Linux (Ubuntu/Debian) Setup

#### 1. Update System and Install Python

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3.11 python3.11-venv python3-pip

# Verify installation
python3 --version
pip3 --version
```

#### 2. Install Git

```bash
sudo apt install git

# Verify installation
git --version
```

#### 3. Install Chrome and Dependencies

```bash
# Add Google Chrome repository
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Install Chrome
sudo apt update
sudo apt install google-chrome-stable

# Install Xvfb for headless testing
sudo apt install xvfb
```

#### 4. Clone and Setup Project

```bash
# Clone repository
git clone <repository-url>
cd function-non-functional-testing

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "import app; app.init_db()"

# Run application
python app.py
```

#### 5. Install Docker (Optional)

```bash
# Install Docker
sudo apt install docker.io docker-compose

# Add user to docker group
sudo usermod -aG docker $USER

# Restart session or run:
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

## 🔧 Environment Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application settings
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database settings
DATABASE=users.db

# Testing settings
TEST_DATABASE=test_users.db
PYTEST_ADDOPTS=--tb=short --color=yes

# Selenium settings
SELENIUM_DRIVER=Chrome
SELENIUM_HEADLESS=True
DISPLAY=:99
```

### Virtual Environment Setup

#### Creating Virtual Environment

```bash
# Python 3.11+
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
```

#### Installing Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install pytest-xdist pytest-html pytest-cov black flake8
```

## 🧪 Test Environment Setup

### Local Testing Setup

#### 1. Basic Test Run

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run simple test
pytest tests/functional/test_api_endpoints.py -v
```

#### 2. UI Testing Setup

```bash
# For Linux headless testing
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &

# Run UI tests
pytest tests/functional/test_ui_selenium.py -v
```

#### 3. Load Testing Setup

```bash
# Start application
python app.py &

# Run load tests
locust -f tests/non_functional/test_load_locust.py --host=http://localhost:5000
```

### Docker Testing Setup

#### 1. Build Test Images

```bash
# Build application image
docker build -t flask-auth-system --target app .

# Build test image
docker build -t flask-auth-system-test --target test .
```

#### 2. Run Tests in Docker

```bash
# All tests
docker-compose --profile test up --build test

# Specific test types
docker-compose --profile test up --build test-functional
docker-compose --profile test up --build test-security
docker-compose --profile test up --build test-performance
```

## 🚀 Azure Pipeline Setup

### Prerequisites for Azure DevOps

1. **Azure DevOps Account**: Sign up at dev.azure.com
2. **Project Creation**: Create a new project
3. **Repository**: Connect your Git repository

### Pipeline Configuration

#### 1. Create Pipeline

```yaml
# In Azure DevOps:
# 1. Go to Pipelines > Create Pipeline
# 2. Select your repository
# 3. Use existing azure-pipelines.yml
```

#### 2. Configure Service Connections (if needed)

```yaml
# For Docker Hub (optional)
# 1. Go to Project Settings > Service Connections
# 2. Create Docker Registry connection
# 3. Update pipeline variables
```

#### 3. Set Pipeline Variables

```yaml
# In Pipeline > Edit > Variables
FLASK_ENV: testing
SECRET_KEY: azure-pipeline-secret-key
PYTHON_VERSION: 3.11
```

### GitHub Actions Setup

#### 1. Repository Secrets

```yaml
# In GitHub repository settings > Secrets and variables > Actions
FLASK_ENV: testing
SECRET_KEY: github-actions-secret-key
```

#### 2. Enable Actions

```yaml
# Ensure .github/workflows/ci.yml is in your repository
# Actions will run automatically on push/PR
```

## 🔍 Verification Steps

### 1. Application Verification

```bash
# Start application
python app.py

# Test endpoints
curl http://localhost:5000/api/health
curl http://localhost:5000/api/users/count

# Open browser to http://localhost:5000
```

### 2. Test Verification

```bash
# Run test suite
./scripts/run_tests.sh all -v

# Check test results
ls -la test-results/
```

### 3. Docker Verification

```bash
# Test Docker setup
docker-compose --profile test up --build test

# Check containers
docker ps -a
```

## 🛠️ Troubleshooting

### Common Issues and Solutions

#### Python/Pip Issues

```bash
# Python not found
which python3
python3 --version

# Pip not working
python -m pip --version
python -m pip install --upgrade pip
```

#### Virtual Environment Issues

```bash
# Can't activate venv
ls -la venv/
rm -rf venv/
python -m venv venv

# Wrong Python version in venv
python -m venv --clear venv
```

#### Chrome/Selenium Issues

```bash
# Chrome not found (Linux)
google-chrome --version
sudo apt install google-chrome-stable

# ChromeDriver issues
pip install --upgrade webdriver-manager

# Headless display issues (Linux)
export DISPLAY=:99
Xvfb :99 -screen 0 1920x1080x24 &
```

#### Docker Issues

```bash
# Docker not running
sudo systemctl start docker  # Linux
# Start Docker Desktop        # Windows/macOS

# Permission denied
sudo usermod -aG docker $USER
newgrp docker

# Build failures
docker system prune -f
docker-compose down --volumes
```

#### Database Issues

```bash
# Database locked
rm -f *.db
python -c "import app; app.init_db()"

# Permission issues
chmod 664 *.db
```

### Performance Issues

#### Slow Tests

```bash
# Run tests in parallel
pytest tests/ -n auto

# Skip slow tests
pytest tests/ -m "not slow"

# Reduce test scope
pytest tests/functional/ -k "not ui"
```

#### Memory Issues

```bash
# Monitor memory usage
htop  # Linux/macOS
# Task Manager  # Windows

# Reduce parallel workers
pytest tests/ -n 2

# Use Docker with memory limits
docker run --memory=2g flask-auth-system-test
```

## 📞 Getting Help

### Debug Information Collection

```bash
# System information
python --version
pip --version
docker --version

# Environment information
pip list
env | grep FLASK
env | grep PYTEST

# Test logs
pytest tests/ -v -s --tb=long
```

### Log Locations

- **Application logs**: Console output
- **Test results**: `test-results/` directory
- **Docker logs**: `docker-compose logs`
- **CI/CD logs**: Azure DevOps / GitHub Actions interface

### Support Resources

1. **Project Documentation**: README.md
2. **Test Configuration**: pytest.ini
3. **Docker Configuration**: docker-compose.yml
4. **CI/CD Configuration**: azure-pipelines.yml

---

**Setup Complete! 🎉**

You should now have a fully functional testing environment. Run `./scripts/run_tests.sh all -v` to verify everything is working correctly.
