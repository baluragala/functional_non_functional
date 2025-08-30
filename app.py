"""
Flask Web Application for User Registration and Login System
Demonstrates functional and non-functional testing capabilities
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import re
import logging
import time
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE = 'users.db'

def get_db_connection():
    """Get database connection with proper error handling"""
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error: {e}")
        raise

def init_db():
    """Initialize the database with users table"""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

def validate_username(username):
    """Validate username format"""
    if len(username) < 3 or len(username) > 20:
        return False, "Username must be between 3 and 20 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, "Username is valid"

def log_login_attempt(username, ip_address, success):
    """Log login attempts for security monitoring"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                'INSERT INTO login_attempts (username, ip_address, success) VALUES (?, ?, ?)',
                (username, ip_address, success)
            )
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error logging login attempt: {e}")

def is_account_locked(username):
    """Check if account is locked due to failed login attempts"""
    try:
        with get_db_connection() as conn:
            user = conn.execute(
                'SELECT failed_login_attempts, account_locked_until FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            
            if user and user['account_locked_until']:
                lock_time = datetime.fromisoformat(user['account_locked_until'])
                if datetime.now() < lock_time:
                    return True
                else:
                    # Unlock account if lock period has expired
                    conn.execute(
                        'UPDATE users SET account_locked_until = NULL, failed_login_attempts = 0 WHERE username = ?',
                        (username,)
                    )
                    conn.commit()
            return False
    except Exception as e:
        logger.error(f"Error checking account lock status: {e}")
        return False

def increment_failed_login(username):
    """Increment failed login attempts and lock account if necessary"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                'UPDATE users SET failed_login_attempts = failed_login_attempts + 1 WHERE username = ?',
                (username,)
            )
            
            user = conn.execute(
                'SELECT failed_login_attempts FROM users WHERE username = ?',
                (username,)
            ).fetchone()
            
            if user and user['failed_login_attempts'] >= 5:
                # Lock account for 30 minutes
                lock_until = datetime.now() + timedelta(minutes=30)
                conn.execute(
                    'UPDATE users SET account_locked_until = ? WHERE username = ?',
                    (lock_until.isoformat(), username)
                )
            
            conn.commit()
    except Exception as e:
        logger.error(f"Error incrementing failed login attempts: {e}")

def reset_failed_login(username):
    """Reset failed login attempts on successful login"""
    try:
        with get_db_connection() as conn:
            conn.execute(
                'UPDATE users SET failed_login_attempts = 0, account_locked_until = NULL, last_login = CURRENT_TIMESTAMP WHERE username = ?',
                (username,)
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error resetting failed login attempts: {e}")

def require_login(f):
    """Decorator to require login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Input validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('register.html')
        
        # Validate username
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            flash(username_msg, 'error')
            return render_template('register.html')
        
        # Validate email
        if not validate_email(email):
            flash('Invalid email format', 'error')
            return render_template('register.html')
        
        # Validate password
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            flash(password_msg, 'error')
            return render_template('register.html')
        
        # Check password confirmation
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')
        
        # Check if user already exists
        try:
            with get_db_connection() as conn:
                existing_user = conn.execute(
                    'SELECT id FROM users WHERE username = ? OR email = ?',
                    (username, email)
                ).fetchone()
                
                if existing_user:
                    flash('Username or email already exists', 'error')
                    return render_template('register.html')
                
                # Create new user
                password_hash = generate_password_hash(password)
                conn.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, password_hash)
                )
                conn.commit()
                
                flash('Registration successful! Please log in.', 'success')
                logger.info(f"New user registered: {username}")
                return redirect(url_for('login'))
                
        except sqlite3.Error as e:
            logger.error(f"Database error during registration: {e}")
            flash('Registration failed. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip_address = request.remote_addr
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')
        
        # Check if account is locked
        if is_account_locked(username):
            flash('Account is temporarily locked due to multiple failed login attempts. Please try again later.', 'error')
            log_login_attempt(username, ip_address, False)
            return render_template('login.html')
        
        try:
            with get_db_connection() as conn:
                user = conn.execute(
                    'SELECT id, username, password_hash FROM users WHERE username = ?',
                    (username,)
                ).fetchone()
                
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    reset_failed_login(username)
                    log_login_attempt(username, ip_address, True)
                    flash('Login successful!', 'success')
                    logger.info(f"User logged in: {username}")
                    return redirect(url_for('dashboard'))
                else:
                    increment_failed_login(username)
                    log_login_attempt(username, ip_address, False)
                    flash('Invalid username or password', 'error')
                    logger.warning(f"Failed login attempt for: {username}")
                    
        except sqlite3.Error as e:
            logger.error(f"Database error during login: {e}")
            flash('Login failed. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/dashboard')
@require_login
def dashboard():
    """User dashboard (protected route)"""
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/logout')
def logout():
    """User logout"""
    username = session.get('username')
    session.clear()
    flash('You have been logged out successfully', 'info')
    logger.info(f"User logged out: {username}")
    return redirect(url_for('index'))

# API endpoints for testing
@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/users/count')
def user_count():
    """Get total user count (for testing purposes)"""
    try:
        with get_db_connection() as conn:
            count = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()
            return jsonify({'user_count': count['count']})
    except sqlite3.Error as e:
        logger.error(f"Error getting user count: {e}")
        return jsonify({'error': 'Database error'}), 500

@app.route('/api/login-attempts/<username>')
def get_login_attempts(username):
    """Get login attempts for a user (for security monitoring)"""
    try:
        with get_db_connection() as conn:
            attempts = conn.execute(
                'SELECT * FROM login_attempts WHERE username = ? ORDER BY timestamp DESC LIMIT 10',
                (username,)
            ).fetchall()
            return jsonify([dict(attempt) for attempt in attempts])
    except sqlite3.Error as e:
        logger.error(f"Error getting login attempts: {e}")
        return jsonify({'error': 'Database error'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error_code=404, error_message='Page not found'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message='Internal server error'), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
