import os
import sqlite3
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_ccs_sit_in')

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'students.db')

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
            rating TEXT DEFAULT '',
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
            selected_pc TEXT DEFAULT '',
            res_time TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending'
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_remarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            admin_name TEXT NOT NULL,
            remark_type TEXT NOT NULL,
            message TEXT NOT NULL,
            date_posted DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_software (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            lab         TEXT NOT NULL,
            software    TEXT NOT NULL,
            added_by    TEXT NOT NULL,
            date_added  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            recipient   TEXT NOT NULL,
            type        TEXT NOT NULL,
            message     TEXT NOT NULL,
            link        TEXT DEFAULT '',
            is_read     INTEGER DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
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

def seed_students():
    conn = get_db_connection()
    cursor = conn.cursor()

    students = [
        ('23749626', 'Aranas', 'Maria Nina', 'A', '2nd Year', 'maria@gmail.com', 'BSIT', 'Cebu'),
        ('24963025', 'Taburnal', 'Emmanuel Brylle', 'B', '2nd Year', 'emman@gmail.com', 'BSCS', 'Cebu'),
        ('24653022', 'Froilan', 'Mark', '1st Year', 'mark@gmail.com', 'BSIT', 'Bohol'),
        ('26262230', 'Bellita', 'Engel', 'D', '3rd Year', 'bellita@gmail.com', 'BSCS-AI', 'Cebu'),
        ('23749627', 'Escuadro', 'April', 'E', '4th Year', 'escudaro@gmail.com', 'BSIT', 'Cebu'),
        ('25306750', 'Seaborge', 'Ancline April', 'F', '1st Year', 'april@gmail.com', 'BSBA', 'Cebu'),
        ('24365630', 'Ylaya', 'Neo', 'G', '2nd Year', 'leo@gmail.com', 'BSIT', 'Cebu'),
        ('21325648', 'Guinita', 'Earl', 'H', '3rd Year', 'guinita@gmail.com', 'BSCS', 'Cebu'),
        ('22432456', 'Antoque', 'Ronan', 'I', '4th Year', 'antoque@gmail.com', 'BSIT', 'Toledo'),
        ('24356523', 'Libradilla', 'John Cedrick', 'J', '2nd Year', 'libradilla@gmail.com', 'BSCS-AI', 'Cebu'),
    ]

    for s in students:
        try:
            hashed_pw = generate_password_hash('student123')

            cursor.execute('''
                INSERT INTO users
                (id_number, lastname, firstname, middlename, course_level,
                 password, email, course, address, role, remaining_sessions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'student', ?)
            ''', (
                s[0], s[1], s[2], s[3], s[4],
                hashed_pw,
                s[5], s[6], s[7],
                30 if s[6] in ('BSIT', 'BSCS', 'BSCS-AI') else 15
            ))

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()
    print("10 students added!")


init_db()
create_default_admin()
seed_students()


# =======================================================
# NOTIFICATION HELPER
# =======================================================
def create_notification(conn, recipient, notif_type, message, link=''):
    ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    conn.execute(
        "INSERT INTO notifications (recipient, type, message, link, created_at) VALUES (?, ?, ?, ?, ?)",
        (recipient, notif_type, message, link, ph_time)
    )
    conn.commit()


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


@app.route('/add_admin_remark', methods=['POST'])
def add_admin_remark():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    student_id = request.form.get('student_id')
    admin_name = session.get('firstname')
    remark_type = request.form.get('remark_type')
    message = request.form.get('message')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO admin_remarks (student_id, admin_name, remark_type, message)
        VALUES (?, ?, ?, ?)
    ''', (student_id, admin_name, remark_type, message))
    conn.commit()
    conn.close()

    return redirect(url_for('student_list'))


@app.route('/login', methods=['POST'])
def login():
    id_number = request.form.get('id_number', '').strip()
    password = request.form.get('password', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id_number = ?', (id_number,)).fetchone()
    conn.close()

    if user:
        if check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['firstname'] = user['firstname']
            session['role'] = user['role']
            session['id_number'] = user['id_number']

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

    student = cursor.execute(
        "SELECT * FROM users WHERE id = ?", (session['user_id'],)
    ).fetchone()

    if student is None:
        session.clear()
        conn.close()
        return redirect(url_for('home'))

    announcements = cursor.execute(
        "SELECT * FROM announcements ORDER BY date_posted DESC"
    ).fetchall()

    reservations_raw = cursor.execute("""
        SELECT * FROM reservations
        WHERE id_number = ?
        ORDER BY id DESC
    """, (student['id_number'],)).fetchall()
    reservations = [dict(r) for r in reservations_raw]

    # ── SIT-IN SUMMARY ──────────────────────────────────
    # NOTE: sitin_records has no 'date' or 'pc_number' column.
    # Date is extracted from time_in. Status is 'Active' or 'Completed'.
    summary_row = cursor.execute("""
        SELECT
            COUNT(*)                                                        AS num_sessions,
            COALESCE(CAST(ROUND(SUM(
                CASE WHEN time_out IS NOT NULL
                THEN (julianday(time_out) - julianday(time_in)) * 1440
                ELSE 0 END
            )) AS INTEGER), 0)                                              AS total_minutes,
            COALESCE(CAST(ROUND(AVG(
                CASE WHEN time_out IS NOT NULL
                THEN (julianday(time_out) - julianday(time_in)) * 1440
                ELSE NULL END
            )) AS INTEGER), 0)                                              AS avg_minutes,
            COALESCE(CAST(ROUND(MAX(
                CASE WHEN time_out IS NOT NULL
                THEN (julianday(time_out) - julianday(time_in)) * 1440
                ELSE NULL END
            )) AS INTEGER), 0)                                              AS longest_minutes
        FROM sitin_records
        WHERE id_number = ? AND status = 'Completed'
    """, (student['id_number'],)).fetchone()

    def fmt_duration(total_min):
        """Format minutes into 'Xh Ym' or 'Ym' string."""
        total_min = int(total_min or 0)
        h, m = divmod(total_min, 60)
        if h > 0 and m > 0:
            return f"{h}h {m}m"
        elif h > 0:
            return f"{h}h 0m"
        else:
            return f"{m}m"

    sitin_summary = {
        'total_sessions' : summary_row['num_sessions']   or 0,
        'total_hours'    : fmt_duration(summary_row['total_minutes']),
        'avg_duration'   : fmt_duration(summary_row['avg_minutes']),
        'longest_session': fmt_duration(summary_row['longest_minutes']),
    }

    # ── SIT-IN HISTORY ──────────────────────────────────
    # 'date'      → extracted from time_in via strftime
    # 'pc_number' → not in table, padded manually as '—'
    # status values in DB: 'Active' or 'Completed'
    history_raw = cursor.execute("""
        SELECT
            strftime('%Y-%m-%d', time_in)  AS date,
            strftime('%I:%M %p', time_in)  AS time_in,
            CASE WHEN time_out IS NOT NULL
                 THEN strftime('%I:%M %p', time_out)
                 ELSE NULL END             AS time_out,
            CASE WHEN time_out IS NOT NULL THEN
                CASE
                    WHEN CAST(ROUND((julianday(time_out) - julianday(time_in)) * 1440) AS INTEGER) >= 60
                    THEN CAST(CAST(ROUND((julianday(time_out) - julianday(time_in)) * 1440) AS INTEGER) / 60 AS TEXT)
                         || 'h '
                         || CAST(CAST(ROUND((julianday(time_out) - julianday(time_in)) * 1440) AS INTEGER) % 60 AS TEXT)
                         || 'm'
                    ELSE CAST(CAST(ROUND((julianday(time_out) - julianday(time_in)) * 1440) AS INTEGER) AS TEXT) || 'm'
                END
            ELSE NULL END AS duration,
            lab,
            purpose,
            status
        FROM sitin_records
        WHERE id_number = ?
        ORDER BY time_in DESC
    """, (student['id_number'],)).fetchall()

    # Pad missing pc_number column
    sitin_history = []
    for row in history_raw:
        r = dict(row)
        r['pc_number'] = '—'
        sitin_history.append(r)

    conn.close()

    return render_template('student.html',
        student       = dict(student),
        announcements = announcements,
        reservations  = reservations,
        sitin_summary = sitin_summary,
        sitin_history = sitin_history,
    )

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    total_students = cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'").fetchone()[0]
    current_sitin  = cursor.execute("SELECT COUNT(*) FROM sitin_records WHERE status = 'Active'").fetchone()[0]
    total_sitin    = cursor.execute("SELECT COUNT(*) FROM sitin_records").fetchone()[0]
    announcements  = cursor.execute("SELECT * FROM announcements ORDER BY date_posted DESC").fetchall()
    records        = cursor.execute('''
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s
        JOIN users u ON s.id_number = u.id_number
        ORDER BY s.time_in DESC
    ''').fetchall()

    # ── Analytics: Line Chart (last 7 days) ──────────────
    daily_rows = cursor.execute("""
        SELECT date(time_in) AS day, COUNT(*) AS cnt
        FROM sitin_records
        WHERE date(time_in) >= date('now', '-6 days')
        GROUP BY day
        ORDER BY day ASC
    """).fetchall()

    from datetime import date, timedelta
    today      = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    daily_map  = {row['day']: row['cnt'] for row in daily_rows}
    daily_labels = [d[5:] for d in date_range]          # e.g. "05-10"
    daily_data   = [daily_map.get(d, 0) for d in date_range]

    # ── Analytics: Bar Chart (per lab) ───────────────────
    lab_rows = cursor.execute("""
        SELECT lab, COUNT(*) AS cnt
        FROM sitin_records
        WHERE lab IS NOT NULL AND lab != ''
        GROUP BY lab
        ORDER BY cnt DESC
    """).fetchall()
    lab_labels = [r['lab'] for r in lab_rows]
    lab_data   = [r['cnt'] for r in lab_rows]

    # ── Analytics: Pie Chart (per purpose) ───────────────
    purpose_rows = cursor.execute("""
        SELECT purpose, COUNT(*) AS cnt
        FROM sitin_records
        WHERE purpose IS NOT NULL AND purpose != ''
        GROUP BY purpose
        ORDER BY cnt DESC
    """).fetchall()
    purpose_labels = [r['purpose'] for r in purpose_rows]
    purpose_data   = [r['cnt'] for r in purpose_rows]

    conn.close()

    return render_template('admin_dashboard.html',
        firstname      = session['firstname'],
        total_students = total_students,
        current_sitin  = current_sitin,
        total_sitin    = total_sitin,
        announcements  = announcements,
        records        = records,
        daily_labels   = daily_labels,
        daily_data     = daily_data,
        lab_labels     = lab_labels,
        lab_data       = lab_data,
        purpose_labels = purpose_labels,
        purpose_data   = purpose_data,
    )


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


@app.route('/get_occupied_pcs')
def get_occupied_pcs():
    lab = request.args.get('lab', '')
    if not lab:
        return jsonify({'occupied': []})

    conn = get_db_connection()
    cursor = conn.cursor()
    rows = cursor.execute("""
        SELECT selected_pc FROM reservations
        WHERE res_lab = ? AND status IN ('Pending', 'Approved') AND selected_pc != ''
    """, (lab,)).fetchall()
    conn.close()

    occupied = []
    for row in rows:
        pc = row['selected_pc']
        if pc and pc.upper().startswith('PC'):
            try:
                occupied.append(int(pc[2:]))
            except ValueError:
                pass

    return jsonify({'occupied': occupied})


@app.route('/reports')
def reports():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    start_date     = request.args.get('start_date', '')
    end_date       = request.args.get('end_date', '')
    lab_filter     = request.args.get('lab', '')
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

    records  = cursor.execute(query, params).fetchall()
    labs     = cursor.execute("SELECT DISTINCT lab FROM sitin_records WHERE lab IS NOT NULL").fetchall()
    purposes = cursor.execute("SELECT DISTINCT purpose FROM sitin_records WHERE purpose IS NOT NULL").fetchall()
    conn.close()

    return render_template('reports.html', records=records, labs=labs, purposes=purposes,
                           start_date=start_date, end_date=end_date,
                           lab_filter=lab_filter, purpose_filter=purpose_filter)


@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    message    = request.form['message']
    admin_name = session['firstname']
    ph_time    = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %I:%M %p')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO announcements (admin_name, message, date_posted)
        VALUES (?, ?, ?)
    ''', (admin_name, message, ph_time))
    conn.commit()

    students = cursor.execute(
        "SELECT id_number FROM users WHERE role = 'student'"
    ).fetchall()

    preview = message[:80] + ('...' if len(message) > 80 else '')
    for s in students:
        create_notification(
            conn,
            recipient  = s['id_number'],
            notif_type = 'announcement',
            message    = f"📢 New announcement from Admin: {preview}",
            link       = '/dashboard'
        )

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

    student = cursor.execute(
        "SELECT * FROM users WHERE id_number = ? AND role = 'student'", (id_number,)
    ).fetchone()

    if not student:
        conn.close()
        return jsonify({'found': False, 'message': 'Student not found!'})

    sitin = cursor.execute(
        "SELECT * FROM sitin_records WHERE id_number = ? AND status = 'Active'", (id_number,)
    ).fetchone()
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


@app.route('/admin_add_student', methods=['POST'])
def admin_add_student():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    id_number    = request.form.get('id_number')
    firstname    = request.form.get('firstname')
    lastname     = request.form.get('lastname')
    middlename   = request.form.get('middlename', '')
    course       = request.form.get('course')
    course_level = request.form.get('course_level')
    default_pw   = generate_password_hash('default123')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO users (id_number, lastname, firstname, middlename, course, course_level, password, role, remaining_sessions)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'student', ?)
        ''', (id_number, lastname, firstname, middlename, course, course_level, default_pw,
              30 if course in ('BSIT', 'BSCS', 'BSCS-AI') else 15))
        conn.commit()
    except Exception as e:
        print('Error adding student:', e)
    finally:
        conn.close()

    return redirect(url_for('student_list'))


@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
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

    user_id   = session['user_id']
    firstname = request.form['firstname']
    lastname  = request.form['lastname']
    course    = request.form['course']
    address   = request.form['address']

    conn = get_db_connection()
    cursor = conn.cursor()

    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        filename        = secure_filename(file.filename)
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
    lab       = request.form['lab']
    purpose   = request.form['purpose']

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

    record = cursor.execute(
        "SELECT id_number, status FROM sitin_records WHERE id = ?", (record_id,)
    ).fetchone()

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

    record = cursor.execute(
        "SELECT id_number, status FROM sitin_records WHERE id = ?", (record_id,)
    ).fetchone()

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

    firstname    = request.form['firstname']
    middlename   = request.form.get('middlename', '')
    lastname     = request.form['lastname']
    course       = request.form['course']
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

    record_id     = request.form['record_id']
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
    id_number   = request.form['id_number']
    res_date    = request.form['res_date']
    res_lab     = request.form['res_lab']
    res_purpose = request.form['res_purpose']
    selected_pc = request.form.get('selected_pc', '')
    res_time    = request.form.get('res_time', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO reservations (id_number, res_date, res_lab, res_purpose, selected_pc, res_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (id_number, res_date, res_lab, res_purpose, selected_pc, res_time))
    conn.commit()

    student = cursor.execute(
        "SELECT firstname, lastname FROM users WHERE id_number = ?", (id_number,)
    ).fetchone()
    student_name = f"{student['firstname']} {student['lastname']}" if student else id_number

    pc_info = f" ({selected_pc})" if selected_pc else ""

    create_notification(
        conn,
        recipient  = 'admin',
        notif_type = 'reservation',
        message    = f"📅 {student_name} requested {res_lab}{pc_info} on {res_date} for {res_purpose}.",
        link       = '/admin_reservations'
    )

    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/submit_student_feedback', methods=['POST'])
def submit_student_feedback():
    id_number    = request.form['id_number']
    student_name = request.form['student_name']
    message      = request.form['message']
    rating       = request.form.get('rating', '')

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO student_feedback (id_number, student_name, message, rating)
        VALUES (?, ?, ?, ?)
    ''', (id_number, student_name, message, rating))
    conn.commit()

    preview = message[:50] + ('...' if len(message) > 50 else '')
    create_notification(
        conn,
        recipient  = 'admin',
        notif_type = 'announcement',
        message    = f"💬 New feedback from {student_name} ({rating}): {preview}",
        link       = '/admin_feedbacks'
    )

    conn.close()
    return redirect(url_for('dashboard'))


@app.route('/leaderboard')
def leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

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

    leaderboard_data = []
    for s in students:
        points_sitins = min((s['total_sitins'] / 30) * 50, 50)
        points_hours  = min((s['total_hours']  / 100) * 30, 30)
        points_tasks  = min((s['tasks_completed'] / 30) * 20, 20)
        total_points  = round(points_sitins + points_hours + points_tasks, 2)

        leaderboard_data.append({
            'id_number':       s['id_number'],
            'firstname':       s['firstname'],
            'lastname':        s['lastname'],
            'course':          s['course'],
            'profile_pic':     s['profile_pic'],
            'total_sitins':    s['total_sitins'],
            'total_hours':     round(s['total_hours'], 1),
            'tasks_completed': s['tasks_completed'],
            'points_sitins':   round(points_sitins, 1),
            'points_hours':    round(points_hours, 1),
            'points_tasks':    round(points_tasks, 1),
            'total_points':    total_points
        })

    leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
    for i, student in enumerate(leaderboard_data):
        student['rank'] = i + 1

    return render_template('leaderboard.html',
                           leaderboard=leaderboard_data,
                           role=session.get('role'),
                           current_user_id=session.get('user_id'))


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


@app.route('/admin_feedbacks')
def admin_feedbacks():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()
    feedbacks = cursor.execute(
        "SELECT * FROM student_feedback ORDER BY date_submitted DESC"
    ).fetchall()
    conn.close()

    return render_template('admin_feedbacks.html', feedbacks=feedbacks)


@app.route('/process_reservation/<int:res_id>/<string:action>', methods=['POST'])
def process_reservation(res_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    if action not in ('approve', 'decline'):
        return redirect(url_for('admin_reservations'))

    status = 'Approved' if action == 'approve' else 'Declined'

    conn = get_db_connection()
    cursor = conn.cursor()

    res_row = cursor.execute(
        "SELECT * FROM reservations WHERE id = ?", (res_id,)
    ).fetchone()

    cursor.execute(
        "UPDATE reservations SET status = ? WHERE id = ?", (status, res_id)
    )
    conn.commit()

    if res_row:
        pc_info = f" ({res_row['selected_pc']})" if res_row['selected_pc'] else ""
        if action == 'approve':
            create_notification(
                conn,
                recipient  = res_row['id_number'],
                notif_type = 'approved',
                message    = f"✅ Your reservation for {res_row['res_lab']}{pc_info} on {res_row['res_date']} has been APPROVED!",
                link       = '/dashboard'
            )
        else:
            create_notification(
                conn,
                recipient  = res_row['id_number'],
                notif_type = 'declined',
                message    = f"❌ Your reservation for {res_row['res_lab']}{pc_info} on {res_row['res_date']} was declined.",
                link       = '/dashboard'
            )

    conn.close()
    return redirect(url_for('admin_reservations'))


@app.route('/ai_recommendation')
def ai_recommendation():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    student = cursor.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    history = cursor.execute(
        'SELECT * FROM sitin_records WHERE id_number = ?', (student['id_number'],)
    ).fetchall()
    total_sitins = len(history)
    conn.close()

    course_tips = "Keep exploring and applying technology to your field of study."
    if "BSIT" in student['course'].upper() or "IT" in student['course'].upper():
        course_tips = "Focus on your Python and Flask projects. System architecture is a great skill!"

    recommendation = (
        f"Hello {student['firstname']}! You have {student['remaining_sessions']} sessions left "
        f"and completed {total_sitins} sit-ins. {course_tips}"
    )

    return jsonify({
        'name':               student['firstname'],
        'course':             student['course'],
        'remaining_sessions': student['remaining_sessions'],
        'total_sitins':       total_sitins,
        'recommendation':     recommendation
    })


# =======================================================
# NOTIFICATION ROUTES
# =======================================================

@app.route('/notifications/count')
def notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})

    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')

    conn = get_db_connection()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM notifications WHERE recipient = ? AND is_read = 0",
        (recipient,)
    ).fetchone()
    conn.close()

    return jsonify({'count': row['cnt'] if row else 0})


@app.route('/notifications/list')
def notifications_list():
    if 'user_id' not in session:
        return jsonify([])

    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')

    conn = get_db_connection()
    rows = conn.execute(
        """SELECT id, type, message, link, is_read, created_at
           FROM notifications
           WHERE recipient = ?
           ORDER BY created_at DESC
           LIMIT 20""",
        (recipient,)
    ).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


@app.route('/notifications/read/<int:notif_id>', methods=['POST'])
def notification_read(notif_id):
    conn = get_db_connection()
    conn.execute("UPDATE notifications SET is_read = 1 WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()
    return jsonify({'ok': True})


@app.route('/notifications/read_all', methods=['POST'])
def notifications_read_all():
    if 'user_id' not in session:
        return jsonify({'ok': False})

    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')

    conn = get_db_connection()
    conn.execute(
        "UPDATE notifications SET is_read = 1 WHERE recipient = ?", (recipient,)
    )
    conn.commit()
    conn.close()
    return jsonify({'ok': True})

@app.route('/admin_software')
def admin_software():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch all software grouped per lab
    rows = cursor.execute("""
        SELECT * FROM lab_software
        ORDER BY lab ASC, software ASC
    """).fetchall()
    conn.close()

    # Group by lab
    labs_order = ['Lab 524','Lab 526','Lab 528','Lab 530','Lab 542','Lab 544','Mac Lab']
    software_by_lab = {lab: [] for lab in labs_order}
    for row in rows:
        if row['lab'] in software_by_lab:
            software_by_lab[row['lab']].append(dict(row))
        else:
            software_by_lab[row['lab']] = [dict(row)]

    return render_template('admin_software.html',
        firstname       = session.get('firstname', 'Admin'),
        software_by_lab = software_by_lab,
        labs_order      = labs_order,
    )


@app.route('/add_software', methods=['POST'])
def add_software():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    lab      = request.form.get('lab', '').strip()
    software = request.form.get('software', '').strip()

    if not lab or not software:
        return redirect(url_for('admin_software'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for duplicate in same lab
    existing = cursor.execute("""
        SELECT id FROM lab_software WHERE lab = ? AND LOWER(software) = LOWER(?)
    """, (lab, software)).fetchone()

    if not existing:
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("""
            INSERT INTO lab_software (lab, software, added_by, date_added)
            VALUES (?, ?, ?, ?)
        """, (lab, software, session.get('firstname', 'Admin'), ph_time))
        conn.commit()

    conn.close()
    return redirect(url_for('admin_software', added='true'))


@app.route('/delete_software/<int:sw_id>', methods=['POST'])
def delete_software(sw_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))

    conn = get_db_connection()
    conn.execute("DELETE FROM lab_software WHERE id = ?", (sw_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_software', deleted='true'))


@app.route('/get_lab_software')
def get_lab_software():
    """JSON endpoint — used by student dashboard to show software per lab."""
    lab = request.args.get('lab', '')
    if not lab:
        return jsonify([])

    conn = get_db_connection()
    rows = conn.execute("""
        SELECT software FROM lab_software
        WHERE lab = ?
        ORDER BY software ASC
    """, (lab,)).fetchall()
    conn.close()

    return jsonify([r['software'] for r in rows])


# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))