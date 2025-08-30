# Multi-stage Dockerfile for Flask application and testing

# Stage 1: Base Python image
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Application stage
FROM base as app

# Copy application code
COPY app.py .
COPY templates/ templates/

# Create directory for database
RUN mkdir -p /app/data

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["python", "app.py"]

# Stage 3: Testing stage with Chrome and additional test dependencies
FROM base as test

# Install Chrome and ChromeDriver dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

# Add Google Chrome repository
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list

# Install Google Chrome
RUN apt-get update && apt-get install -y \
    google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Install Firefox for cross-browser testing
RUN apt-get update && apt-get install -y \
    firefox-esr \
    && rm -rf /var/lib/apt/lists/*

# Copy all application and test files
COPY . .

# Install test dependencies (if any additional ones)
RUN pip install --no-cache-dir pytest-xvfb

# Set display for headless testing
ENV DISPLAY=:99

# Create test results directory
RUN mkdir -p /app/test-results

# Default command for testing
CMD ["pytest", "--tb=short", "--html=test-results/report.html", "--self-contained-html"]

# Stage 4: CI/CD stage optimized for Azure Pipelines
FROM test as ci

# Install additional CI tools
RUN pip install --no-cache-dir \
    pytest-azurepipelines \
    pytest-cov \
    pytest-xdist

# Create directories for test outputs
RUN mkdir -p /app/test-results/coverage \
    && mkdir -p /app/test-results/junit

# Set up test configuration for CI
ENV PYTEST_ADDOPTS="--junitxml=test-results/junit/test-results.xml --cov=app --cov-report=html:test-results/coverage --cov-report=xml:test-results/coverage.xml"

# Default CI command
CMD ["pytest", "tests/", "--tb=short"]
