import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = 'super_secret_key_ccs_sit_in' 

# --- DATABASE CONNECTION ---
def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- INITIALIZE DATABASE ---
def init_db():
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

# Initialize the table when the app starts
init_db()

# --- ROUTES ---

@app.route('/')
def home():
    # If user is logged in, skip the login page and go to dashboard
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1. Get data from form
        id_number = request.form['id_number']
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        middlename = request.form.get('middlename', '') 
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
            # Success! Return to Home Page to Login
            return redirect(url_for('home')) 
            
        except sqlite3.IntegrityError:
            return "Error: This ID Number is already registered."

    # If GET request, show the form
    return render_template('register.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if a user with this email exists
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user:
        # Check if the password matches
        if user['password'] == password:
            # Login successful! Save user to session
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            return redirect(url_for('dashboard'))
        else:
            return "Incorrect Password! <a href='/'>Try Again</a>"
    else:
        return "Email not found! <a href='/'>Try Again</a>"

@app.route('/dashboard')
def dashboard():
    # Protect this page!
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    return f"<h1>Welcome, {session['firstname']}!</h1><p>You are now logged in.</p><a href='/logout'>Logout</a>"

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)