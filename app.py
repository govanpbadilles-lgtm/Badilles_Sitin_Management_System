import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

# =======================================================
# 1. APP CONFIGURATION
# =======================================================
app = Flask(__name__)

# Secret key is required for 'session' (logging in) to work securely.
app.secret_key = 'super_secret_key_ccs_sit_in' 


# =======================================================
# 2. DATABASE MANAGEMENT
# =======================================================

def get_db_connection():
    """Opens a connection to the SQLite database file."""
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row # Allows accessing columns by name (e.g., row['email'])
    return conn

def init_db():
    """Creates the 'users' table if it doesn't exist yet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT UNIQUE NOT NULL,
            lastname TEXT NOT NULL,
            firstname TEXT NOT NULL,
            middlename TEXT,
            course_level TEXT,
            password TEXT NOT NULL,
            email TEXT,
            course TEXT,
            address TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database immediately when the app launches
init_db()


# =======================================================
# 3. ROUTE HANDLERS
# =======================================================

@app.route('/')
def home():
    """
    The Home Page.
    - If user is logged in: Redirect straight to Dashboard.
    - If not logged in: Show the Landing Page (with Login Modal).
    """
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    The Registration Page.
    - GET: Shows the registration form.
    - POST: Receives form data and saves it to the database.
    """
    if request.method == 'POST':
        # 1. Get data from form inputs
        id_number = request.form['id_number']
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        middlename = request.form.get('middlename', '') # Optional field
        course_level = request.form['course_level']
        password = request.form['password']
        email = request.form['email']
        course = request.form['course']
        address = request.form['address']

        # 2. Save to Database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_number, lastname, firstname, middlename, course_level, password, email, course, address))
            
            conn.commit()
            conn.close()
            
            # 3. Success! Redirect to Home so they can Login.
            return redirect(url_for('home')) 
            
        except sqlite3.IntegrityError:
            # This happens if the ID Number already exists in the DB
            return "Error: This ID Number is already registered. <a href='/register'>Try Again</a>"

    # If GET request, just show the HTML form
    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    """
    Handles the Login Logic (triggered by the Modal).
    """
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Find user by email
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user:
        # 2. Check if password matches
        if user['password'] == password:
            # 3. Login Successful -> Save User Info in Session
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            return redirect(url_for('dashboard'))
        else:
            return "Incorrect Password! <a href='/'>Try Again</a>"
    else:
        return "Email not found! <a href='/'>Try Again</a>"


@app.route('/dashboard')
def dashboard():
    """
    The Protected Page.
    - Only visible if you are logged in.
    """
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    return f"<h1>Welcome, {session['firstname']}!</h1><p>You are now logged in.</p><a href='/logout'>Logout</a>"


@app.route('/logout')
def logout():
    """
    Logs the user out by clearing the session.
    """
    session.clear()
    return redirect(url_for('home'))


# =======================================================
# 4. RUN THE APP
# =======================================================
if __name__ == '__main__':
    app.run(debug=True)