#!/bin/bash

# Quick setup script for Flask Authentication System Testing Project
# Usage: ./scripts/setup.sh [--docker] [--dev] [--test]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default options
SETUP_DOCKER=false
SETUP_DEV=false
RUN_TESTS=false

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
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --docker       Setup Docker environment"
    echo "  --dev          Setup development environment"
    echo "  --test         Run tests after setup"
    echo "  --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Basic setup"
    echo "  $0 --dev --test       # Development setup with tests"
    echo "  $0 --docker           # Docker setup"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --docker)
            SETUP_DOCKER=true
            shift
            ;;
        --dev)
            SETUP_DEV=true
            shift
            ;;
        --test)
            RUN_TESTS=true
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

print_status "Starting Flask Authentication System setup..."

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check Python
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3 not found. Please install Python 3.11 or higher."
        exit 1
    fi
    
    # Check pip
    if command -v pip3 >/dev/null 2>&1; then
        print_success "pip3 found"
    else
        print_error "pip3 not found. Please install pip."
        exit 1
    fi
    
    # Check Git
    if command -v git >/dev/null 2>&1; then
        print_success "Git found"
    else
        print_warning "Git not found. Version control features may not work."
    fi
    
    # Check Docker (if needed)
    if [[ "$SETUP_DOCKER" == true ]]; then
        if command -v docker >/dev/null 2>&1; then
            print_success "Docker found"
        else
            print_error "Docker not found. Please install Docker."
            exit 1
        fi
        
        if command -v docker-compose >/dev/null 2>&1; then
            print_success "Docker Compose found"
        else
            print_error "Docker Compose not found. Please install Docker Compose."
            exit 1
        fi
    fi
    
    # Check Chrome (for Selenium tests)
    if command -v google-chrome >/dev/null 2>&1 || command -v chromium-browser >/dev/null 2>&1; then
        print_success "Chrome/Chromium found"
    else
        print_warning "Chrome not found. UI tests may fail."
        print_status "Install Chrome from: https://www.google.com/chrome/"
    fi
}

# Function to setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    print_status "Installing dependencies..."
    pip install -r requirements.txt
    
    # Install development dependencies if needed
    if [[ "$SETUP_DEV" == true ]]; then
        print_status "Installing development dependencies..."
        pip install black flake8 pylint pytest-xdist pytest-html pytest-cov
    fi
    
    print_success "Python environment setup complete"
}

# Function to setup application
setup_application() {
    print_status "Setting up application..."
    
    # Initialize database
    print_status "Initializing database..."
    python -c "import app; app.init_db()"
    print_success "Database initialized"
    
    # Create test results directory
    mkdir -p test-results
    print_status "Test results directory created"
    
    # Set up environment variables
    if [[ ! -f ".env" ]]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# Flask Application Settings
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=True

# Database Settings
DATABASE=users.db

# Testing Settings
TEST_DATABASE=test_users.db
PYTEST_ADDOPTS=--tb=short --color=yes

# Selenium Settings
SELENIUM_DRIVER=Chrome
SELENIUM_HEADLESS=True
DISPLAY=:99
EOF
        print_success ".env file created"
    else
        print_status ".env file already exists"
    fi
    
    print_success "Application setup complete"
}

# Function to setup Docker environment
setup_docker_env() {
    print_status "Setting up Docker environment..."
    
    # Build Docker images
    print_status "Building Docker images..."
    docker build -t flask-auth-system --target app .
    docker build -t flask-auth-system-test --target test .
    
    print_success "Docker images built successfully"
    
    # Test Docker setup
    print_status "Testing Docker setup..."
    docker run --rm flask-auth-system-test pytest --version
    
    print_success "Docker environment setup complete"
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    if [[ "$SETUP_DOCKER" == true ]]; then
        print_status "Running tests in Docker..."
        docker-compose --profile test up --build --abort-on-container-exit test
    else
        print_status "Running tests locally..."
        
        # Set up display for headless testing (Linux)
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v Xvfb >/dev/null 2>&1; then
                export DISPLAY=:99
                Xvfb :99 -screen 0 1920x1080x24 &
                XVFB_PID=$!
                sleep 2
            fi
        fi
        
        # Run tests
        pytest tests/ -v --tb=short --html=test-results/setup-test-report.html --self-contained-html
        
        # Clean up Xvfb
        if [[ -n "$XVFB_PID" ]]; then
            kill $XVFB_PID 2>/dev/null || true
        fi
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed. Check test-results/ for details."
    fi
}

# Function to show next steps
show_next_steps() {
    print_success "Setup complete! 🎉"
    echo ""
    echo "Next steps:"
    echo ""
    
    if [[ "$SETUP_DOCKER" == true ]]; then
        echo "🐳 Docker Commands:"
        echo "  docker-compose up app                    # Start application"
        echo "  docker-compose --profile test up test    # Run all tests"
        echo "  docker-compose --profile dev up app-dev  # Development mode"
    else
        echo "🐍 Local Commands:"
        echo "  source venv/bin/activate                 # Activate virtual environment"
        echo "  python app.py                            # Start application"
        echo "  ./scripts/run_tests.sh all               # Run all tests"
    fi
    
    echo ""
    echo "📊 Testing Commands:"
    echo "  ./scripts/run_tests.sh functional         # Run functional tests"
    echo "  ./scripts/run_tests.sh security           # Run security tests"
    echo "  ./scripts/run_tests.sh performance        # Run performance tests"
    echo "  ./scripts/run_tests.sh load               # Run load tests"
    echo ""
    echo "🌐 Application URLs:"
    echo "  http://localhost:5000                     # Main application"
    echo "  http://localhost:5000/api/health          # Health check"
    echo "  http://localhost:8089                     # Locust UI (during load tests)"
    echo ""
    echo "📚 Documentation:"
    echo "  README.md                                 # Project overview"
    echo "  SETUP.md                                  # Detailed setup guide"
    echo "  TESTING_GUIDE.md                         # Testing guide"
    echo ""
    echo "🔧 Useful Files:"
    echo "  test-results/                             # Test reports"
    echo "  .env                                      # Environment variables"
    echo "  pytest.ini                               # Test configuration"
}

# Main execution
main() {
    print_status "Flask Authentication System - Quick Setup"
    echo ""
    
    # Check requirements
    check_requirements
    
    # Setup based on options
    if [[ "$SETUP_DOCKER" == true ]]; then
        setup_docker_env
    else
        setup_python_env
        setup_application
    fi
    
    # Run tests if requested
    if [[ "$RUN_TESTS" == true ]]; then
        run_tests
    fi
    
    # Show next steps
    show_next_steps
}

# Run main function
main

print_success "Setup script completed successfully! 🚀"
