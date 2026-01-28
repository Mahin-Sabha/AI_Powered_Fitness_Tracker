from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import os
import sqlite3
import subprocess
import signal
import socket
import time

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# SQLite database setup
DATABASE = 'users.db'

def get_db():
    """Get database connection"""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    """Initialize database with users table"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            height REAL,
            weight REAL,
            fitness_level TEXT,
            fitness_goal TEXT,
            profile_completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Per-exercise workout logs for persistence
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            exercise TEXT NOT NULL,
            reps INTEGER DEFAULT 0,
            duration_seconds INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # End-of-workout session summaries
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workout_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            total_reps INTEGER DEFAULT 0,
            total_duration_seconds INTEGER DEFAULT 0,
            exercise_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    db.close()

# Initialize database on startup
init_db()

def user_exists(username):
    """Check if username exists"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    db.close()
    return result is not None

def email_exists(email):
    """Check if email exists"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    result = cursor.fetchone()
    db.close()
    return result is not None

def create_user(username, email, password):
    """Create a new user"""
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(
            'INSERT INTO users (username, email, password) VALUES (?, ?, ?)',
            (username, email, generate_password_hash(password))
        )
        db.commit()
        db.close()
        return True
    except sqlite3.IntegrityError:
        db.close()
        return False

def get_user(username):
    """Get user by username"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT username, email, password, profile_completed FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    db.close()
    return dict(user) if user else None


def get_user_by_email(email):
    """Get user by email"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT username, email, password, profile_completed FROM users WHERE email = ?', (email,))
    user = cursor.fetchone()
    db.close()
    return dict(user) if user else None

# Store Streamlit process globally
streamlit_process = None

@app.route('/')
def landing():
    """Landing page"""
    return render_template('landing.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if request.method == 'GET':
        # Clear any old flash messages and session data
        session.pop('_flashes', None)
        if 'username' in session:
            session.clear()
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required', 'error')
            return render_template('signup.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'error')
            return render_template('signup.html')
        
        # Check if user exists
        if user_exists(username):
            flash('Username already exists', 'error')
            return render_template('signup.html')
        
        if email_exists(email):
            flash('Email already exists', 'error')
            return render_template('signup.html')
        
        # Create user
        if not create_user(username, email, password):
            flash('Error creating account', 'error')
            return render_template('signup.html')
        
        # Set session for the new user
        session['username'] = username
        session['email'] = email
        session['profile_completed'] = 0
        
        flash('Account created successfully! Please complete your profile.', 'success')
        return redirect(url_for('user_details'))
    
    return render_template('signup.html')

@app.route('/user-details', methods=['GET', 'POST'])
def user_details():
    """User details page for completing profile after signup"""
    if 'username' not in session:
        flash('Please login first', 'error')
        return redirect(url_for('login'))

    # If the user already finished their profile, skip this step and launch the app
    existing_user = get_user_by_email(session.get('email', ''))
    if existing_user and existing_user.get('profile_completed'):
        session['profile_completed'] = existing_user['profile_completed']
        return redirect(url_for('start_streamlit'))
    
    if request.method == 'POST':
        # Check if user clicked skip
        if request.form.get('skip'):
            session['profile_completed'] = existing_user['profile_completed'] if existing_user else 0
            return redirect(url_for('start_streamlit'))
        
        # Get form data
        age = request.form.get('age', '').strip()
        gender = request.form.get('gender', '').strip()
        height = request.form.get('height', '').strip()
        weight = request.form.get('weight', '').strip()
        
        # Update user profile in database (fitness level/goal removed)
        db = get_db()
        cursor = db.cursor()
        try:
            cursor.execute('''
                UPDATE users 
                SET age = ?, gender = ?, height = ?, weight = ?, profile_completed = 1
                WHERE email = ?
            ''', (age if age else None, 
                  gender if gender else None,
                  float(height) if height else None, 
                  float(weight) if weight else None,
                  session['email']))
            db.commit()
            db.close()
            
            session['profile_completed'] = 1
            flash('Profile completed successfully!', 'success')
            return redirect(url_for('start_streamlit'))
        except Exception as e:
            db.close()
            flash(f'Error updating profile: {str(e)}', 'error')
            return render_template('user_details.html', username=session['username'])
    
    return render_template('user_details.html', username=session['username'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        # Check credentials
        user = get_user_by_email(email)
        
        if not user or not check_password_hash(user['password'], password):
            flash('Invalid email or password', 'error')
            return render_template('login.html')
        
        # Set session
        session['username'] = user['username']
        session['email'] = user['email']
        session['profile_completed'] = user.get('profile_completed', 0)
        
        return redirect(url_for('start_streamlit'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('landing'))

@app.route('/dashboard')
def dashboard():
    """User dashboard - requires login"""
    if 'username' not in session:
        flash('Please login to access the dashboard', 'error')
        return redirect(url_for('login'))
    
    return render_template('dashboard.html', username=session['username'])

@app.route('/trainer')
def trainer():
    """Launch Streamlit trainer - requires login"""
    if 'username' not in session:
        flash('Please login to access the trainer', 'error')
        return redirect(url_for('login'))
    
    # Provide link/instructions to Streamlit app
    return render_template('trainer.html', 
                         username=session['username'],
                         streamlit_url='http://localhost:8501')

@app.route('/start-streamlit')
def start_streamlit():
    """Start Streamlit app (if not running)"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    global streamlit_process
    
    # Check if already running
    if streamlit_process and streamlit_process.poll() is None:
        # Already running, redirect directly to Streamlit with user info
        email = session.get('email', '')
        username = session.get('username', '')
        return redirect(f'http://localhost:8501/?email={email}&username={username}')
    
    # Start Streamlit
    try:
        import time
        import socket
        
        # Check if port 8501 is already in use
        def is_port_open(port):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        
        env = os.environ.copy()
        # Provide user info via environment as a fallback
        env['USER_EMAIL'] = session.get('email', '')
        env['USERNAME'] = session.get('username', '')

        # If port is in use, try to connect directly
        if is_port_open(8501):
            email = session.get('email', '')
            username = session.get('username', '')
            return redirect(f'http://localhost:8501/?email={email}&username={username}')
        
        # Start new Streamlit process with better output handling
        streamlit_process = subprocess.Popen(
            ['streamlit', 'run', 'streamlit_app.py', '--server.port', '8501', '--server.headless', 'true'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env
        )
        
        # Wait for Streamlit to be ready (up to 10 seconds)
        for i in range(20):
            time.sleep(0.5)
            if is_port_open(8501):
                email = session.get('email', '')
                username = session.get('username', '')
                return redirect(f'http://localhost:8501/?email={email}&username={username}')
        
        # If we get here, Streamlit didn't start
        flash('Streamlit app took too long to start. Please try again.', 'error')
        return redirect(url_for('user_details'))
        
    except Exception as e:
        print(f"Error starting Streamlit: {str(e)}")
        flash(f'Error starting Streamlit: {str(e)}. Make sure you have Streamlit installed (pip install streamlit)', 'error')
        return redirect(url_for('user_details'))

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/features')
def features():
    """Features page"""
    return render_template('features.html')

@app.errorhandler(404)
def page_not_found(e):
    """404 error handler"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    """500 error handler"""
    return render_template('500.html'), 500

def cleanup():
    """Cleanup function to stop Streamlit on exit"""
    global streamlit_process
    if streamlit_process:
        try:
            streamlit_process.send_signal(signal.SIGTERM)
            streamlit_process.wait(timeout=5)
        except:
            pass

if __name__ == '__main__':
    try:
        # Run Flask app on port 5000
        app.run(debug=True, port=5000, host='0.0.0.0')
    finally:
        cleanup()