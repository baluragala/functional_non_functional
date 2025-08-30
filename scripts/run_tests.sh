#!/bin/bash

# Test runner script for local development and CI/CD
# Usage: ./scripts/run_tests.sh [test-type] [options]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
VERBOSE=false
COVERAGE=false
HTML_REPORT=false
PARALLEL=false
DOCKER=false

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [test-type] [options]"
    echo ""
    echo "Test types:"
    echo "  all                 Run all tests (default)"
    echo "  unit               Run unit tests only"
    echo "  functional         Run functional tests only"
    echo "  api                Run API tests only"
    echo "  ui                 Run UI tests only"
    echo "  security           Run security tests only"
    echo "  performance        Run performance tests only"
    echo "  load               Run load tests only"
    echo ""
    echo "Options:"
    echo "  -v, --verbose      Verbose output"
    echo "  -c, --coverage     Generate coverage report"
    echo "  -h, --html         Generate HTML report"
    echo "  -p, --parallel     Run tests in parallel"
    echo "  -d, --docker       Run tests in Docker"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 functional -v -h"
    echo "  $0 security --coverage"
    echo "  $0 all --docker --parallel"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        all|unit|functional|api|ui|security|performance|load)
            TEST_TYPE="$1"
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -h|--html)
            HTML_REPORT=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -d|--docker)
            DOCKER=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if we're in the project root
if [[ ! -f "app.py" ]]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Create test results directory
mkdir -p test-results

# Set up environment variables
export FLASK_ENV=testing
export SECRET_KEY=test-secret-key

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [[ "$VERBOSE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Add coverage
if [[ "$COVERAGE" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --cov=app --cov-report=term-missing --cov-report=xml:test-results/coverage.xml"
fi

# Add HTML report
if [[ "$HTML_REPORT" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD --html=test-results/report.html --self-contained-html"
fi

# Add parallel execution
if [[ "$PARALLEL" == true ]]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# Add JUnit XML output
PYTEST_CMD="$PYTEST_CMD --junitxml=test-results/junit.xml"

# Function to run tests in Docker
run_docker_tests() {
    print_status "Running tests in Docker..."
    
    case $TEST_TYPE in
        all)
            docker-compose --profile test up --build --abort-on-container-exit test
            ;;
        functional)
            docker-compose --profile test up --build --abort-on-container-exit test-functional
            ;;
        security)
            docker-compose --profile test up --build --abort-on-container-exit test-security
            ;;
        performance)
            docker-compose --profile test up --build --abort-on-container-exit test-performance
            ;;
        load)
            docker-compose --profile load-test up --build --abort-on-container-exit load-test-headless
            ;;
        *)
            print_error "Docker test type '$TEST_TYPE' not supported"
            exit 1
            ;;
    esac
}

# Function to run local tests
run_local_tests() {
    print_status "Setting up test environment..."
    
    # Check if virtual environment exists
    if [[ ! -d "venv" ]]; then
        print_warning "Virtual environment not found. Creating one..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    # Initialize database
    print_status "Initializing test database..."
    python -c "import app; app.init_db()"
    
    # Set up display for UI tests
    if [[ "$TEST_TYPE" == "ui" || "$TEST_TYPE" == "all" || "$TEST_TYPE" == "functional" ]]; then
        if command -v Xvfb >/dev/null 2>&1; then
            print_status "Starting Xvfb for headless browser testing..."
            export DISPLAY=:99
            Xvfb :99 -screen 0 1920x1080x24 &
            XVFB_PID=$!
            sleep 2
        else
            print_warning "Xvfb not found. UI tests may fail in headless environment."
        fi
    fi
    
    # Run tests based on type
    case $TEST_TYPE in
        all)
            print_status "Running all tests..."
            $PYTEST_CMD tests/
            ;;
        unit)
            print_status "Running unit tests..."
            $PYTEST_CMD tests/unit/
            ;;
        functional)
            print_status "Running functional tests..."
            $PYTEST_CMD tests/functional/
            ;;
        api)
            print_status "Running API tests..."
            $PYTEST_CMD tests/functional/test_api_endpoints.py
            ;;
        ui)
            print_status "Running UI tests..."
            $PYTEST_CMD tests/functional/test_ui_selenium.py
            ;;
        security)
            print_status "Running security tests..."
            $PYTEST_CMD tests/non_functional/test_security.py
            ;;
        performance)
            print_status "Running performance tests..."
            $PYTEST_CMD tests/non_functional/test_performance.py
            ;;
        load)
            print_status "Running load tests..."
            print_status "Starting application..."
            python app.py &
            APP_PID=$!
            sleep 10
            
            print_status "Running Locust load tests..."
            locust -f tests/non_functional/test_load_locust.py --host=http://localhost:5000 --headless -u 10 -r 2 -t 60s --html test-results/load-test-report.html
            
            print_status "Stopping application..."
            kill $APP_PID
            ;;
        *)
            print_error "Unknown test type: $TEST_TYPE"
            exit 1
            ;;
    esac
    
    # Clean up Xvfb if it was started
    if [[ -n "$XVFB_PID" ]]; then
        kill $XVFB_PID 2>/dev/null || true
    fi
}

# Main execution
print_status "Starting test execution..."
print_status "Test type: $TEST_TYPE"
print_status "Docker mode: $DOCKER"

if [[ "$DOCKER" == true ]]; then
    run_docker_tests
else
    run_local_tests
fi

# Check if tests passed
if [[ $? -eq 0 ]]; then
    print_success "All tests passed!"
    
    # Show test results location
    if [[ -d "test-results" ]]; then
        print_status "Test results available in:"
        ls -la test-results/
    fi
    
    exit 0
else
    print_error "Tests failed!"
    exit 1
fi
