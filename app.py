import os
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash  # FIX #1: Password hashing
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_ccs_sit_in')  # FIX #3: Env variable

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =======================================================
# DATABASE MANAGEMENT
# =======================================================
def get_db_connection():
    conn = sqlite3.connect('students.db')
    conn.row_factory = sqlite3.Row
    return conn

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
            address TEXT,
            role TEXT DEFAULT 'student',
            remaining_sessions INTEGER DEFAULT 30,
            profile_pic TEXT DEFAULT 'default_profile.png'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_name TEXT NOT NULL,
            message TEXT NOT NULL,
            date_posted DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sitin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT NOT NULL,
            purpose TEXT,
            lab TEXT,
            time_in DATETIME DEFAULT CURRENT_TIMESTAMP,
            time_out DATETIME,
            status TEXT DEFAULT 'Active',
            feedback TEXT DEFAULT ''
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            message TEXT NOT NULL,
            date_submitted DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_number TEXT NOT NULL,
            res_date TEXT NOT NULL,
            res_lab TEXT NOT NULL,
            res_purpose TEXT NOT NULL,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    conn.commit()
    conn.close()

def create_default_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    admin = cursor.execute("SELECT * FROM users WHERE role = 'admin'").fetchone()
    if not admin:
        try:
            # FIX #1 APPLIED: Hash the default admin password
            hashed_pw = generate_password_hash('admin123')
            cursor.execute('''
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address, role)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', ('ADMIN-001', 'Admin', 'CCS', '', 'N/A', hashed_pw, 'admin@ccs.edu.ph', 'N/A', 'UC Campus', 'admin'))
            conn.commit()
            print("Default admin account successfully created!")
        except sqlite3.IntegrityError:
            pass
    conn.close()

init_db()
create_default_admin()


# =======================================================
# ROUTE HANDLERS
# =======================================================
@app.route('/')
def home():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
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

        if course in ['BSIT', 'BSCS', 'BSCS-AI']:
            sessions = 30
        else:
            sessions = 15

        # FIX #1 APPLIED: Hash password before saving
        hashed_pw = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address, remaining_sessions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (id_number, lastname, firstname, middlename, course_level, hashed_pw, email, course, address, sessions))
            conn.commit()
            conn.close()
            return redirect(url_for('home', registered='true'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Error: This ID Number is already registered. <a href='/register'>Try Again</a>"

    return render_template('register.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()

    # FIX #3 APPLIED: Admin bypass kuhaa na, gamiton ang database login para sa tanan
    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user:
        # FIX #1 APPLIED: check_password_hash para sa verification
        if check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            session['role'] = user['role']

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard', login='success'))
            else:
                return redirect(url_for('dashboard', login='success'))
        else:
            return redirect(url_for('home', error='true'))
    else:
        return redirect(url_for('home', error='true'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') == 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    student = cursor.execute("SELECT * FROM users WHERE id = ?", (session['user_id'],)).fetchone()

    if student is None:
        session.clear()
        conn.close()
        return redirect(url_for('home'))

    announcements = cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC").fetchall()

    # BAG-O: Kuhaon ang reservations sa current student
    reservations = cursor.execute("""
        SELECT * FROM reservations 
        WHERE id_number = ? 
        ORDER BY id DESC
    """, (student['id_number'],)).fetchall()

    conn.close()

    return render_template('student.html', student=student, announcements=announcements, reservations=reservations)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    total_students = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    current_sitin = cursor.execute("SELECT COUNT(*) FROM sitin_records WHERE status = 'Active'").fetchone()[0]
    total_sitin = cursor.execute("SELECT COUNT(*) FROM sitin_records").fetchone()[0]
    announcements = cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC").fetchall()
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
                           records=records)


@app.route('/history')
def history():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    records = cursor.execute('''
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s
        JOIN users u ON s.id_number = u.id_number
        ORDER BY s.time_in DESC
    ''').fetchall()
    conn.close()

    return render_template('history.html', records=records)


@app.route('/active_sitins')
def active_sitins():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    active_records = cursor.execute('''
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s
        JOIN users u ON s.id_number = u.id_number
        WHERE s.status = 'Active'
        ORDER BY s.time_in DESC
    ''').fetchall()
    conn.close()

    return render_template('active_sitins.html', active_records=active_records)


@app.route('/reports')
def reports():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    lab_filter = request.args.get('lab', '')
    purpose_filter = request.args.get('purpose', '')

    query = '''
        SELECT s.*, u.firstname, u.lastname, u.course
        FROM sitin_records s
        JOIN users u ON s.id_number = u.id_number
        WHERE 1=1
    '''
    params = []

    if start_date:
        query += " AND date(s.time_in) >= date(?)"
        params.append(start_date)
    if end_date:
        query += " AND date(s.time_in) <= date(?)"
        params.append(end_date)
    if lab_filter:
        query += " AND s.lab = ?"
        params.append(lab_filter)
    if purpose_filter:
        query += " AND s.purpose = ?"
        params.append(purpose_filter)

    query += " ORDER BY s.time_in DESC"

    records = cursor.execute(query, params).fetchall()
    labs = cursor.execute("SELECT DISTINCT lab FROM sitin_records WHERE lab IS NOT NULL").fetchall()
    purposes = cursor.execute("SELECT DISTINCT purpose FROM sitin_records WHERE purpose IS NOT NULL").fetchall()
    conn.close()

    return render_template('reports.html', records=records, labs=labs, purposes=purposes,
                           start_date=start_date, end_date=end_date, lab_filter=lab_filter, purpose_filter=purpose_filter)


@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    message = request.form['message']
    admin_name = session['firstname']
    ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %I:%M %p')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO announcements (admin_name, message, date_posted)
        VALUES (?, ?, ?)
    ''', (admin_name, message, ph_time))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_dashboard', posted='true'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home', logout='success'))


@app.route('/search_student')
def search_student():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    id_number = request.args.get('id_number')
    conn = get_db_connection()
    cursor = conn.cursor()

    student = cursor.execute("SELECT * FROM users WHERE id_number = ? AND role = 'student'", (id_number,)).fetchone()

    if not student:
        conn.close()
        return jsonify({'found': False, 'message': 'Student not found!'})

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
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
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
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    # FIX #5 APPLIED: Resetting based on course type (IT = 30, others = 15)
    cursor.execute("""
        UPDATE users 
        SET remaining_sessions = CASE 
            WHEN course IN ('BSIT', 'BSCS', 'BSCS-AI') THEN 30 
            ELSE 15 
        END
        WHERE role = 'student'
    """)
    conn.commit()
    conn.close()

    return redirect(url_for('student_list'))


@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    user_id = session['user_id']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    course = request.form['course']
    address = request.form['address']

    conn = get_db_connection()
    cursor = conn.cursor()

    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"user_{user_id}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        cursor.execute('''
            UPDATE users SET firstname=?, lastname=?, course=?, address=?, profile_pic=?
            WHERE id=?
        ''', (firstname, lastname, course, address, unique_filename, user_id))
    else:
        cursor.execute('''
            UPDATE users SET firstname=?, lastname=?, course=?, address=?
            WHERE id=?
        ''', (firstname, lastname, course, address, user_id))

    conn.commit()
    conn.close()
    session['firstname'] = firstname

    return redirect(url_for('dashboard', update='success'))


@app.route('/sit_in', methods=['POST'])
def sit_in():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    id_number = request.form['id_number']
    lab = request.form['lab']
    purpose = request.form['purpose']

    conn = get_db_connection()
    cursor = conn.cursor()

    student = cursor.execute("SELECT * FROM users WHERE id_number = ?", (id_number,)).fetchone()

    if student and student['remaining_sessions'] > 0:
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO sitin_records (id_number, purpose, lab, status, time_in)
            VALUES (?, ?, ?, 'Active', ?)
        ''', (id_number, purpose, lab, ph_time))
        conn.commit()

    conn.close()
    return redirect(url_for('admin_dashboard', sitin='success'))


@app.route('/logout_sitin', methods=['POST'])
def logout_sitin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    record_id = request.form['record_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # FIX #2 APPLIED: Gi-apil na ang 'status' sa SELECT para dili mag-error
    record = cursor.execute("SELECT id_number, status FROM sitin_records WHERE id = ?", (record_id,)).fetchone()

    if record and record['status'] == 'Active':
        id_number = record['id_number']
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            UPDATE sitin_records
            SET status = 'Completed', time_out = ?
            WHERE id = ?
        ''', (ph_time, record_id))

        cursor.execute('''
            UPDATE users
            SET remaining_sessions = remaining_sessions - 1
            WHERE id_number = ? AND remaining_sessions > 0
        ''', (id_number,))
        conn.commit()

    conn.close()
    return redirect(url_for('admin_dashboard', logout_sitin='success'))


@app.route('/time_out_sitin', methods=['POST'])
def time_out_sitin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    record_id = request.form['record_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    record = cursor.execute("SELECT id_number, status FROM sitin_records WHERE id = ?", (record_id,)).fetchone()

    if record and record['status'] == 'Active':
        id_number = record['id_number']
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute('''
            UPDATE sitin_records
            SET status = 'Completed', time_out = ?
            WHERE id = ?
        ''', (ph_time, record_id))

        cursor.execute('''
            UPDATE users
            SET remaining_sessions = remaining_sessions - 1
            WHERE id_number = ? AND remaining_sessions > 0
        ''', (id_number,))
        conn.commit()

    conn.close()
    return redirect(url_for('admin_dashboard', timeout='success'))


@app.route('/edit_student/<int:id>', methods=['POST'])
def edit_student(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

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


@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    record_id = request.form['record_id']
    feedback_text = request.form['feedback']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE sitin_records
        SET feedback = ?
        WHERE id = ?
    ''', (feedback_text, record_id))
    conn.commit()
    conn.close()

    return redirect(url_for('history', feedback='success'))


@app.route('/submit_reservation', methods=['POST'])
def submit_reservation():
    id_number = request.form['id_number']
    res_date = request.form['res_date']
    res_lab = request.form['res_lab']
    res_purpose = request.form['res_purpose']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reservations (id_number, res_date, res_lab, res_purpose)
        VALUES (?, ?, ?, ?)
    ''', (id_number, res_date, res_lab, res_purpose))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/submit_student_feedback', methods=['POST'])
def submit_student_feedback():
    id_number = request.form['id_number']
    student_name = request.form['student_name']
    message = request.form['message']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO student_feedback (id_number, student_name, message)
        VALUES (?, ?, ?)
    ''', (id_number, student_name, message))
    conn.commit()
    conn.close()

    return redirect(url_for('dashboard'))


@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all students with their sit-in data for leaderboard calculation
    students = cursor.execute('''
        SELECT 
            u.id,
            u.id_number,
            u.firstname,
            u.lastname,
            u.course,
            u.profile_pic,
            COUNT(s.id) AS total_sitins,
            COALESCE(SUM(
                CASE 
                    WHEN s.time_out IS NOT NULL 
                    THEN (julianday(s.time_out) - julianday(s.time_in)) * 24 
                    ELSE 0 
                END
            ), 0) AS total_hours,
            COUNT(CASE WHEN s.feedback != '' AND s.feedback IS NOT NULL THEN 1 END) AS tasks_completed
        FROM users u
        LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
        WHERE u.role = 'student'
        GROUP BY u.id
    ''').fetchall()

    conn.close()

    # Calculate points for each student
    leaderboard_data = []
    for s in students:
        # Points Earned (50%) - based on total sit-ins, max 30 sessions
        points_sitins = min((s['total_sitins'] / 30) * 50, 50)
        
        # Total Hours Sit-in (30%) - based on hours, max 100 hours
        points_hours = min((s['total_hours'] / 100) * 30, 30)
        
        # Task Completed / Feedback (20%) - based on feedbacks, max 30
        points_tasks = min((s['tasks_completed'] / 30) * 20, 20)
        
        total_points = round(points_sitins + points_hours + points_tasks, 2)

        leaderboard_data.append({
            'id_number': s['id_number'],
            'firstname': s['firstname'],
            'lastname': s['lastname'],
            'course': s['course'],
            'profile_pic': s['profile_pic'],
            'total_sitins': s['total_sitins'],
            'total_hours': round(s['total_hours'], 1),
            'tasks_completed': s['tasks_completed'],
            'points_sitins': round(points_sitins, 1),
            'points_hours': round(points_hours, 1),
            'points_tasks': round(points_tasks, 1),
            'total_points': total_points
        })

    # Sort by total points descending
    leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)

    # Add rank
    for i, student in enumerate(leaderboard_data):
        student['rank'] = i + 1

    current_user_id = session.get('user_id')
    role = session.get('role')

    return render_template('leaderboard.html', 
                           leaderboard=leaderboard_data,
                           role=role,
                           current_user_id=current_user_id)


@app.route('/admin_reservations')
def admin_reservations():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    records = cursor.execute('''
        SELECT r.*, u.firstname, u.lastname
        FROM reservations r
        JOIN users u ON r.id_number = u.id_number
        ORDER BY r.id DESC
    ''').fetchall()
    conn.close()

    return render_template('admin_reservations.html', records=records)


# FIX #4 APPLIED: Gi-ilis ang GET method padulong POST para secure ang data modification
@app.route('/process_reservation/<int:res_id>/<string:action>', methods=['POST'])
def process_reservation(res_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    if action not in ('approve', 'decline'):
        return redirect(url_for('admin_reservations'))

    status = 'Approved' if action == 'approve' else 'Declined'

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE reservations
        SET status = ?
        WHERE id = ?
    ''', (status, res_id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_reservations'))

@app.route('/ai_recommendation')
def ai_recommendation():
    """Nag-generate og AI recommendations base sa data sa estudyante."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # Kuhaon ang data sa estudyante
    student = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    # Kuhaon ang iyang sit-in history aron maihap
    history = cursor.execute('SELECT * FROM sitin_records WHERE id_number = ?', (student['id_number'],)).fetchall()
    total_sitins = len(history)

    conn.close()

    # ==========================================
    # MOCK AI RESPONSE (Para ma-test ang UI nimo)
    # Puhon, pwede nimo i-connect ang Gemini API o OpenAI API diri.
    # ==========================================
    
    course_tips = ""
    if "BSIT" in student['course'].upper() or "IT" in student['course'].upper():
        course_tips = "Focus on your Python and Flask projects. System architecture is a great skill!"
    else:
        course_tips = "Keep exploring and applying technology to your field of study."

    mock_ai_message = f"""Hello {student['firstname']}! Here is your quick academic evaluation:

• You currently have {student['remaining_sessions']} lab sessions remaining. Manage them wisely!
• You have successfully completed {total_sitins} sit-in sessions so far. Great consistency!
• {course_tips}
• Tip: Don't forget to ask the lab admins if you need specific software installed for your capstone or projects.

Keep up the good work in the CCS Laboratory!"""

    # Ibalik ang JSON padulong sa JavaScript
    return jsonify({
        'name': student['firstname'],
        'course': student['course'],
        'remaining_sessions': student['remaining_sessions'],
        'total_sitins': total_sitins,
        'recommendation': mock_ai_message
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)