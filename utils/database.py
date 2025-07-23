import sqlite3
import hashlib

DB_NAME = "employee_records.db"

def create_connection():
    return sqlite3.connect(DB_NAME)

# ------------------ Table Creation ------------------ #
def create_employee_table():
    with create_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT NOT NULL,
                name TEXT NOT NULL,
                designation TEXT NOT NULL,
                department TEXT NOT NULL,
                unit TEXT NOT NULL,
                epf TEXT NOT NULL,
                esi TEXT NOT NULL,
                joining_date TEXT NOT NULL,
                retirement_date TEXT NOT NULL,
                leaving_date TEXT NOT NULL,
                uan TEXT NOT NULL,
                detected_entity TEXT NOT NULL
            );
        """)

def create_checklist_table():
    """Create checklist table and ensure new file columns exist."""
    with create_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                document_name TEXT NOT NULL,
                is_submitted TEXT NOT NULL,
                verified_by TEXT,
                reviewed_by TEXT,
                verified_date TEXT,
                file_path TEXT,
                uploaded_by TEXT,
                upload_date TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            """
        )
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(checklist)")
        cols = [c[1] for c in cur.fetchall()]
        if 'file_path' not in cols:
            cur.execute("ALTER TABLE checklist ADD COLUMN file_path TEXT")
        if 'uploaded_by' not in cols:
            cur.execute("ALTER TABLE checklist ADD COLUMN uploaded_by TEXT")
        if 'upload_date' not in cols:
            cur.execute("ALTER TABLE checklist ADD COLUMN upload_date TEXT")

def create_file_tracking_table():
    """Create file_tracking table and add optional columns if needed."""
    with create_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS file_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date_taken TEXT NOT NULL,
                taken_by TEXT NOT NULL,
                taken_by_email TEXT,
                file_taken_time TEXT NOT NULL,
                expected_return_date TEXT,
                documents_taken TEXT NOT NULL,
                status_of_documents TEXT NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            );
            """
        )
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(file_tracking)")
        cols = [c[1] for c in cur.fetchall()]
        if "taken_by_email" not in cols:
            cur.execute("ALTER TABLE file_tracking ADD COLUMN taken_by_email TEXT")
        if "expected_return_date" not in cols:
            cur.execute(
                "ALTER TABLE file_tracking ADD COLUMN expected_return_date TEXT"
            )

def create_users_table():
    with create_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                full_name TEXT,
                company TEXT,
                mobile_number TEXT,
                email TEXT,
                profile_photo TEXT
            );
        """)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cur.fetchall()]
        optional_cols = ['full_name', 'company', 'mobile_number', 'email', 'profile_photo']
        for col in optional_cols:
            if col not in cols:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col} TEXT")
        cur.execute("SELECT COUNT(*) FROM users WHERE role = 'super_admin'")
        if cur.fetchone()[0] == 0:
            password_hash = hashlib.sha256('SuperAdmin123'.encode()).hexdigest()
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ('superadmin', password_hash, 'super_admin')
            )
            conn.commit()

def create_user_companies_table():
    with create_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_companies (
                user_id INTEGER NOT NULL,
                company TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

def create_activity_logs_table():
    with create_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                target_name TEXT,
                employee_code TEXT,
                performed_by TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            """
        )

# ------------------ Insert Data ------------------ #
def insert_employee(data):
    with create_connection() as conn:
        conn.execute("""
            INSERT INTO employees (
                employee_code, name, designation, department, unit,
                epf, esi, joining_date, retirement_date, leaving_date, uan, detected_entity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, data)

def insert_checklist_entry(data):
    """Insert a checklist record including optional file info."""
    with create_connection() as conn:
        conn.execute(
            """
            INSERT INTO checklist (
                employee_id,
                document_name,
                is_submitted,
                verified_by,
                reviewed_by,
                verified_date,
                file_path,
                uploaded_by,
                upload_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            data,
        )

def insert_file_tracking_entry(data):
    """Insert a file tracking record including optional email and return date."""
    with create_connection() as conn:
        conn.execute(
            """
            INSERT INTO file_tracking (
                employee_id,
                date_taken,
                taken_by,
                taken_by_email,
               file_taken_time,
                expected_return_date,
                documents_taken,
                status_of_documents
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            data,
        )


def insert_activity_log(action_type, target_name, employee_code, performed_by, timestamp):
    with create_connection() as conn:
        conn.execute(
            """
            INSERT INTO activity_logs (action_type, target_name, employee_code, performed_by, timestamp)
            VALUES (?, ?, ?, ?, ?);
            """,
            (action_type, target_name, employee_code, performed_by, timestamp),
        )


# ------------------ Retrieve Data ------------------ #
def get_all_employees():
    with create_connection() as conn:
        return conn.execute(
            "SELECT id, employee_code, name, designation, department, unit, company FROM employees;"
        ).fetchall()

def get_employees_by_companies(companies):
    """Return employees whose company is in the provided list."""
    if not companies:
        return []
    placeholders = ','.join('?' for _ in companies)
    query = f"SELECT id, employee_code, name, designation, department, unit, company FROM employees WHERE company IN ({placeholders});"
    with create_connection() as conn:
        return conn.execute(query, companies).fetchall()

def get_checklist_by_employee(employee_id):
    with create_connection() as conn:
        return conn.execute(
            """
            SELECT
                document_name,
                is_submitted,
                verified_by,
                reviewed_by,
                verified_date,
                file_path,
                uploaded_by,
                upload_date
            FROM checklist
            WHERE employee_id = ?;
            """,
            (employee_id,),
        ).fetchall()

def get_file_tracking_by_employee(employee_id):
    """Return file tracking records for the given employee."""
    with create_connection() as conn:
        return conn.execute(
            """
            SELECT
                id,
                date_taken,
                taken_by,
                taken_by_email,
                file_taken_time,
                expected_return_date,
                documents_taken,
                status_of_documents
            FROM file_tracking
            WHERE employee_id = ?;
            """,
            (employee_id,),
        ).fetchall()

def get_employee_by_id(employee_id):
    with create_connection() as conn:
        return conn.execute("""
            SELECT * FROM employees WHERE id = ?;
        """, (employee_id,)).fetchone()

def get_employee_by_code(employee_code):
    with create_connection() as conn:
        return conn.execute("""
            SELECT * FROM employees WHERE employee_code = ?;
        """, (employee_code,)).fetchone()


def get_unique_companies():
    with create_connection() as conn:
        rows = conn.execute(
            "SELECT DISTINCT company FROM employees WHERE company IS NOT NULL AND company != ''"
        ).fetchall()
        return [row[0] for row in rows]

def insert_user_company(user_id, company):
    with create_connection() as conn:
        conn.execute(
            "INSERT INTO user_companies (user_id, company) VALUES (?, ?);",
            (user_id, company),
        )

def get_companies_by_user(user_id):
    with create_connection() as conn:
        rows = conn.execute(
            "SELECT company FROM user_companies WHERE user_id = ?;",
            (user_id,),
        ).fetchall()
        return [row[0] for row in rows]

def get_employee_counts_by_company(companies=None):
    """Return a list of (company, employee_count)."""
    with create_connection() as conn:
        if companies:
            placeholders = ','.join('?' for _ in companies)
            query = (
                f"SELECT company, COUNT(*) FROM employees "
                f"WHERE company IN ({placeholders}) GROUP BY company;"
            )
            rows = conn.execute(query, companies).fetchall()
        else:
            rows = conn.execute(
                "SELECT company, COUNT(*) FROM employees GROUP BY company;"
            ).fetchall()
    return rows
def get_file_counts_by_month(companies=None):
    """Return list of (YYYY-MM, file_count) for file tracking records."""
    with create_connection() as conn:
        base = """
            SELECT
                CASE
                    WHEN ft.date_taken LIKE '%/%/%' THEN
                        strftime('%Y-%m', printf('%s-%02d-%02d',
                            substr(ft.date_taken, -4),
                            CAST(substr(ft.date_taken, 1, instr(ft.date_taken, '/') - 1) AS INT),
                            CAST(substr(ft.date_taken, instr(ft.date_taken, '/') + 1,
                                         instr(substr(ft.date_taken, instr(ft.date_taken, '/') + 1), '/') - 1) AS INT)
                        ))
                    WHEN ft.date_taken LIKE '____-__-__' THEN substr(ft.date_taken, 1, 7)
                END AS month
            FROM file_tracking ft
        """
        params = []
        if companies:
            placeholders = ','.join('?' for _ in companies)
            base += f" JOIN employees e ON ft.employee_id = e.id WHERE e.company IN ({placeholders})"
            params = companies
        query = f"SELECT month, COUNT(*) FROM ({base}) WHERE month IS NOT NULL GROUP BY month ORDER BY month;"
        rows = conn.execute(query, params).fetchall()
    return rows

# ------------------ Users ------------------ #
def add_user(username, password, role, full_name=None, company=None, mobile_number=None, email=None, profile_photo=None):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    try:
        with create_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, full_name, company, mobile_number, email, profile_photo)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (username, password_hash, role, full_name, company, mobile_number, email, profile_photo),
            )
    except Exception as e:
        print("User creation error:", e)

def verify_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    with create_connection() as conn:
        return conn.execute("""
            SELECT * FROM users WHERE username = ? AND password_hash = ?;
        """, (username, password_hash)).fetchone()

def get_user_by_username(username):
    with create_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE username = ?;",
            (username,)
        ).fetchone()


# ------------------ Update ------------------ #
def update_file_tracking_status(record_id, new_status):
    with create_connection() as conn:
        conn.execute("""
            UPDATE file_tracking
            SET status_of_documents = ?
            WHERE id = ?;
        """, (new_status, record_id))


def update_file_tracking_entry(
    record_id,
    date_taken,
    taken_by,
    taken_by_email,
    file_taken_time,
    expected_return_date,
    documents_taken,
    status_of_documents,
):
     with create_connection() as conn:
        conn.execute(
            """
            UPDATE file_tracking
            SET date_taken = ?,
                taken_by = ?,
                taken_by_email = ?,
                file_taken_time = ?,
                expected_return_date = ?,
                documents_taken = ?,
                status_of_documents = ?
         WHERE id = ?;
        """,
            (
                date_taken,
                taken_by,
                taken_by_email,
                file_taken_time,
                expected_return_date,
                documents_taken,
                status_of_documents,
                record_id,
            ),
              )


def update_tracking_email_and_return_date(record_id, email, expected_return_date):
    """Update email and expected return date for a file tracking record."""
    with create_connection() as conn:
           conn.execute(
            """
            UPDATE file_tracking
            SET taken_by_email = ?,
                expected_return_date = ?
            WHERE id = ?;
            """,
            (email, expected_return_date, record_id),
        )


def get_admin_users():
    """Return all users with role 'admin'."""
    with create_connection() as conn:
        return conn.execute(
            "SELECT id, username, full_name, email, mobile_number FROM users WHERE role = 'admin';"
        ).fetchall()


def delete_user(user_id: int):
    """Delete a user and associated company mappings."""
    with create_connection() as conn:
        conn.execute("DELETE FROM user_companies WHERE user_id = ?;", (user_id,))
        conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        conn.commit()