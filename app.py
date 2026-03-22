import os
import sqlite3
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session,jsonify

app = Flask(__name__)
# Secret key is required for 'session' (logging in) to work securely.
app.secret_key = 'super_secret_key_ccs_sit_in' 

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # Maximum 2MB ang size sa picture
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# =======================================================
# DATABASE MANAGEMENT
# =======================================================
def get_db_connection():
    """Opens a connection to the SQLite database file."""
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. USERS TABLE (Gidugangan og remaining_sessions)
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
            address TEXT,
            role TEXT DEFAULT 'student',
            remaining_sessions INTEGER DEFAULT 30,
            profile_pic TEXT DEFAULT 'default_profile.png'
        )
    ''')

    # 2. ANNOUNCEMENTS TABLE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_name TEXT NOT NULL,
            message TEXT NOT NULL,
            date_posted DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 3. SIT-IN RECORDS TABLE (Bag-o para ma-track ang lab ug purpose)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sitin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT NOT NULL,
            purpose TEXT,
            lab TEXT,
            time_in DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_out DATETIME,
            status TEXT DEFAULT 'Active'
        )
    ''')
    conn.commit()
    conn.close()

def create_default_admin():
    """Magbuhat og automatic nga admin account kung wala pay admin sa database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # I-check kung naa na ba tay user nga naay role nga 'admin'
    admin = cursor.execute("SELECT * FROM users WHERE role = 'admin'").fetchone()
    
    # Kung WALA pay admin, mag-insert ta og usa
    if not admin:
        try:
            cursor.execute('''
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('ADMIN-001', 'Admin', 'CCS', '', 'N/A', 'admin123', 'admin@ccs.edu.ph', 'N/A', 'UC Campus', 'admin'))
            conn.commit()
            print("Default admin account successfully created!")
        except sqlite3.IntegrityError:
            pass 
            
    conn.close()

# Initialize the database and create admin
init_db()
create_default_admin()


# =======================================================
# ROUTE HANDLERS
# =======================================================
@app.route('/')
def home():
    """The Home Page."""
    if 'user_id' in session:
        # Kung naka-login na, i-check kung admin ba o student
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
        
    return render_template('index.html')

@app.route('/about')
def about():
    """The About Page."""
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """The Registration Page."""
    if request.method == 'POST':
        id_number = request.form['id_number']
        lastname = request.form['lastname']
        firstname = request.form['firstname']
        middlename = request.form.get('middlename', '') 
        course_level = request.form['course_level']
        password = request.form['password']
        email = request.form['email']
        course = request.form['course']
        address = request.form['address']

        # ==========================================
        # LOGIC PARA SA SESSIONS BASE SA COURSE
        # ==========================================
        if course in ['BSIT', 'BSCS', 'BSCS-AI']:
            sessions = 30
        else:
            sessions = 15
        # ==========================================

        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # GI-UPDATE: Gi-apil na nato ang 'remaining_sessions' ug ang variable nga 'sessions' sa tumoy
            cursor.execute('''
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address, remaining_sessions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_number, lastname, firstname, middlename, course_level, password, email, course, address, sessions))
            
            conn.commit()
            conn.close()
            
            # Success! Redirect to Home and tell it to show the toast
            return redirect(url_for('home', registered='true'))
            
        except sqlite3.IntegrityError:
            return "Error: This ID Number is already registered. <a href='/register'>Try Again</a>"
        
    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    """Handles the Login Logic."""
    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user:
        if user['password'] == password:
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            session['role'] = user['role'] 
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard', login='success'))
            else:
                # GIDUGANG NATO ANG login='success' PARA SA TOAST SA STUDENT
                return redirect(url_for('dashboard', login='success'))
        else:
            return redirect(url_for('home', error='true'))
    else:
        return redirect(url_for('home', error='true'))

@app.route('/dashboard')
def dashboard():
    """The Protected Student Page."""
    if 'user_id' not in session or session.get('role') == 'admin':
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kuhaon ang kompleto nga info sa ni-login nga estudyante
    student = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()
    
    # --- KINI ANG ATONG BAG-ONG SAFETY CHECKER ---
    # Kung ang session naa sa browser pero ang user wala na sa database (na-delete)
    if student is None:
        session.clear() # I-clear ang daan nga session
        conn.close()
        return redirect(url_for('home')) 
    # ---------------------------------------------

    # Kuhaon ang mga announcements gikan sa database
    announcements = cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC").fetchall()
    
    conn.close()
    
    return render_template('student.html', student=student, announcements=announcements)

@app.route('/admin_dashboard')
def admin_dashboard():
    """The Protected Admin Page."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home')) 
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Kuhaon nato ang saktong Statistics gikan sa database
    total_students = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    current_sitin = cursor.execute("SELECT COUNT(*) FROM sitin_records WHERE status = 'Active'").fetchone()[0]
    total_sitin = cursor.execute("SELECT COUNT(*) FROM sitin_records").fetchone()[0]
    
    # 2. Kuhaon nato ang mga Announcements
    announcements = cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC").fetchall()

    # 3. BAG-O: Kuhaon nato ang mga Sit-in Records (Gi-join nato sa users para makuha ang pangalan)
    records = cursor.execute('''
        SELECT s.*, u.firstname, u.lastname 
        FROM sitin_records s
        JOIN users u ON s.id_number = u.id_number
        ORDER BY s.time_in DESC
    ''').fetchall()
    
    conn.close()

    return render_template('admin_dashboard.html', 
                           firstname=session['firstname'],
                           total_students=total_students,
                           current_sitin=current_sitin,
                           total_sitin=total_sitin,
                           announcements=announcements,
                           records=records) # Gipasa nato ang records padulong sa HTML

@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    """Para mo-save sa announcement padulong sa database nga naay saktong oras."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
        
    message = request.form['message']
    admin_name = session['firstname']
    
    # 1. Kuhaon ang saktong oras sa Pilipinas (UTC + 8)
    from datetime import datetime, timedelta
    ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %I:%M %p') # Gibutangan nakog %I:%M %p para AM/PM ang format
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 2. I-apil nato ang ph_time sa pag-insert as date_posted
    cursor.execute('''
        INSERT INTO announcements (admin_name, message, date_posted) 
        VALUES (?, ?, ?)
    ''', (admin_name, message, ph_time))
    
    conn.commit()
    conn.close()
    
    # Mobalik sa admin dashboard nga naay signal nga success
    return redirect(url_for('admin_dashboard', posted='true'))

@app.route('/logout')
def logout():
    """Logs the user out by clearing the session."""
    session.clear()
    return redirect(url_for('home'))


@app.route('/search_student')
def search_student():
    """Kini mo-pangita sa estudyante gamit ang ID Number ug ibalik ang iyang info."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    id_number = request.args.get('id_number')
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pangitaon ang student
    student = cursor.execute("SELECT * FROM users WHERE id_number = ? AND role = 'student'", (id_number,)).fetchone()

    if not student:
        conn.close()
        return jsonify({'found': False, 'message': 'Student not found!'})

    # Pangitaon kung naay 'Active' nga sit-in karon
    sitin = cursor.execute("SELECT * FROM sitin_records WHERE id_number = ? AND status = 'Active'", (id_number,)).fetchone()
    conn.close()

    return jsonify({
        'found': True,
        'id_number': student['id_number'],
        'name': f"{student['firstname']} {student['lastname']}",
        'remaining_sessions': student['remaining_sessions'],
        'purpose': sitin['purpose'] if sitin else 'N/A (Not currently in a lab)',
        'lab': sitin['lab'] if sitin else 'N/A'
    })

@app.route('/student_list')
def student_list():
    """Admin Page para makita ang tanang registered students."""
    # I-check kung admin ba ang ni-login
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home')) 
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Kuhaon ang listahan sa students
    students = cursor.execute('''
        SELECT id, id_number, firstname, middlename, lastname, course, course_level, remaining_sessions 
        FROM users 
        WHERE role = 'student' 
        ORDER BY lastname ASC
    ''').fetchall()
    
    conn.close()
    
    return render_template('student_list.html', students=students)

@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('student_list'))

@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    """Function para i-reset ang tanang student sessions balik sa 30"""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # I-update ang tanang estudyante, ibalik sa 30 ang sessions
    cursor.execute("UPDATE users SET remaining_sessions = 30 WHERE role = 'student'")
    conn.commit()
    conn.close()
    
    return redirect(url_for('student_list'))

@app.route('/update_profile', methods=['POST'])
def update_profile():
    """Modawat sa mga gi-edit nga info ug bag-ong profile pic."""
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    course = request.form['course']
    address = request.form['address']
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # I-check kung naay gi-upload nga picture
    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        # Himuong safe ang filename ug i-save sa uploads folder
        filename = secure_filename(file.filename)
        # Butangan natog user_id sa unahan para dili magkaparehas og pangalan
        unique_filename = f"user_{user_id}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        
        # I-update apil ang picture
        cursor.execute('''
            UPDATE users SET firstname=?, lastname=?, course=?, address=?, profile_pic=?
            WHERE id=?
        ''', (firstname, lastname, course, address, unique_filename, user_id))
    else:
        # I-update ang info lang (walay picture gi-ilis)
        cursor.execute('''
            UPDATE users SET firstname=?, lastname=?, course=?, address=?
            WHERE id=?
        ''', (firstname, lastname, course, address, user_id))

    conn.commit()
    conn.close()
    
    # I-update ang session name basig nag-ilis siyag firstname
    session['firstname'] = firstname

    return redirect(url_for('dashboard', update='success'))

@app.route('/sit_in', methods=['POST'])
def sit_in():
    """Modawat sa porma gikan sa Search Modal ug mag-record sa Sit-in."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    id_number = request.form['id_number']
    lab = request.form['lab']
    purpose = request.form['purpose']

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Pangitaon ang estudyante ug i-check kung naa pay sessions nabilin
    student = cursor.execute("SELECT * FROM users WHERE id_number = ?", (id_number,)).fetchone()
    
    if student and student['remaining_sessions'] > 0:
        # 1. Kuhaon ang oras sa Pilipinas (UTC + 8)
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        # 2. I-apil nato ang ph_time sa atong pag-save (Gi-dugang ang time_in)
        cursor.execute('''
            INSERT INTO sitin_records (id_number, purpose, lab, status, time_in)
            VALUES (?, ?, ?, 'Active', ?)
        ''', (id_number, purpose, lab, ph_time))
        
        conn.commit()
    
    conn.close()

    return redirect(url_for('admin_dashboard', sitin='success'))

@app.route('/logout_sitin', methods=['POST'])
def logout_sitin():
    """Mo-time out sa estudyante gikan sa laboratory ug mo-minus sa session."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    record_id = request.form['record_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Kuhaon daan nato ang ID Number sa estudyante nga tag-iya aning record
    record = cursor.execute("SELECT id_number FROM sitin_records WHERE id = ?", (record_id,)).fetchone()

    # I-sure nato nga 'Active' pa siya usa nato minusan para dili madoble og minus
    if record and record['status'] == 'Active':
        id_number = record['id_number']

        # 1. Kuhaon ang oras sa Pilipinas (UTC + 8)
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        # 2. I-update ang status padulong 'Completed' ug ipasa ang saktong time_out
        cursor.execute('''
            UPDATE sitin_records 
            SET status = 'Completed', time_out = ? 
            WHERE id = ?
        ''', (ph_time, record_id))
        
        # 3. Minusan ang remaining sessions
        cursor.execute('''
            UPDATE users 
            SET remaining_sessions = remaining_sessions - 1 
            WHERE id_number = ? AND remaining_sessions > 0
        ''', (id_number,))
        conn.commit()
        
    conn.close()

    # I-redirect balik sa dashboard nga naay signal
    return redirect(url_for('admin_dashboard', logout_sitin='success'))

@app.route('/time_out_sitin', methods=['POST'])
def time_out_sitin():
    """Mo-time out sa estudyante gikan sa lab ug mo-minus sa session."""
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    record_id = request.form['record_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Pangitaon nato kung naa ba gyud ang record ug kung Active pa
    record = cursor.execute("SELECT id_number, status FROM sitin_records WHERE id = ?", (record_id,)).fetchone()

    if record and record['status'] == 'Active':
        id_number = record['id_number']

        # 1. Kuhaon ang saktong oras sa Pilipinas (PST)
        from datetime import datetime, timedelta
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        # 2. I-update ang status padulong 'Completed' ug ibutang ang time_out
        cursor.execute('''
            UPDATE sitin_records 
            SET status = 'Completed', time_out = ? 
            WHERE id = ?
        ''', (ph_time, record_id))
        
        # 3. Karon pa nato MINUSAN ang remaining sessions
        cursor.execute('''
            UPDATE users 
            SET remaining_sessions = remaining_sessions - 1 
            WHERE id_number = ? AND remaining_sessions > 0
        ''', (id_number,))
        
        conn.commit()
        
    conn.close()
    
    # I-redirect balik sa dashboard ug magpadala og signal para sa toast
    return redirect(url_for('admin_dashboard', timeout='success'))



# EDIT STUDENT ROUTE
@app.route('/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    
    # Kuhaon ang bag-ong gi-type sa admin didto sa Edit form
    firstname = request.form['firstname']
    middlename = request.form.get('middlename', '')
    lastname = request.form['lastname']
    course = request.form['course']
    course_level = request.form['course_level']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET firstname = ?, middlename = ?, lastname = ?, course = ?, course_level = ?
        WHERE id = ?
    ''', (firstname, middlename, lastname, course, course_level, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('student_list'))

if __name__ == '__main__':
    app.run(debug=True)