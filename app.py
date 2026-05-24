import os
import re
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# ── DB backend detection ──────────────────────────────────────────────────────
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    os.environ['DATABASE_URL'] = DATABASE_URL

USE_PG = bool(DATABASE_URL)
PH     = '%s' if USE_PG else '?'   # SQL placeholder

if USE_PG:
    import psycopg2 # pyright: ignore[reportMissingModuleSource]
    import psycopg2.extras # pyright: ignore[reportMissingModuleSource]
else:
    import sqlite3

# ─────────────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'super_secret_key_ccs_sit_in')

app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, 'students.db')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# =======================================================
# DATABASE CONNECTION
# =======================================================
def get_db_connection():
    if USE_PG:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


def get_setting(conn, key, default=None):
    row = conn.cursor() if USE_PG else conn
    cur = conn.cursor()
    cur.execute(f"SELECT value FROM app_settings WHERE key = {PH}", (key,))
    result = cur.fetchone()
    return result['value'] if result else default


def set_setting(conn, key, value):
    cur = conn.cursor()
    if USE_PG:
        cur.execute(
            "INSERT INTO app_settings (key, value) VALUES (%s, %s) "
            "ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value",
            (key, value)
        )
    else:
        cur.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )


# =======================================================
# DATABASE INIT
# =======================================================
def init_db():
    conn = get_db_connection()
    cur  = conn.cursor()

    SERIAL = "SERIAL"           if USE_PG else "INTEGER"
    AUTO   = ""                 if USE_PG else "AUTOINCREMENT"
    TS     = "TIMESTAMP"        if USE_PG else "DATETIME"
    IGNORE = "ON CONFLICT DO NOTHING" if USE_PG else "OR IGNORE"

    tables = [
        f"""CREATE TABLE IF NOT EXISTS users (
            id {SERIAL} PRIMARY KEY {AUTO},
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
        )""",
        f"""CREATE TABLE IF NOT EXISTS announcements (
            id {SERIAL} PRIMARY KEY {AUTO},
            admin_name TEXT NOT NULL,
            message TEXT NOT NULL,
            date_posted {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS sitin_records (
            id {SERIAL} PRIMARY KEY {AUTO},
            id_number TEXT NOT NULL,
            purpose TEXT,
            lab TEXT,
            pc_number INTEGER,
            time_in {TS} DEFAULT CURRENT_TIMESTAMP,
            time_out {TS},
            status TEXT DEFAULT 'Active',
            feedback TEXT DEFAULT ''
        )""",
        f"""CREATE TABLE IF NOT EXISTS student_feedback (
            id {SERIAL} PRIMARY KEY {AUTO},
            id_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            message TEXT NOT NULL,
            rating TEXT DEFAULT '',
            date_submitted {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS reservations (
            id {SERIAL} PRIMARY KEY {AUTO},
            id_number TEXT NOT NULL,
            res_date TEXT NOT NULL,
            res_lab TEXT NOT NULL,
            res_purpose TEXT NOT NULL,
            selected_pc TEXT DEFAULT '',
            res_time TEXT DEFAULT '',
            status TEXT DEFAULT 'Pending'
        )""",
        f"""CREATE TABLE IF NOT EXISTS admin_remarks (
            id {SERIAL} PRIMARY KEY {AUTO},
            student_id TEXT NOT NULL,
            admin_name TEXT NOT NULL,
            remark_type TEXT NOT NULL,
            message TEXT NOT NULL,
            date_posted {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS lab_software (
            id {SERIAL} PRIMARY KEY {AUTO},
            lab TEXT NOT NULL,
            software TEXT NOT NULL,
            added_by TEXT NOT NULL,
            date_added {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS notifications (
            id {SERIAL} PRIMARY KEY {AUTO},
            recipient TEXT NOT NULL,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            link TEXT DEFAULT '',
            is_read INTEGER DEFAULT 0,
            created_at {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS student_groups (
            id {SERIAL} PRIMARY KEY {AUTO},
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            icon TEXT DEFAULT 'fas fa-users',
            created_by TEXT NOT NULL,
            created_at {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS group_members (
            id {SERIAL} PRIMARY KEY {AUTO},
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            joined_at {TS} DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(group_id, user_id)
        )""",
        f"""CREATE TABLE IF NOT EXISTS lab_pcs (
            id {SERIAL} PRIMARY KEY {AUTO},
            lab TEXT NOT NULL,
            pc_number INTEGER NOT NULL,
            status TEXT DEFAULT 'Working',
            availability TEXT DEFAULT 'Enabled',
            remarks TEXT DEFAULT '',
            last_updated {TS} DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(lab, pc_number)
        )""",
        """CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )""",
        f"""CREATE TABLE IF NOT EXISTS admin_awards (
            id {SERIAL} PRIMARY KEY {AUTO},
            id_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            points INTEGER NOT NULL,
            reason TEXT,
            assigned_by TEXT NOT NULL,
            date_awarded {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
        f"""CREATE TABLE IF NOT EXISTS admin_tasks (
            id {SERIAL} PRIMARY KEY {AUTO},
            id_number TEXT NOT NULL,
            student_name TEXT NOT NULL,
            task_title TEXT NOT NULL,
            description TEXT,
            points INTEGER DEFAULT 0,
            status TEXT DEFAULT 'To Do',
            assigned_by TEXT NOT NULL,
            date_assigned {TS} DEFAULT CURRENT_TIMESTAMP,
            priority TEXT DEFAULT 'Medium',
            due_date TEXT
        )""",
        f"""CREATE TABLE IF NOT EXISTS chat_messages (
            id {SERIAL} PRIMARY KEY {AUTO},
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            response TEXT NOT NULL,
            created_at {TS} DEFAULT CURRENT_TIMESTAMP
        )""",
    ]

    for sql in tables:
        cur.execute(sql)

    # Migrations for existing databases
    try:
        cur.execute("ALTER TABLE admin_tasks ADD COLUMN priority TEXT DEFAULT 'Medium'")
    except Exception:
        pass
    try:
        cur.execute("ALTER TABLE admin_tasks ADD COLUMN due_date TEXT")
    except Exception:
        pass

    if USE_PG:
        cur.execute("INSERT INTO app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", ('reservations_enabled', 'Enabled'))
        cur.execute("INSERT INTO app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", ('feedback_enabled', 'Enabled'))
    else:
        cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", ('reservations_enabled', 'Enabled'))
        cur.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", ('feedback_enabled', 'Enabled'))

    conn.commit()
    conn.close()


def seed_pcs():
    conn = get_db_connection()
    cur  = conn.cursor()
    labs = ['Lab 524', 'Lab 526', 'Lab 528', 'Lab 530', 'Lab 542', 'Lab 544']
    for lab in labs:
        for i in range(1, 51):
            try:
                cur.execute(f"INSERT INTO lab_pcs (lab, pc_number) VALUES ({PH}, {PH})", (lab, i))
            except Exception:
                if USE_PG:
                    conn.rollback()
    conn.commit()
    conn.close()


def create_default_admin():
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE role = {PH}", ('admin',))
    admin = cur.fetchone()
    if not admin:
        try:
            hashed_pw = generate_password_hash('admin123')
            cur.execute(f"""
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level, password, email, course, address, role)
                VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
            """, ('ADMIN-001', 'Admin', 'CCS', '', 'N/A', hashed_pw, 'admin@ccs.edu.ph', 'N/A', 'UC Campus', 'admin'))
            conn.commit()
            print("Default admin account successfully created!")
        except Exception as e:
            print(f"Admin seed error: {e}")
            if USE_PG:
                conn.rollback()
    conn.close()


def seed_students():
    conn = get_db_connection()
    cur  = conn.cursor()
    students = [
        ('23749626', 'Aranas',     'Maria Nina',        'A', '2nd Year', 'maria@gmail.com',    'BSIT',    'Cebu'),
        ('24963025', 'Taburnal',   'Emmanuel Brylle',   'B', '2nd Year', 'emman@gmail.com',    'BSCS',    'Cebu'),
        ('24653022', 'Froilan',    'Mark',              'C', '1st Year', 'mark@gmail.com',     'BSIT',    'Bohol'),
        ('26262230', 'Bellita',    'Engel',             'D', '3rd Year', 'bellita@gmail.com',  'BSCS-AI', 'Cebu'),
        ('23749627', 'Escuadro',   'April',             'E', '4th Year', 'escudaro@gmail.com', 'BSIT',    'Cebu'),
        ('25306750', 'Seaborge',   'Ancline April',     'F', '1st Year', 'april@gmail.com',    'BSBA',    'Cebu'),
        ('24365630', 'Ylaya',      'Neo',               'G', '2nd Year', 'leo@gmail.com',      'BSIT',    'Cebu'),
        ('21325648', 'Guinita',    'Earl',              'H', '3rd Year', 'guinita@gmail.com',  'BSCS',    'Cebu'),
        ('22432456', 'Antoque',    'Ronan',             'I', '4th Year', 'antoque@gmail.com',  'BSIT',    'Toledo'),
        ('24356523', 'Libradilla', 'John Cedrick',      'J', '2nd Year', 'libradilla@gmail.com','BSCS-AI','Cebu'),
    ]
    for s in students:
        try:
            hashed_pw = generate_password_hash('student123')
            cur.execute(f"""
                INSERT INTO users
                (id_number, lastname, firstname, middlename, course_level,
                 password, email, course, address, role, remaining_sessions)
                VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},'student',{PH})
            """, (s[0], s[1], s[2], s[3], s[4], hashed_pw, s[5], s[6], s[7],
                  30 if s[6] in ('BSIT', 'BSCS', 'BSCS-AI') else 15))
        except Exception:
            if USE_PG:
                conn.rollback()
    conn.commit()
    conn.close()
    print("10 students added!")


init_db()
create_default_admin()
seed_students()
seed_pcs()


@app.context_processor
def inject_navbar_title():
    def get_navbar_title():
        return "College of Computer Studies Sit-in Monitoring System"
    return dict(get_navbar_title=get_navbar_title)


# =======================================================
# NOTIFICATION HELPER
# =======================================================
def create_notification(conn, recipient, notif_type, message, link=''):
    ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    cur = conn.cursor()
    cur.execute(
        f"INSERT INTO notifications (recipient, type, message, link, created_at) VALUES ({PH},{PH},{PH},{PH},{PH})",
        (recipient, notif_type, message, link, ph_time)
    )
    conn.commit()


# =======================================================
# DATE HELPERS (SQLite vs PostgreSQL)
# =======================================================
def sql_date(col):
    """Cast a timestamp column to DATE string."""
    if USE_PG:
        return f"TO_CHAR({col}, 'YYYY-MM-DD')"
    return f"strftime('%Y-%m-%d', {col})"

def sql_time(col):
    """Cast a timestamp column to 12-hour time string."""
    if USE_PG:
        return f"TO_CHAR({col}, 'HH12:MI AM')"
    return f"strftime('%I:%M %p', {col})"

def sql_minutes_diff(t_out, t_in):
    """Return minute difference between two timestamp columns."""
    if USE_PG:
        return f"EXTRACT(EPOCH FROM ({t_out} - {t_in})) / 60"
    return f"(julianday({t_out}) - julianday({t_in})) * 1440"

def sql_days_ago(n):
    """SQL expression for N days ago."""
    if USE_PG:
        return f"CURRENT_DATE - INTERVAL '{n} days'"
    return f"date('now', '-{n} days')"


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


@app.route('/community')
def community():
    user_id = session.get('user_id') or 0
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT
            g.*,
            COALESCE((SELECT COUNT(*) FROM group_members WHERE group_id = g.id), 0) AS member_count,
            EXISTS(SELECT 1 FROM group_members WHERE group_id = g.id AND user_id = {PH}) AS is_member
        FROM student_groups g
        ORDER BY g.created_at DESC
    """, (user_id,))
    groups = cur.fetchall()
    conn.close()
    message = request.args.get('message')
    success = request.args.get('success') == '1'
    return render_template('community.html', groups=groups, message=message, success=success)


@app.route('/community/create_group', methods=['POST'])
def create_group():
    if 'user_id' not in session:
        return redirect(url_for('register'))
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon        = request.form.get('icon', 'fas fa-users').strip() or 'fas fa-users'
    if not name or not description:
        return redirect(url_for('community', message='Please provide a name and description.', success='0'))
    conn = get_db_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            f"INSERT INTO student_groups (name, description, icon, created_by) VALUES ({PH},{PH},{PH},{PH})",
            (name, description, icon, session.get('firstname', 'Student'))
        )
        if USE_PG:
            cur.execute("SELECT lastval()")
            group_id = cur.fetchone()[0]
        else:
            group_id = cur.lastrowid
        cur.execute(
            f"INSERT INTO group_members (group_id, user_id) VALUES ({PH},{PH}) ON CONFLICT DO NOTHING" if USE_PG
            else f"INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES ({PH},{PH})",
            (group_id, session['user_id'])
        )
        conn.commit()
        message, success = 'Group created successfully. You have been added as a member.', '1'
    except Exception:
        conn.rollback()
        message, success = 'A group with that name already exists.', '0'
    finally:
        conn.close()
    return redirect(url_for('community', message=message, success=success))


@app.route('/community/join_group/<int:group_id>', methods=['POST'])
def join_group(group_id):
    if 'user_id' not in session:
        return redirect(url_for('register'))
    conn = get_db_connection()
    cur  = conn.cursor()
    if USE_PG:
        cur.execute("INSERT INTO group_members (group_id, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                    (group_id, session['user_id']))
    else:
        cur.execute("INSERT OR IGNORE INTO group_members (group_id, user_id) VALUES (?,?)",
                    (group_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('community', message='You have joined the group.', success='1'))


@app.route('/community/leave_group/<int:group_id>', methods=['POST'])
def leave_group(group_id):
    if 'user_id' not in session:
        return redirect(url_for('register'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"DELETE FROM group_members WHERE group_id = {PH} AND user_id = {PH}",
                (group_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect(url_for('community', message='You have left the group.', success='1'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        id_number    = request.form['id_number']
        lastname     = request.form['lastname']
        firstname    = request.form['firstname']
        middlename   = request.form.get('middlename', '')
        course_level = request.form['course_level']
        password     = request.form['password']
        email        = request.form['email']
        course       = request.form['course']
        address      = request.form['address']
        sessions     = 30 if course in ['BSIT', 'BSCS', 'BSCS-AI'] else 15
        hashed_pw    = generate_password_hash(password)
        conn = get_db_connection()
        cur  = conn.cursor()
        try:
            cur.execute(f"""
                INSERT INTO users (id_number, lastname, firstname, middlename, course_level,
                    password, email, course, address, remaining_sessions)
                VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH})
            """, (id_number, lastname, firstname, middlename, course_level,
                  hashed_pw, email, course, address, sessions))
            conn.commit()
            conn.close()
            return redirect(url_for('home', registered='true'))
        except Exception:
            if USE_PG:
                conn.rollback()
            conn.close()
            return "Error: This ID Number is already registered. <a href='/register'>Try Again</a>"
    return render_template('register.html')


@app.route('/add_admin_remark', methods=['POST'])
def add_admin_remark():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    student_id  = request.form.get('student_id')
    admin_name  = session.get('firstname')
    remark_type = request.form.get('remark_type')
    message     = request.form.get('message')
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        INSERT INTO admin_remarks (student_id, admin_name, remark_type, message)
        VALUES ({PH},{PH},{PH},{PH})
    """, (student_id, admin_name, remark_type, message))
    conn.commit()
    conn.close()
    return redirect(url_for('student_list'))


@app.route('/login', methods=['POST'])
def login():
    id_number = request.form.get('id_number', '').strip()
    password  = request.form.get('password', '').strip()
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id_number = {PH}", (id_number,))
    user = cur.fetchone()
    conn.close()
    if user and check_password_hash(user['password'], password):
        session['user_id']   = user['id']
        session['firstname'] = user['firstname']
        session['role']      = user['role']
        session['id_number'] = user['id_number']
        if user['role'] == 'admin':
            return redirect(url_for('admin_dashboard', login='success'))
        return redirect(url_for('dashboard', login='success'))
    return redirect(url_for('home', error='true'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard' if session.get('role') == 'admin' else 'dashboard'))
    message, success = None, False
    if request.method == 'POST':
        id_number        = request.form.get('id_number', '').strip()
        email            = request.form.get('email', '').strip()
        password         = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        if not all([id_number, email, password, confirm_password]):
            message = 'All fields are required.'
        elif password != confirm_password:
            message = 'The password and confirmation do not match.'
        elif len(password) < 6:
            message = 'Password must be at least 6 characters long.'
        else:
            conn = get_db_connection()
            cur  = conn.cursor()
            cur.execute(f"SELECT * FROM users WHERE id_number = {PH} AND email = {PH}", (id_number, email))
            user = cur.fetchone()
            if user:
                hashed_pw = generate_password_hash(password)
                cur.execute(f"UPDATE users SET password = {PH} WHERE id = {PH}", (hashed_pw, user['id']))
                conn.commit()
                conn.close()
                message, success = 'Password reset successfully. Please log in.', True
            else:
                conn.close()
                message = 'No account found with that ID number and email.'
    return render_template('forgot_password.html', message=message, success=success)


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session or session.get('role') == 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute(f"SELECT * FROM users WHERE id = {PH}", (session['user_id'],))
    student = cur.fetchone()
    if student is None:
        session.clear()
        conn.close()
        return redirect(url_for('home'))

    cur.execute("SELECT * FROM announcements ORDER BY date_posted DESC")
    announcements = cur.fetchall()

    cur.execute(f"SELECT * FROM reservations WHERE id_number = {PH} ORDER BY id DESC", (student['id_number'],))
    reservations = [dict(r) for r in cur.fetchall()]

    # ── Sit-in summary ────────────────────────────────────
    if USE_PG:
        cur.execute(f"""
            SELECT
                COUNT(*)                                                              AS num_sessions,
                COALESCE(ROUND(SUM(
                    CASE WHEN time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (time_out - time_in)) / 60
                    ELSE 0 END
                ))::INTEGER, 0)                                                       AS total_minutes,
                COALESCE(ROUND(AVG(
                    CASE WHEN time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (time_out - time_in)) / 60
                    ELSE NULL END
                ))::INTEGER, 0)                                                       AS avg_minutes,
                COALESCE(ROUND(MAX(
                    CASE WHEN time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (time_out - time_in)) / 60
                    ELSE NULL END
                ))::INTEGER, 0)                                                       AS longest_minutes
            FROM sitin_records
            WHERE id_number = %s AND status = 'Completed'
        """, (student['id_number'],))
    else:
        cur.execute("""
            SELECT
                COUNT(*)                                                              AS num_sessions,
                COALESCE(CAST(ROUND(SUM(
                    CASE WHEN time_out IS NOT NULL
                    THEN (julianday(time_out) - julianday(time_in)) * 1440
                    ELSE 0 END
                )) AS INTEGER), 0)                                                    AS total_minutes,
                COALESCE(CAST(ROUND(AVG(
                    CASE WHEN time_out IS NOT NULL
                    THEN (julianday(time_out) - julianday(time_in)) * 1440
                    ELSE NULL END
                )) AS INTEGER), 0)                                                    AS avg_minutes,
                COALESCE(CAST(ROUND(MAX(
                    CASE WHEN time_out IS NOT NULL
                    THEN (julianday(time_out) - julianday(time_in)) * 1440
                    ELSE NULL END
                )) AS INTEGER), 0)                                                    AS longest_minutes
            FROM sitin_records
            WHERE id_number = ? AND status = 'Completed'
        """, (student['id_number'],))
    summary_row = cur.fetchone()

    def fmt_duration(total_min):
        total_min = int(total_min or 0)
        h, m = divmod(total_min, 60)
        if h > 0:
            return f"{h}h {m}m"
        return f"{m}m"

    sitin_summary = {
        'total_sessions' : summary_row['num_sessions']    or 0,
        'total_hours'    : fmt_duration(summary_row['total_minutes']),
        'avg_duration'   : fmt_duration(summary_row['avg_minutes']),
        'longest_session': fmt_duration(summary_row['longest_minutes']),
    }

    # ── Sit-in history ────────────────────────────────────
    if USE_PG:
        cur.execute("""
            SELECT
                TO_CHAR(time_in,  'YYYY-MM-DD')  AS date,
                TO_CHAR(time_in,  'HH12:MI AM')  AS time_in,
                CASE WHEN time_out IS NOT NULL
                     THEN TO_CHAR(time_out, 'HH12:MI AM')
                     ELSE NULL END               AS time_out,
                CASE WHEN time_out IS NOT NULL THEN
                    CASE
                        WHEN ROUND(EXTRACT(EPOCH FROM (time_out - time_in))/60)::INTEGER >= 60
                        THEN (ROUND(EXTRACT(EPOCH FROM (time_out - time_in))/60)::INTEGER / 60)::TEXT
                             || 'h '
                             || (ROUND(EXTRACT(EPOCH FROM (time_out - time_in))/60)::INTEGER %% 60)::TEXT
                             || 'm'
                        ELSE ROUND(EXTRACT(EPOCH FROM (time_out - time_in))/60)::TEXT || 'm'
                    END
                ELSE NULL END AS duration,
                lab, pc_number, purpose, status
            FROM sitin_records
            WHERE id_number = %s
            ORDER BY time_in DESC
        """, (student['id_number'],))
    else:
        cur.execute("""
            SELECT
                strftime('%Y-%m-%d', time_in)    AS date,
                strftime('%I:%M %p', time_in)    AS time_in,
                CASE WHEN time_out IS NOT NULL
                     THEN strftime('%I:%M %p', time_out)
                     ELSE NULL END               AS time_out,
                CASE WHEN time_out IS NOT NULL THEN
                    CASE
                        WHEN CAST(ROUND((julianday(time_out)-julianday(time_in))*1440) AS INTEGER) >= 60
                        THEN CAST(CAST(ROUND((julianday(time_out)-julianday(time_in))*1440) AS INTEGER)/60 AS TEXT)
                             || 'h '
                             || CAST(CAST(ROUND((julianday(time_out)-julianday(time_in))*1440) AS INTEGER)%60 AS TEXT)
                             || 'm'
                        ELSE CAST(CAST(ROUND((julianday(time_out)-julianday(time_in))*1440) AS INTEGER) AS TEXT)||'m'
                    END
                ELSE NULL END AS duration,
                lab, pc_number, purpose, status
            FROM sitin_records
            WHERE id_number = ?
            ORDER BY time_in DESC
        """, (student['id_number'],))
    sitin_history = [dict(row) for row in cur.fetchall()]

    # ── Leaderboard Rankings ──────────────────────────────
    if USE_PG:
        cur.execute("""
            SELECT u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (s.time_out - s.time_in)) / 3600 ELSE 0 END), 0) AS total_hours,
                COALESCE(SUM(CASE WHEN s.feedback IS NOT NULL AND s.feedback != '' THEN 1 ELSE 0 END), 0) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic
        """)
    else:
        cur.execute("""
            SELECT u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN (julianday(s.time_out)-julianday(s.time_in))*24 ELSE 0 END),0) AS total_hours,
                COALESCE(SUM(CASE WHEN s.feedback IS NOT NULL AND s.feedback != '' THEN 1 ELSE 0 END),0) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic
        """)
    students_lb = cur.fetchall()
    
    leaderboard_data = []
    for s in students_lb:
        total_sitins = int(s['total_sitins'] or 0)
        total_hours = float(s['total_hours'] or 0)
        tasks_completed = int(s['tasks_completed'] or 0)

        pts_sitins = min((total_sitins / 30) * 50, 50)
        pts_hours  = min((total_hours / 100) * 30, 30)
        pts_tasks  = min((tasks_completed / 30) * 20, 20)
        total_pts  = round(pts_sitins + pts_hours + pts_tasks, 2)
        leaderboard_data.append({
            'id_number': s['id_number'], 'firstname': s['firstname'], 'lastname': s['lastname'],
            'course': s['course'], 'profile_pic': s['profile_pic'],
            'total_sitins': total_sitins, 'total_hours': round(total_hours, 1),
            'tasks_completed': tasks_completed,
            'points_sitins': round(pts_sitins, 1), 'points_hours': round(pts_hours, 1),
            'points_tasks': round(pts_tasks, 1), 'total_points': total_pts
        })
    leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
    for i, s in enumerate(leaderboard_data):
        s['rank'] = i + 1

    reservations_enabled = get_setting(conn, 'reservations_enabled', 'Enabled')
    feedback_enabled     = get_setting(conn, 'feedback_enabled',     'Enabled')
    conn.close()

    return render_template('student.html',
        student              = dict(student),
        announcements        = announcements,
        reservations         = reservations,
        sitin_summary        = sitin_summary,
        sitin_history        = sitin_history,
        reservations_enabled = reservations_enabled,
        feedback_enabled     = feedback_enabled,
        leaderboard          = leaderboard_data,
    )


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE role = 'student'"); total_students = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM sitin_records WHERE status = 'Active'"); current_sitin = cur.fetchone()['c']
    cur.execute("SELECT COUNT(*) AS c FROM sitin_records"); total_sitin = cur.fetchone()['c']
    cur.execute("SELECT * FROM announcements ORDER BY date_posted DESC"); announcements = cur.fetchall()
    cur.execute("""
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s JOIN users u ON s.id_number = u.id_number
        ORDER BY s.time_in DESC
    """); records = cur.fetchall()

    # Analytics: daily last 7 days
    if USE_PG:
        cur.execute("""
            SELECT DATE(time_in) AS day, COUNT(*) AS cnt
            FROM sitin_records
            WHERE DATE(time_in) >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY day ORDER BY day ASC
        """)
    else:
        cur.execute("""
            SELECT date(time_in) AS day, COUNT(*) AS cnt
            FROM sitin_records
            WHERE date(time_in) >= date('now', '-6 days')
            GROUP BY day ORDER BY day ASC
        """)
    daily_rows = cur.fetchall()

    from datetime import date
    today      = date.today()
    date_range = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
    daily_map  = {str(row['day']): row['cnt'] for row in daily_rows}
    daily_labels = [d[5:] for d in date_range]
    daily_data   = [daily_map.get(d, 0) for d in date_range]

    cur.execute("""
        SELECT lab, COUNT(*) AS cnt FROM sitin_records
        WHERE lab IS NOT NULL AND lab != ''
        GROUP BY lab ORDER BY cnt DESC
    """)
    lab_rows = cur.fetchall()
    lab_labels = [r['lab'] for r in lab_rows]
    lab_data   = [r['cnt'] for r in lab_rows]

    cur.execute("""
        SELECT purpose, COUNT(*) AS cnt FROM sitin_records
        WHERE purpose IS NOT NULL AND purpose != ''
        GROUP BY purpose ORDER BY cnt DESC
    """)
    purpose_rows   = cur.fetchall()
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
    cur  = conn.cursor()
    cur.execute("""
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s JOIN users u ON s.id_number = u.id_number
        ORDER BY s.time_in DESC
    """)
    records = cur.fetchall()
    conn.close()
    return render_template('history.html', records=records)


@app.route('/active_sitins')
def active_sitins():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT s.*, u.firstname, u.lastname
        FROM sitin_records s JOIN users u ON s.id_number = u.id_number
        WHERE s.status = 'Active' ORDER BY s.time_in DESC
    """)
    active_records = cur.fetchall()
    conn.close()
    return render_template('active_sitins.html', active_records=active_records)


@app.route('/get_occupied_pcs')
def get_occupied_pcs():
    lab = request.args.get('lab', '')
    if not lab:
        return jsonify({'occupied': []})
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT selected_pc FROM reservations
        WHERE res_lab = {PH} AND status IN ('Pending', 'Approved') AND selected_pc != ''
    """, (lab,))
    rows = cur.fetchall()
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
    cur  = conn.cursor()

    start_date     = request.args.get('start_date', '')
    end_date       = request.args.get('end_date', '')
    lab_filter     = request.args.get('lab', '')
    purpose_filter = request.args.get('purpose', '')

    if USE_PG:
        query  = "SELECT s.*, u.firstname, u.lastname, u.course FROM sitin_records s JOIN users u ON s.id_number = u.id_number WHERE 1=1"
        date_cast_start = "DATE(s.time_in) >= %s::DATE"
        date_cast_end   = "DATE(s.time_in) <= %s::DATE"
    else:
        query  = "SELECT s.*, u.firstname, u.lastname, u.course FROM sitin_records s JOIN users u ON s.id_number = u.id_number WHERE 1=1"
        date_cast_start = "date(s.time_in) >= date(?)"
        date_cast_end   = "date(s.time_in) <= date(?)"

    params = []
    if start_date:
        query += f" AND {date_cast_start}"; params.append(start_date)
    if end_date:
        query += f" AND {date_cast_end}";   params.append(end_date)
    if lab_filter:
        query += f" AND s.lab = {PH}";      params.append(lab_filter)
    if purpose_filter:
        query += f" AND s.purpose = {PH}";  params.append(purpose_filter)
    query += " ORDER BY s.time_in DESC"

    cur.execute(query, params)
    records = cur.fetchall()
    cur.execute("SELECT DISTINCT lab FROM sitin_records WHERE lab IS NOT NULL"); labs     = cur.fetchall()
    cur.execute("SELECT DISTINCT purpose FROM sitin_records WHERE purpose IS NOT NULL"); purposes = cur.fetchall()
    conn.close()
    return render_template('reports.html', records=records, labs=labs, purposes=purposes,
        start_date=start_date, end_date=end_date, lab_filter=lab_filter, purpose_filter=purpose_filter)


@app.route('/post_announcement', methods=['POST'])
def post_announcement():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    message    = request.form['message']
    admin_name = session['firstname']
    ph_time    = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %I:%M %p')
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"INSERT INTO announcements (admin_name, message, date_posted) VALUES ({PH},{PH},{PH})",
                (admin_name, message, ph_time))
    conn.commit()
    cur.execute(f"SELECT id_number FROM users WHERE role = {PH}", ('student',))
    students = cur.fetchall()
    preview = message[:80] + ('...' if len(message) > 80 else '')
    for s in students:
        create_notification(conn, recipient=s['id_number'], notif_type='announcement',
                            message=f"📢 New announcement from Admin: {preview}", link='/dashboard')
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
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id_number = {PH} AND role = 'student'", (id_number,))
    student = cur.fetchone()
    if not student:
        conn.close()
        return jsonify({'found': False, 'message': 'Student not found!'})
    cur.execute(f"SELECT * FROM sitin_records WHERE id_number = {PH} AND status = 'Active'", (id_number,))
    sitin = cur.fetchone()
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
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, id_number, firstname, middlename, lastname, course, course_level, remaining_sessions
        FROM users WHERE role = 'student' ORDER BY lastname ASC
    """)
    students = cur.fetchall()
    conn.close()
    return render_template('student_list.html', students=students)


@app.route('/delete_student/<int:id>', methods=['POST'])
def delete_student(id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT id_number FROM users WHERE id={PH}", (id,))
    student = cur.fetchone()
    if student:
        id_number = student['id_number']
        cur.execute(f"DELETE FROM sitin_records WHERE id_number={PH}", (id_number,))
        cur.execute(f"DELETE FROM reservations WHERE id_number={PH}", (id_number,))
        cur.execute(f"DELETE FROM admin_awards WHERE id_number={PH}", (id_number,))
        cur.execute(f"DELETE FROM admin_tasks WHERE id_number={PH}", (id_number,))
        cur.execute(f"DELETE FROM users WHERE id={PH}", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('student_list', deleted='success'))


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
    cur  = conn.cursor()
    try:
        cur.execute(f"""
            INSERT INTO users (id_number, lastname, firstname, middlename, course, course_level, password, role, remaining_sessions)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},'student',{PH})
        """, (id_number, lastname, firstname, middlename, course, course_level, default_pw,
              30 if course in ('BSIT', 'BSCS', 'BSCS-AI') else 15))
        conn.commit()
    except Exception as e:
        print('Error adding student:', e)
        if USE_PG:
            conn.rollback()
    finally:
        conn.close()
    return redirect(url_for('student_list', added='success'))


@app.route('/reset_sessions', methods=['POST'])
def reset_sessions():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        UPDATE users
        SET remaining_sessions = CASE
            WHEN course IN ('BSIT','BSCS','BSCS-AI') THEN 30
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
    cur  = conn.cursor()
    file = request.files.get('profile_pic')
    if file and allowed_file(file.filename):
        filename        = secure_filename(file.filename)
        unique_filename = f"user_{user_id}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
        cur.execute(f"""
            UPDATE users SET firstname={PH}, lastname={PH}, course={PH}, address={PH}, profile_pic={PH}
            WHERE id={PH}
        """, (firstname, lastname, course, address, unique_filename, user_id))
    else:
        cur.execute(f"""
            UPDATE users SET firstname={PH}, lastname={PH}, course={PH}, address={PH}
            WHERE id={PH}
        """, (firstname, lastname, course, address, user_id))
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
    pc_number = request.form.get('pc_number')
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id_number = {PH}", (id_number,))
    student = cur.fetchone()
    if student and student['remaining_sessions'] > 0:
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(f"""
            INSERT INTO sitin_records (id_number, purpose, lab, pc_number, status, time_in)
            VALUES ({PH},{PH},{PH},{PH},'Active',{PH})
        """, (id_number, purpose, lab, pc_number, ph_time))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard', sitin='success'))


@app.route('/logout_sitin', methods=['POST'])
def logout_sitin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    record_id = request.form['record_id']
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT id_number, status FROM sitin_records WHERE id = {PH}", (record_id,))
    record = cur.fetchone()
    if record and record['status'] == 'Active':
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(f"UPDATE sitin_records SET status='Completed', time_out={PH} WHERE id={PH}", (ph_time, record_id))
        cur.execute(f"UPDATE users SET remaining_sessions = remaining_sessions - 1 WHERE id_number={PH} AND remaining_sessions > 0",
                    (record['id_number'],))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard', logout_sitin='success'))


@app.route('/time_out_sitin', methods=['POST'])
def time_out_sitin():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    record_id = request.form['record_id']
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT id_number, status FROM sitin_records WHERE id = {PH}", (record_id,))
    record = cur.fetchone()
    if record and record['status'] == 'Active':
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(f"UPDATE sitin_records SET status='Completed', time_out={PH} WHERE id={PH}", (ph_time, record_id))
        cur.execute(f"UPDATE users SET remaining_sessions = remaining_sessions - 1 WHERE id_number={PH} AND remaining_sessions > 0",
                    (record['id_number'],))
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
    cur  = conn.cursor()
    cur.execute(f"""
        UPDATE users SET firstname={PH}, middlename={PH}, lastname={PH}, course={PH}, course_level={PH}
        WHERE id={PH}
    """, (firstname, middlename, lastname, course, course_level, id))
    conn.commit()
    conn.close()
    return redirect(url_for('student_list', edited='success'))


@app.route('/add_feedback', methods=['POST'])
def add_feedback():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    record_id     = request.form['record_id']
    feedback_text = request.form['feedback']
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"UPDATE sitin_records SET feedback={PH} WHERE id={PH}", (feedback_text, record_id))
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
    cur  = conn.cursor()
    reservations_enabled = get_setting(conn, 'reservations_enabled', 'Enabled')
    if reservations_enabled == 'Disabled':
        conn.close()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Reservations are currently disabled.'}), 403
        return redirect(url_for('dashboard', error='reservation_disabled'))
    try:
        cur.execute(f"""
            INSERT INTO reservations (id_number, res_date, res_lab, res_purpose, selected_pc, res_time)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH})
        """, (id_number, res_date, res_lab, res_purpose, selected_pc, res_time))
        cur.execute(f"SELECT firstname, lastname FROM users WHERE id_number = {PH}", (id_number,))
        student = cur.fetchone()
        student_name = f"{student['firstname']} {student['lastname']}" if student else id_number
        pc_info = f" ({selected_pc})" if selected_pc else ""
        create_notification(conn, recipient='admin', notif_type='reservation',
            message=f"📅 {student_name} requested {res_lab}{pc_info} on {res_date} for {res_purpose}.",
            link='/admin_reservations')
        conn.close()
        return jsonify({'success': True, 'message': 'Reservation created successfully!',
                        'details': {'lab': res_lab, 'pc': selected_pc, 'date': res_date, 'time': res_time}})
    except Exception as e:
        if USE_PG and conn:
            conn.rollback()
        if conn:
            conn.close()
        return jsonify({'success': False, 'message': f'Reservation failed: {str(e)}'}), 500


@app.route('/submit_student_feedback', methods=['POST'])
def submit_student_feedback():
    id_number    = request.form['id_number']
    student_name = request.form['student_name']
    message      = request.form['message']
    rating       = request.form.get('rating', '')
    conn = get_db_connection()
    cur  = conn.cursor()
    feedback_enabled = get_setting(conn, 'feedback_enabled', 'Enabled')
    if feedback_enabled == 'Disabled':
        conn.close()
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Student feedback is currently disabled.'}), 403
        return redirect(url_for('dashboard', error='feedback_disabled'))
    cur.execute(f"INSERT INTO student_feedback (id_number, student_name, message, rating) VALUES ({PH},{PH},{PH},{PH})",
                (id_number, student_name, message, rating))
    preview = message[:50] + ('...' if len(message) > 50 else '')
    create_notification(conn, recipient='admin', notif_type='announcement',
        message=f"💬 New feedback from {student_name} ({rating}): {preview}", link='/admin_feedbacks')
    conn.close()
    return redirect(url_for('dashboard', feedback='success'))


@app.route('/leaderboard')
def leaderboard():
    conn = get_db_connection()
    cur  = conn.cursor()
    if USE_PG:
        cur.execute("""
            SELECT u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (s.time_out - s.time_in)) / 3600 ELSE 0 END), 0) AS total_hours,
                COALESCE(SUM(CASE WHEN s.feedback IS NOT NULL AND s.feedback != '' THEN 1 ELSE 0 END), 0) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic
        """)
    else:
        cur.execute("""
            SELECT u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN (julianday(s.time_out)-julianday(s.time_in))*24 ELSE 0 END),0) AS total_hours,
                COALESCE(SUM(CASE WHEN s.feedback IS NOT NULL AND s.feedback != '' THEN 1 ELSE 0 END),0) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic
        """)
    students = cur.fetchall()
    conn.close()
    leaderboard_data = []
    for s in students:
        total_sitins = int(s['total_sitins'] or 0)
        total_hours = float(s['total_hours'] or 0)
        tasks_completed = int(s['tasks_completed'] or 0)

        pts_sitins = min((total_sitins / 30) * 50, 50)
        pts_hours  = min((total_hours / 100) * 30, 30)
        pts_tasks  = min((tasks_completed / 30) * 20, 20)
        total_pts  = round(pts_sitins + pts_hours + pts_tasks, 2)
        leaderboard_data.append({
            'id_number': s['id_number'], 'firstname': s['firstname'], 'lastname': s['lastname'],
            'course': s['course'], 'profile_pic': s['profile_pic'],
            'total_sitins': total_sitins, 'total_hours': round(total_hours, 1),
            'tasks_completed': tasks_completed,
            'points_sitins': round(pts_sitins, 1), 'points_hours': round(pts_hours, 1),
            'points_tasks': round(pts_tasks, 1), 'total_points': total_pts
        })
    leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
    for i, s in enumerate(leaderboard_data):
        s['rank'] = i + 1

    role = session.get('role')
    if role == 'admin':
        # Re-open connection to query admin details
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("SELECT * FROM admin_awards ORDER BY date_awarded DESC")
        awards = cur.fetchall()
        cur.execute("SELECT * FROM admin_tasks ORDER BY date_assigned DESC")
        tasks = cur.fetchall()
        cur.execute("SELECT id_number, firstname, lastname, course FROM users WHERE role='student' ORDER BY lastname ASC, firstname ASC")
        students_list = cur.fetchall()
        conn.close()
        tab = request.args.get('tab', 'rankings')
        return render_template('admin_leaderboard.html', 
                               leaderboard=leaderboard_data,
                               students=students_list, 
                               awards=awards, 
                               tasks=tasks, 
                               current_tab=tab,
                               role=role,
                               current_user_id=session.get('user_id'))

    if role == 'student':
        return redirect(url_for('dashboard', action='leaderboard'))

    return render_template('leaderboard.html', leaderboard=leaderboard_data,
                           role=role, current_user_id=session.get('user_id'))


@app.route('/api/public/leaderboard')
def public_leaderboard():
    conn = get_db_connection()
    cur  = conn.cursor()
    if USE_PG:
        cur.execute("""
            SELECT u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN EXTRACT(EPOCH FROM (s.time_out - s.time_in)) / 3600 ELSE 0 END), 0) AS total_hours,
                COUNT(CASE WHEN s.feedback != '' AND s.feedback IS NOT NULL THEN 1 END) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id, u.id_number, u.firstname, u.lastname, u.course, u.profile_pic
        """)
    else:
        cur.execute("""
            SELECT u.id_number, u.firstname, u.lastname, u.course, u.profile_pic,
                COUNT(s.id) AS total_sitins,
                COALESCE(SUM(CASE WHEN s.time_out IS NOT NULL
                    THEN (julianday(s.time_out)-julianday(s.time_in))*24 ELSE 0 END),0) AS total_hours,
                COUNT(CASE WHEN s.feedback != '' AND s.feedback IS NOT NULL THEN 1 END) AS tasks_completed
            FROM users u
            LEFT JOIN sitin_records s ON u.id_number = s.id_number AND s.status = 'Completed'
            WHERE u.role = 'student'
            GROUP BY u.id
        """)
    students = cur.fetchall()
    conn.close()
    leaderboard_data = []
    for s in students:
        pts_sitins = min((float(s['total_sitins']) / 30) * 50, 50)
        pts_hours  = min((float(s['total_hours'])  / 100) * 30, 30)
        pts_tasks  = min((float(s['tasks_completed']) / 30) * 20, 20)
        total_pts  = round(pts_sitins + pts_hours + pts_tasks, 2)

        leaderboard_data.append({
            'id_number': s['id_number'], 'firstname': s['firstname'], 'lastname': s['lastname'],
            'course': s['course'], 'profile_pic': s['profile_pic'],
            'total_sitins': s['total_sitins'], 'total_hours': round(s['total_hours'], 1),
            'tasks_completed': s['tasks_completed'],
            'points_sitins': round(pts_sitins, 1), 'points_hours': round(pts_hours, 1),
            'points_tasks': round(pts_tasks, 1), 'total_points': total_pts
        })
    leaderboard_data.sort(key=lambda x: x['total_points'], reverse=True)
    for i, s in enumerate(leaderboard_data):
        s['rank'] = i + 1
    return jsonify(leaderboard_data)


@app.route('/admin_reservations')
def admin_reservations():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT r.*, u.firstname, u.lastname
        FROM reservations r JOIN users u ON r.id_number = u.id_number
        ORDER BY r.id DESC
    """)
    records = cur.fetchall()
    reservations_enabled = get_setting(conn, 'reservations_enabled', 'Enabled')
    feedback_enabled     = get_setting(conn, 'feedback_enabled',     'Enabled')
    conn.close()
    return render_template('admin_reservations.html', records=records,
        reservations_enabled=reservations_enabled, feedback_enabled=feedback_enabled)


@app.route('/admin_feedbacks')
def admin_feedbacks():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM student_feedback ORDER BY date_submitted DESC")
    feedbacks = cur.fetchall()
    reservations_enabled = get_setting(conn, 'reservations_enabled', 'Enabled')
    feedback_enabled     = get_setting(conn, 'feedback_enabled',     'Enabled')
    conn.close()
    return render_template('admin_feedbacks.html', feedbacks=feedbacks,
        reservations_enabled=reservations_enabled, feedback_enabled=feedback_enabled)


@app.route('/admin_award_points', methods=['GET', 'POST'])
def admin_award_points():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    if request.method == 'POST':
        id_number = request.form.get('id_number', '').strip()
        points    = int(request.form.get('points', 0))
        reason    = request.form.get('reason', '').strip()
        category  = request.form.get('category', 'Other').strip()
        formatted_reason = f"[{category}] {reason}"
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(f"SELECT firstname, lastname FROM users WHERE id_number = {PH}", (id_number,))
        student = cur.fetchone()
        student_name = f"{student['firstname']} {student['lastname']}" if student else id_number
        cur.execute(f"""
            INSERT INTO admin_awards (id_number, student_name, points, reason, assigned_by)
            VALUES ({PH},{PH},{PH},{PH},{PH})
        """, (id_number, student_name, points, formatted_reason, session.get('firstname', 'Admin')))
        conn.commit()
        conn.close()
    return redirect(url_for('leaderboard', tab='award'))


@app.route('/admin_manage_tasks', methods=['GET', 'POST'])
def admin_manage_tasks():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    if request.method == 'POST':
        id_number   = request.form.get('id_number', '').strip()
        task_title  = request.form.get('task_title', '').strip()
        description = request.form.get('description', '').strip()
        points      = int(request.form.get('points', 0))
        priority    = request.form.get('priority', 'Medium').strip()
        due_date    = request.form.get('due_date', '').strip()
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(f"SELECT firstname, lastname FROM users WHERE id_number = {PH}", (id_number,))
        student = cur.fetchone()
        student_name = f"{student['firstname']} {student['lastname']}" if student else id_number
        cur.execute(f"""
            INSERT INTO admin_tasks (id_number, student_name, task_title, description, points, assigned_by, priority, due_date, status)
            VALUES ({PH},{PH},{PH},{PH},{PH},{PH},{PH},{PH},'To Do')
        """, (id_number, student_name, task_title, description, points, session.get('firstname', 'Admin'), priority, due_date))
        conn.commit()
        conn.close()
    return redirect(url_for('leaderboard', tab='tasks'))


@app.route('/admin_manage_tasks/<int:task_id>/complete', methods=['POST'])
def admin_complete_task(task_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    conn.cursor().execute(f"UPDATE admin_tasks SET status='Completed' WHERE id={PH}", (task_id,))
    conn.commit(); conn.close()
    return redirect(url_for('leaderboard', tab='tasks'))


@app.route('/admin_manage_tasks/<int:task_id>/update_status', methods=['POST'])
def admin_update_task_status(task_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    if request.is_json:
        data = request.get_json()
        new_status = data.get('status')
    else:
        new_status = request.form.get('status')
        
    if new_status not in ('To Do', 'In Progress', 'Completed'):
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
        
    conn = get_db_connection()
    conn.cursor().execute(f"UPDATE admin_tasks SET status={PH} WHERE id={PH}", (new_status, task_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/admin_manage_tasks/<int:task_id>/delete', methods=['POST'])
def admin_delete_task(task_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    conn.cursor().execute(f"DELETE FROM admin_tasks WHERE id={PH}", (task_id,))
    conn.commit(); conn.close()
    return redirect(url_for('leaderboard', tab='tasks'))


@app.route('/admin_award_points/<int:award_id>/delete', methods=['POST'])
def admin_delete_award(award_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    conn.cursor().execute(f"DELETE FROM admin_awards WHERE id={PH}", (award_id,))
    conn.commit(); conn.close()
    return redirect(url_for('leaderboard', tab='award'))


@app.route('/admin_update_system_settings', methods=['POST'])
def admin_update_system_settings():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    reservations_enabled = request.form.get('reservations_enabled', 'Disabled')
    feedback_enabled     = request.form.get('feedback_enabled',     'Disabled')
    next_page            = request.form.get('next_page', '/admin_dashboard')
    conn = get_db_connection()
    set_setting(conn, 'reservations_enabled', reservations_enabled)
    set_setting(conn, 'feedback_enabled',     feedback_enabled)
    conn.commit(); conn.close()
    return redirect(next_page)


@app.route('/process_reservation/<int:res_id>/<string:action>', methods=['POST'])
def process_reservation(res_id, action):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    if action not in ('approve', 'decline'):
        return redirect(url_for('admin_reservations'))
    status = 'Approved' if action == 'approve' else 'Declined'
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM reservations WHERE id = {PH}", (res_id,))
    res_row = cur.fetchone()
    cur.execute(f"UPDATE reservations SET status={PH} WHERE id={PH}", (status, res_id))
    conn.commit()
    if res_row:
        pc_info = f" ({res_row['selected_pc']})" if res_row['selected_pc'] else ""
        if action == 'approve':
            create_notification(conn, recipient=res_row['id_number'], notif_type='approved',
                message=f"✅ Your reservation for {res_row['res_lab']}{pc_info} on {res_row['res_date']} has been APPROVED!",
                link='/dashboard')
        else:
            create_notification(conn, recipient=res_row['id_number'], notif_type='declined',
                message=f"❌ Your reservation for {res_row['res_lab']}{pc_info} on {res_row['res_date']} was declined.",
                link='/dashboard')
    conn.close()
    return redirect(url_for('admin_reservations'))


@app.route('/ai_recommendation')
def ai_recommendation():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT * FROM users WHERE id = {PH}", (session['user_id'],))
    student = cur.fetchone()
    cur.execute(f"SELECT * FROM sitin_records WHERE id_number = {PH}", (student['id_number'],))
    history      = cur.fetchall()
    total_sitins = len(history)
    conn.close()
    course_tips = "Keep exploring and applying technology to your field."
    if "BSIT" in student['course'].upper() or "IT" in student['course'].upper():
        course_tips = "Focus on your Python and Flask projects. System architecture is a great skill!"
    recommendation = (f"Hello {student['firstname']}! You have {student['remaining_sessions']} sessions left "
                      f"and completed {total_sitins} sit-ins. {course_tips}")
    return jsonify({'name': student['firstname'], 'course': student['course'],
                    'remaining_sessions': student['remaining_sessions'],
                    'total_sitins': total_sitins, 'recommendation': recommendation})


# =======================================================
# NOTIFICATION ROUTES
# =======================================================
@app.route('/notifications/count')
def notifications_count():
    if 'user_id' not in session:
        return jsonify({'count': 0})
    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT COUNT(*) AS cnt FROM notifications WHERE recipient={PH} AND is_read=0", (recipient,))
    row = cur.fetchone()
    conn.close()
    return jsonify({'count': row['cnt'] if row else 0})


@app.route('/notifications/list')
def notifications_list():
    if 'user_id' not in session:
        return jsonify([])
    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT id, type, message, link, is_read, created_at
        FROM notifications WHERE recipient={PH}
        ORDER BY created_at DESC LIMIT 20
    """, (recipient,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/notifications/read/<int:notif_id>', methods=['POST'])
def notification_read(notif_id):
    conn = get_db_connection()
    conn.cursor().execute(f"UPDATE notifications SET is_read=1 WHERE id={PH}", (notif_id,))
    conn.commit(); conn.close()
    return jsonify({'ok': True})


@app.route('/notifications/read_all', methods=['POST'])
def notifications_read_all():
    if 'user_id' not in session:
        return jsonify({'ok': False})
    recipient = 'admin' if session.get('role') == 'admin' else session.get('id_number', '')
    conn = get_db_connection()
    conn.cursor().execute(f"UPDATE notifications SET is_read=1 WHERE recipient={PH}", (recipient,))
    conn.commit(); conn.close()
    return jsonify({'ok': True})


@app.route('/admin_software')
def admin_software():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute("SELECT * FROM lab_software ORDER BY lab ASC, software ASC")
    rows = cur.fetchall()
    conn.close()
    labs_order      = ['Lab 524','Lab 526','Lab 528','Lab 530','Lab 542','Lab 544']
    software_by_lab = {lab: [] for lab in labs_order}
    for row in rows:
        lab = row['lab']
        if lab not in software_by_lab:
            software_by_lab[lab] = []
        software_by_lab[lab].append(dict(row))
    return render_template('admin_software.html', firstname=session.get('firstname', 'Admin'),
                           software_by_lab=software_by_lab, labs_order=labs_order)


@app.route('/add_software', methods=['POST'])
def add_software():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    lab      = request.form.get('lab', '').strip()
    software = request.form.get('software', '').strip()
    if not lab or not software:
        return redirect(url_for('admin_software'))
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT id FROM lab_software WHERE lab={PH} AND LOWER(software)=LOWER({PH})", (lab, software))
    existing = cur.fetchone()
    if not existing:
        ph_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        cur.execute(f"INSERT INTO lab_software (lab, software, added_by, date_added) VALUES ({PH},{PH},{PH},{PH})",
                    (lab, software, session.get('firstname', 'Admin'), ph_time))
        conn.commit()
    conn.close()
    return redirect(url_for('admin_software', added='true'))


@app.route('/delete_software/<int:sw_id>', methods=['POST'])
def delete_software(sw_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('home'))
    conn = get_db_connection()
    conn.cursor().execute(f"DELETE FROM lab_software WHERE id={PH}", (sw_id,))
    conn.commit(); conn.close()
    return redirect(url_for('admin_software', deleted='true'))


@app.route('/get_lab_software')
def get_lab_software():
    lab = request.args.get('lab', '')
    if not lab:
        return jsonify([])
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT software FROM lab_software WHERE lab={PH} ORDER BY software ASC", (lab,))
    rows = cur.fetchall()
    conn.close()
    return jsonify([r['software'] for r in rows])


@app.route('/api/get_lab_pcs')
def get_lab_pcs():
    lab = request.args.get('lab', '')
    if not lab:
        return jsonify([])
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"""
        SELECT pc_number, status, availability, remarks, last_updated
        FROM lab_pcs WHERE lab={PH} ORDER BY pc_number ASC
    """, (lab,))
    pc_rows = cur.fetchall()
    cur.execute(f"SELECT pc_number FROM sitin_records WHERE lab={PH} AND status='Active'", (lab,))
    occupied_set = {r['pc_number'] for r in cur.fetchall()}
    pcs = []
    for r in pc_rows:
        status = r['status']
        if r['availability'] == 'Disabled':
            status = 'Disabled'
        elif status == 'Working' and r['pc_number'] in occupied_set:
            status = 'Occupied'
        pcs.append({'pc_number': r['pc_number'], 'status': status, 'condition': r['status'],
                    'availability': r['availability'], 'remarks': r['remarks'], 'last_updated': str(r['last_updated'])})
    conn.close()
    return jsonify(pcs)


@app.route('/api/update_pc_status', methods=['POST'])
def update_pc_status():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    data         = request.get_json()
    lab          = data.get('lab')
    pc_number    = data.get('pc_number')
    new_status   = data.get('status')
    availability = data.get('availability')
    remarks      = data.get('remarks', '')
    ph_time      = (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    conn.cursor().execute(f"""
        UPDATE lab_pcs SET status={PH}, availability={PH}, remarks={PH}, last_updated={PH}
        WHERE lab={PH} AND pc_number={PH}
    """, (new_status, availability, remarks, ph_time, lab, pc_number))
    conn.commit(); conn.close()
    return jsonify({'success': True})


# =======================================================
# AI CHAT ASSISTANT
# =======================================================
def detect_language(msg):
    bisaya_keywords  = ['unsay','pila','naa','asa','unsaon','nindot','maayong','adlaw','kumusta','karon','balanse']
    tagalog_keywords = ['ano','ilan','meron','nasaan','paano','maganda','magandang','araw','ngayon','bakit']
    msg_low = msg.lower()
    if any(k in msg_low for k in bisaya_keywords):  return 'bisaya'
    if any(k in msg_low for k in tagalog_keywords): return 'tagalog'
    return 'english'


@app.route('/api/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session.get('id_number') or f"user_{session['user_id']}"
    role    = session.get('role', 'student')
    data    = request.get_json()
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    lang    = detect_language(message)
    msg_low = message.lower()

    conn = get_db_connection()
    cur  = conn.cursor()

    responses = {
        'english': {
            'greeting':      "Hello! I am your CCS AI Assistant. How can I help you today?",
            'unknown':       "I'm sorry, I couldn't quite understand that. Please try again or ask about labs, PCs, or your sessions.",
            'datetime':      f"Today is {datetime.now().strftime('%A, %B %d, %Y')}. The current time is {datetime.now().strftime('%I:%M %p')}.",
            'rules':         "SITIN Rules: Bring your ID, maintain silence, no food/drinks, and always 'Time Out' before leaving.",
            'lab_avail':     "In {lab}, there are {avail} PCs available ({occupied} currently occupied).",
            'lab_not_found': "I couldn't find that lab. We have Lab 524, 526, 528, 530, 542, and 544.",
            'total_avail':   "Across all labs, there are {total} available PCs right now.",
            'session_student': "You have {rem} sessions remaining for this semester.",
            'session_admin': "There are currently {active} students actively sitting in.",
            'whoami':        "You are logged in as {name}, a {role}.",
            'pc_status':     "PC {num} in {lab} is currently {status}.{remarks}"
        },
        'tagalog': {
            'greeting':      "Kumusta! Ako ang iyong CCS AI Assistant. May maipaglilingkod ba ako?",
            'unknown':       "Paumanhin, hindi ko masyadong naintindihan. Maaari mo bang ulitin o magtanong tungkol sa lab, PC, o iyong sessions?",
            'datetime':      f"Ngayon ay {datetime.now().strftime('%A, %B %d, %Y')}. Ang oras ay {datetime.now().strftime('%I:%M %p')}.",
            'rules':         "Mga Panuntunan: Magdala ng ID, manahimik, bawal ang pagkain/inumin, at laging mag-'Time Out' bago umalis.",
            'lab_avail':     "Sa {lab}, mayroong {avail} na bakanteng PC ({occupied} ang kasalukuyang ginagamit).",
            'lab_not_found': "Hindi ko mahanap ang lab na iyon. Meron tayong Lab 524, 526, 528, 530, 542, at 544.",
            'total_avail':   "Sa lahat ng lab, mayroong {total} na bakanteng PC ngayon.",
            'session_student': "Mayroon kang {rem} na natitirang sessions para sa semestre.",
            'session_admin': "Mayroong {active} na estudyanteng naka-sit-in sa kasalukuyan.",
            'whoami':        "Ikaw ay naka-login bilang si {name}, isang {role}.",
            'pc_status':     "Ang PC {num} sa {lab} ay {status}.{remarks}"
        },
        'bisaya': {
            'greeting':      "Kumusta! Ako imong CCS AI Assistant. Unsay akong matabang nimo karon?",
            'unknown':       "Pasayloa ko, wala kaayo ko kasabot. Palihug usaba o pangutana bahin sa lab, PC, o imong sessions.",
            'datetime':      f"Karon kay {datetime.now().strftime('%A, %B %d, %Y')}. Ang oras kay {datetime.now().strftime('%I:%M %p')}.",
            'rules':         "Mga Lagda: Dad-a ang ID, hilom lang sa sulod, bawal ang pagkaon/ilimnon, ug ayaw kalimot og 'Time Out'.",
            'lab_avail':     "Sa {lab}, naa pay {avail} ka bakante nga PC ({occupied} ang gigamit karon).",
            'lab_not_found': "Wala nako makit-i ang maong lab. Naa tay Lab 524, 526, 528, 530, 542, ug 544.",
            'total_avail':   "Sa tanang lab, naa pay {total} ka bakante nga PC karon.",
            'session_student': "Naa pay {rem} ka sessions nabilin para nimo karong semestreha.",
            'session_admin': "Naay {active} ka estudyante nga naka-sitin karon.",
            'whoami':        "Naka-login ka isip {name}, usa ka {role}.",
            'pc_status':     "Ang PC {num} sa {lab} kay {status}.{remarks}"
        }
    }

    final_resp = responses[lang]['unknown']

    if any(w in msg_low for w in ['hi','hello','hey','kumusta','mabuhay','maayong']):
        final_resp = responses[lang]['greeting']
    elif any(w in msg_low for w in ['date','time','day','oras','petsa','adlaw','ngayon','karon']):
        final_resp = responses[lang]['datetime']
    elif 'pc' in msg_low and any(c.isdigit() for c in msg_low):
        nums = re.findall(r'\d+', msg_low)
        if nums:
            target_pc = int(nums[0])
            cur.execute(f"SELECT lab, status, remarks FROM lab_pcs WHERE pc_number={PH} LIMIT 1", (target_pc,))
            pc_info = cur.fetchone()
            if pc_info:
                cur.execute(f"SELECT 1 FROM sitin_records WHERE lab={PH} AND pc_number={PH} AND status='Active'",
                            (pc_info['lab'], target_pc))
                is_occ = cur.fetchone()
                status = "Occupied" if is_occ else pc_info['status']
                rem    = f" ({pc_info['remarks']})" if pc_info['remarks'] else ""
                final_resp = responses[lang]['pc_status'].format(num=target_pc, lab=pc_info['lab'], status=status, remarks=rem)
    elif any(w in msg_low for w in ['lab','available','bakante','sulod']):
        lab_match = None
        for l in ['524','526','528','530','542','544']:
            if l in msg_low:
                lab_match = f"Lab {l}"; break
        if lab_match:
            cur.execute(f"SELECT COUNT(*) AS c FROM lab_pcs WHERE lab={PH} AND status='Working' AND availability='Enabled'", (lab_match,))
            working_pcs  = cur.fetchone()['c']
            cur.execute(f"SELECT COUNT(*) AS c FROM sitin_records WHERE lab={PH} AND status='Active'", (lab_match,))
            occupied_pcs = cur.fetchone()['c']
            avail        = max(0, working_pcs - occupied_pcs)
            final_resp   = responses[lang]['lab_avail'].format(lab=lab_match, avail=avail, occupied=occupied_pcs)
        else:
            cur.execute("SELECT COUNT(*) AS c FROM lab_pcs WHERE status='Working' AND availability='Enabled'")
            total_avail  = cur.fetchone()['c']
            cur.execute("SELECT COUNT(*) AS c FROM sitin_records WHERE status='Active'")
            total_active = cur.fetchone()['c']
            final_resp   = responses[lang]['total_avail'].format(total=max(0, total_avail - total_active))
    elif any(w in msg_low for w in ['session','remaining','nabilin','pila','ilan','balance','balanse']):
        if role == 'student':
            cur.execute(f"SELECT remaining_sessions FROM users WHERE id={PH}", (session['user_id'],))
            student    = cur.fetchone()
            final_resp = responses[lang]['session_student'].format(rem=student['remaining_sessions'])
        else:
            cur.execute("SELECT COUNT(*) AS c FROM sitin_records WHERE status='Active'")
            active     = cur.fetchone()['c']
            final_resp = responses[lang]['session_admin'].format(active=active)
    elif any(w in msg_low for w in ['rule','how','unsaon','paano','sitin','lagda']):
        final_resp = responses[lang]['rules']
    elif any(w in msg_low for w in ['who','me','ako','kinsa','sino']):
        cur.execute(f"SELECT firstname, lastname FROM users WHERE id={PH}", (session['user_id'],))
        user       = cur.fetchone()
        final_resp = responses[lang]['whoami'].format(name=f"{user['firstname']} {user['lastname']}", role=role.capitalize())

    cur.execute(f"INSERT INTO chat_messages (user_id, role, message, response) VALUES ({PH},{PH},{PH},{PH})",
                (user_id, role, message, final_resp))
    conn.commit()
    conn.close()
    return jsonify({'message': message, 'response': final_resp})


@app.route('/api/chat/history')
def get_chat_history():
    if 'user_id' not in session:
        return jsonify([])
    user_id = session.get('id_number') or f"user_{session['user_id']}"
    conn = get_db_connection()
    cur  = conn.cursor()
    cur.execute(f"SELECT message, response, created_at FROM chat_messages WHERE user_id={PH} ORDER BY created_at ASC",
                (user_id,))
    rows    = cur.fetchall()
    conn.close()
    history = []
    for r in rows:
        history.append({'type': 'user', 'text': r['message'],  'time': str(r['created_at'])})
        history.append({'type': 'ai',   'text': r['response'], 'time': str(r['created_at'])})
    return jsonify(history)


# =======================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))