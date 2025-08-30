"""
Load testing using Locust framework
Run with: locust -f tests/non_functional/test_load_locust.py --host=http://localhost:5000
"""

from locust import HttpUser, task, between
import random
import string


class AuthenticationUser(HttpUser):
    """Simulates a user interacting with the authentication system"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        self.username = None
        self.password = "LoadTest123!"
        self.registered = False
    
    def generate_username(self):
        """Generate a unique username for this user"""
        if not self.username:
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            self.username = f"loadtest_{random_suffix}"
        return self.username
    
    @task(1)
    def view_home_page(self):
        """View the home page"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def view_login_page(self):
        """View the login page"""
        with self.client.get("/login", catch_response=True) as response:
            if response.status_code == 200 and b"Sign In" in response.content:
                response.success()
            else:
                response.failure("Login page not loaded correctly")
    
    @task(2)
    def view_register_page(self):
        """View the registration page"""
        with self.client.get("/register", catch_response=True) as response:
            if response.status_code == 200 and b"Create New Account" in response.content:
                response.success()
            else:
                response.failure("Registration page not loaded correctly")
    
    @task(3)
    def check_health(self):
        """Check API health endpoint"""
        with self.client.get("/api/health", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        response.success()
                    else:
                        response.failure("Health check returned unhealthy status")
                except:
                    response.failure("Invalid JSON response from health check")
            else:
                response.failure(f"Health check failed with status {response.status_code}")
    
    @task(2)
    def get_user_count(self):
        """Get user count from API"""
        with self.client.get("/api/users/count", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if 'user_count' in data:
                        response.success()
                    else:
                        response.failure("User count not in response")
                except:
                    response.failure("Invalid JSON response from user count")
            else:
                response.failure(f"User count failed with status {response.status_code}")
    
    @task(1)
    def register_user(self):
        """Register a new user"""
        if self.registered:
            return  # Already registered
        
        username = self.generate_username()
        email = f"{username}@loadtest.com"
        
        with self.client.post("/register", data={
            'username': username,
            'email': email,
            'password': self.password,
            'confirm_password': self.password
        }, catch_response=True) as response:
            if response.status_code == 302 and '/login' in response.headers.get('Location', ''):
                response.success()
                self.registered = True
            elif response.status_code == 200 and b"already exists" in response.content:
                # Username collision, try again with different username
                self.username = None
                response.success()  # This is expected behavior
            else:
                response.failure(f"Registration failed with status {response.status_code}")
    
    @task(2)
    def login_user(self):
        """Login with registered user"""
        if not self.registered:
            return  # Need to register first
        
        with self.client.post("/login", data={
            'username': self.username,
            'password': self.password
        }, catch_response=True) as response:
            if response.status_code == 302 and '/dashboard' in response.headers.get('Location', ''):
                response.success()
            elif response.status_code == 200 and b"Invalid username or password" in response.content:
                response.failure("Login failed - invalid credentials")
            elif response.status_code == 200 and b"Account is temporarily locked" in response.content:
                response.failure("Account is locked")
            else:
                response.failure(f"Login failed with status {response.status_code}")
    
    @task(1)
    def access_dashboard(self):
        """Access dashboard (requires login)"""
        with self.client.get("/dashboard", catch_response=True) as response:
            if response.status_code == 200 and b"Welcome to Your Dashboard" in response.content:
                response.success()
            elif response.status_code == 302 and '/login' in response.headers.get('Location', ''):
                # Not logged in, this is expected
                response.success()
            else:
                response.failure(f"Dashboard access failed with status {response.status_code}")
    
    @task(1)
    def logout_user(self):
        """Logout user"""
        with self.client.get("/logout", catch_response=True) as response:
            if response.status_code == 302:
                response.success()
            else:
                response.failure(f"Logout failed with status {response.status_code}")


class BruteForceAttacker(HttpUser):
    """Simulates brute force attack attempts"""
    
    wait_time = between(0.1, 0.5)  # Aggressive timing
    weight = 1  # Lower weight than normal users
    
    def on_start(self):
        """Called when attacker starts"""
        self.target_username = "admin"  # Common target
        self.passwords = [
            "password", "123456", "admin", "password123",
            "qwerty", "letmein", "welcome", "monkey"
        ]
    
    @task
    def brute_force_login(self):
        """Attempt brute force login"""
        password = random.choice(self.passwords)
        
        with self.client.post("/login", data={
            'username': self.target_username,
            'password': password
        }, catch_response=True) as response:
            if response.status_code == 200:
                if b"Account is temporarily locked" in response.content:
                    response.success()  # Account locking is working
                elif b"Invalid username or password" in response.content:
                    response.success()  # Expected for wrong password
                else:
                    response.failure("Unexpected response to brute force attempt")
            else:
                response.failure(f"Brute force attempt failed with status {response.status_code}")


class APIUser(HttpUser):
    """User focused on API endpoints"""
    
    wait_time = between(0.5, 2)
    weight = 2
    
    @task(5)
    def health_check(self):
        """Frequent health checks"""
        self.client.get("/api/health")
    
    @task(3)
    def user_count(self):
        """Check user count"""
        self.client.get("/api/users/count")
    
    @task(1)
    def login_attempts_check(self):
        """Check login attempts for random user"""
        username = f"user{random.randint(1, 100)}"
        self.client.get(f"/api/login-attempts/{username}")


class MixedWorkloadUser(HttpUser):
    """User with mixed workload patterns"""
    
    wait_time = between(2, 8)  # More realistic user behavior
    
    def on_start(self):
        """Initialize user session"""
        self.logged_in = False
        self.username = None
        self.password = "MixedTest123!"
    
    @task(10)
    def browse_site(self):
        """Browse the site like a normal user"""
        # Visit home page
        self.client.get("/")
        
        # Maybe check login page
        if random.random() < 0.3:
            self.client.get("/login")
        
        # Maybe check registration page
        if random.random() < 0.2:
            self.client.get("/register")
    
    @task(3)
    def register_and_login_flow(self):
        """Complete registration and login flow"""
        if self.logged_in:
            return
        
        # Generate unique username
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.username = f"mixed_{random_suffix}"
        email = f"{self.username}@mixedtest.com"
        
        # Register
        response = self.client.post("/register", data={
            'username': self.username,
            'email': email,
            'password': self.password,
            'confirm_password': self.password
        })
        
        if response.status_code == 302:
            # Login
            response = self.client.post("/login", data={
                'username': self.username,
                'password': self.password
            })
            
            if response.status_code == 302:
                self.logged_in = True
    
    @task(2)
    def use_dashboard(self):
        """Use dashboard if logged in"""
        if self.logged_in:
            self.client.get("/dashboard")
    
    @task(1)
    def logout(self):
        """Logout if logged in"""
        if self.logged_in:
            self.client.get("/logout")
            self.logged_in = False


# Custom load test scenarios
class StressTestUser(HttpUser):
    """User for stress testing with high load"""
    
    wait_time = between(0.1, 0.3)  # Very aggressive
    weight = 1
    
    @task(20)
    def rapid_health_checks(self):
        """Rapid health check requests"""
        self.client.get("/api/health")
    
    @task(10)
    def rapid_page_loads(self):
        """Rapid page loading"""
        pages = ["/", "/login", "/register"]
        page = random.choice(pages)
        self.client.get(page)
    
    @task(5)
    def rapid_api_calls(self):
        """Rapid API calls"""
        self.client.get("/api/users/count")


# Performance monitoring user
class MonitoringUser(HttpUser):
    """User that monitors system performance"""
    
    wait_time = between(5, 10)  # Infrequent checks
    weight = 1
    
    @task
    def system_health_check(self):
        """Comprehensive system health check"""
        # Check all major endpoints
        endpoints = [
            "/",
            "/login", 
            "/register",
            "/api/health",
            "/api/users/count"
        ]
        
        for endpoint in endpoints:
            response = self.client.get(endpoint)
            # Log any failures for monitoring
            if response.status_code >= 400:
                print(f"Monitoring alert: {endpoint} returned {response.status_code}")


# Configuration for different test scenarios
class QuickLoadTest(HttpUser):
    """Quick load test configuration"""
    tasks = [AuthenticationUser]
    wait_time = between(1, 2)


class SustainedLoadTest(HttpUser):
    """Sustained load test configuration"""
    tasks = [AuthenticationUser, APIUser, MixedWorkloadUser]
    wait_time = between(2, 5)


class StressTest(HttpUser):
    """Stress test configuration"""
    tasks = [AuthenticationUser, StressTestUser, BruteForceAttacker]
    wait_time = between(0.1, 1)


# Example usage:
# locust -f test_load_locust.py --host=http://localhost:5000
# locust -f test_load_locust.py --host=http://localhost:5000 -u 10 -r 2 -t 60s
# locust -f test_load_locust.py --host=http://localhost:5000 --headless -u 50 -r 5 -t 300s
