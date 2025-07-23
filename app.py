from flask import Flask, render_template, request, redirect, session, send_from_directory
from utils.entity_classifier import classify_entity
from utils.database import (
    create_employee_table,
    create_checklist_table,
    create_file_tracking_table,
    create_users_table,
    create_activity_logs_table,
    create_user_companies_table,
    insert_employee,
    insert_checklist_entry,
    insert_file_tracking_entry,
    add_user,
     insert_user_company,
    get_unique_companies,
    get_all_employees,
    get_checklist_by_employee,
    get_file_tracking_by_employee,
    verify_user,
    get_employee_by_code,
    create_connection,
    insert_activity_log,
    get_user_by_username,
    get_admin_users,
    delete_user,
    get_companies_by_user,
    get_employees_by_companies,
    update_tracking_email_and_return_date,
     get_employee_counts_by_company,
     get_file_counts_by_month,
)
from utils.logger import log_action
from functools import wraps
import qrcode
import os
import csv
import smtplib
from email.message import EmailMessage
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
import re
from datetime import datetime


COMPANY_NAMES = [
    "Aromeo Brands Private Limited",
    "Canara Security Press Limited",
    "Manipal Digital Network Limited",
    "Manipal Energy & Infratech Limited",
    "Manipal Media Network Limited",
    "Manipal Payment and Identity Solutions Limited",
    "Manipal Technologies Limited",
    "QuestPro Consultancy Services Private Limited",
    "Westtek Enterprises Private Limited",
    "Zeta Cyber Solutions Private Limited",
]

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
CHECKLIST_FOLDER = os.path.join(UPLOAD_FOLDER, 'checklists')
os.makedirs(CHECKLIST_FOLDER, exist_ok=True)
PROFILE_FOLDER = os.path.join(UPLOAD_FOLDER, 'profiles')
os.makedirs(PROFILE_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}

# Mapping of locker code ranges to locker groups and numbers
LOCKER_RANGES = [
    ("A1", 40273, 40996, 1),
    ("A2", 41001, 41488, 1),
    ("A3", 41491, 41961, 1),
    ("A4", 41973, 42338, 1),
    ("A5", 42347, 42808, 1),
    ("B1", 42809, 43099, 2),
    ("B2", 43112, 43590, 2),
    ("B3", 43592, 43954, 2),
    ("B4", 43961, 44349, 2),
    ("B5", 44351, 44897, 2),
    ("C1", 44898, 45247, 3),
    ("C2", 45254, 45528, 3),
    ("C3", 45533, 45716, 3),
    ("C4", 45720, 45885, 3),
    ("D2", 45994, 46089, 4),
    ("D3", 46091, 46192, 4),
    ("D4", 46194, 46274, 4),
    ("D5", 61330, 61362, 4),
    ("E1", 30005, 30242, 6),
    ("E2", 30250, 30548, 6),
    ("E3", 30559, 30781, 6),
    ("E4", 30804, 30912, 6),
    ("F1", 26001, 26157, 7),
    ("F2", 26159, 26270, 7),
    ("F4", 86089, 86217, 7),
    ("F5", 84019, 84021, 7),
    ("G1", 10109, 10366, 8),
    ("G2", 28022, 28295, 8),
    ("G3", 28303, 28440, 8),
    ("H1", 20002, 20206, 9),
    ("H2", 20210, 20453, 9),
    ("H3", 20457, 20662, 9),
    ("H4", 20663, 20848, 9),
    ("H5", 15528, 15643, 9),
    ("I1", 55004, 55161, 10),
    ("I2", 55165, 55287, 10),
    ("I3", 55288, 55419, 10),
    ("I4", 55421, 55513, 10),
    ("I5", 55515, 55595, 10),
    ("J1", 55599, 55681, 11),
    ("J2", 55682, 55769, 11),
    ("J3", 55770, 55850, 11),
    ("J4", 55851, 55937, 11),
    ("K1", 55938, 56021, 12),
    ("K2", 56022, 56082, 12),
    ("K3", 56083, 56138, 12),
    ("K4", 56139, 56186, 12),
    ("K5", 56190, 56247, 12),
    ("L1", 56248, 56305, 13),
    ("L2", 56306, 56360, 13),
    ("L3", 56361, 56415, 13),
    ("L4", 56416, 56500, 13),
    ("M1", 56501, 56590, 14),
    ("M2", 56591, 56675, 14),
    ("M3", 56676, 56780, 14),
    ("M4", 56781, 56865, 14),
    ("M5", 56866, 56948, 14),
    ("N1", 56949, 57031, 15),
    ("N2", 57032, 57114, 15),
    ("N3", 57115, 57197, 15),
    ("N4", 57198, 57281, 15),
    ("N5", 58197, 58237, 15),
    ("O1", 24001, 24037, 17),
    ("O2", 85017, 85074, 17),
    ("O3", 87039, 87049, 17),
]

def get_locker_info(code: str):
    """Return locker group and number for the given employee code."""
    try:
        num = int(code)
    except ValueError:
        return None, None
    for grp, start, end, locker in LOCKER_RANGES:
        if start <= num <= end:
            return grp, locker
    return None, None

def allowed_file(filename: str) -> bool:
    """Return True if the file has an allowed extension."""
    ext = os.path.splitext(filename)[1].lower()
    return ext in ALLOWED_EXTENSIONS

create_employee_table()
create_checklist_table()
create_file_tracking_table()
create_users_table()
create_user_companies_table()
create_activity_logs_table()

def send_email(to_address: str, subject: str, body: str):
    """Send an email using SMTP details from environment variables."""
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    username = os.environ.get("SMTP_USERNAME")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("EMAIL_FROM", username)

    if not smtp_server or not username or not password:
        print("SMTP credentials not configured; skipping email send")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_address
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
    except Exception as e:
        print("Error sending email:", e)

def generate_qr(employee_code):
    qr_img = qrcode.make(f"http://192.168.1.142:5000/employee/{employee_code}?next=/employee/{employee_code}")
    qr_path = f"static/qr_codes/{employee_code}.png"
    os.makedirs(os.path.dirname(qr_path), exist_ok=True)
    qr_img.save(qr_path)

def super_admin_required(f):
    """Allow only the super admin user."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_role' not in session:
            return redirect(f"/login?next={request.path}")
        if session.get('user_role') != 'super_admin':
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    """Allow both admin and super admin roles."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_role' not in session:
            return redirect(f"/login?next={request.path}")
        if session.get('user_role') not in ['admin', 'super_admin']:
            return redirect('/unauthorized')
        return f(*args, **kwargs)
    return wrapper

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'user_role' not in session:
            return redirect(f"/login?next={request.path}")
        return f(*args, **kwargs)
    return wrapper

@app.route('/unauthorized')
def unauthorized():
    return "❌ Unauthorized Access", 403

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = None
    next_page = request.args.get('next')
    if request.method == 'POST':
        user = verify_user(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['user_role'] = user[3]
            session['full_name'] = user[4]
            session['company'] = [c.strip() for c in user[5].split(',')] if user[5] else []
            session['mobile_number'] = user[6]
            session['email'] = user[7]
            session['profile_photo'] = user[8]
            log_action(user[1], 'Login', 'User logged in')
            return redirect(next_page or '/employees')
        message = "Invalid credentials"
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    log_action(session.get('username', 'Unknown'), 'Logout', 'User logged out')
    session.clear()
    return redirect('/login')

@app.route('/profile')
@login_required
def my_profile():
    return redirect(f"/profile/{session['username']}")

@app.route('/profile/<string:username>')
@login_required
def view_profile(username):
    if session['username'] != username and session.get('user_role') != 'super_admin':
        return redirect('/unauthorized')
    user = get_user_by_username(username)
    if not user:
        return "User not found", 404
    return render_template('profile.html', user=user)

@app.route('/add_user', methods=['GET', 'POST'])
@super_admin_required
def add_user_route():
    message = None
    companies = get_unique_companies()
    if request.method == 'POST':
        try:
            photo = request.files.get('profile_photo')
            photo_path = None
            if photo and photo.filename:
                ext = os.path.splitext(photo.filename)[1]
                filename = secure_filename(f"{request.form['username']}_{int(datetime.now().timestamp())}{ext}")
                save_path = os.path.join(PROFILE_FOLDER, filename)
                photo.save(save_path)
                photo_path = os.path.join('profiles', filename)

            selected_companies = request.form.getlist('companies')
            company_str = ",".join(selected_companies)

            selected_companies = request.form.getlist('company')
            add_user(
                request.form['username'],
                request.form['password'],
                request.form['role'],
                request.form.get('full_name'),
                ','.join(selected_companies),
                request.form.get('mobile_number'),
                request.form.get('email'),
                photo_path,
            )
            user = get_user_by_username(request.form['username'])
            for comp in selected_companies:
                insert_user_company(user[0], comp)
            log_action(session['username'], 'Add User', f"Added user {request.form['username']}")
            message = "✅ User created successfully"
        except Exception as e:
            message = "❌ Error creating user"
    return render_template('add_user.html', message=message, companies=companies)


@app.route('/manage_admins')
@super_admin_required
def manage_admins():
    admins = []
    for user in get_admin_users():
        companies = ', '.join(get_companies_by_user(user[0]))
        admins.append({
            'id': user[0],
            'full_name': user[2] or user[1],
            'email': user[3],
            'phone': user[4],
            'companies': companies,
        })
    return render_template('manage_admins.html', admins=admins)


@app.route('/delete_admin/<int:user_id>', methods=['POST'])
@super_admin_required
def delete_admin(user_id):
    delete_user(user_id)
    log_action(session['username'], 'Delete User', f'Deleted admin {user_id}')
    return redirect('/manage_admins')

def prepare_checklist_status(employee_id):
    checklist_items = [
        "Appointment Letter", "NDA Declaration", "Passport Photo", "Employment Form",
        "Dependent Details Form", "ESI Declaration", "EPF Declaration",
        "Form 25 Payment of Wages", "Gratuity Nomination", "NFA (Note for Approval)",
        "Interview Assessment", "HR Interview Assessment", "Resume with Declaration",
        "Vaccination Certificate", "Previous Experience Certificates", "SSLC Certificate",
        "PUC Certificate", "Graduation Certificate", "Post Graduation Certificate",
        "PAN Card", "Aadhar Card", "Bank Account Details"
    ]

    submitted = get_checklist_by_employee(employee_id)
    submitted_dict = {item[0]: item for item in submitted}

    return [{
        'document_name': item,
        'is_submitted': submitted_dict[item][1] if item in submitted_dict else 'Missed',
        'verified_by': submitted_dict[item][2] if item in submitted_dict else '-',
        'reviewed_by': submitted_dict[item][3] if item in submitted_dict else '-',
        'verified_date': submitted_dict[item][4] if item in submitted_dict else '-',
        'file_path': submitted_dict[item][5] if item in submitted_dict else None,
        'uploaded_by': submitted_dict[item][6] if item in submitted_dict else None,
        'upload_date': submitted_dict[item][7] if item in submitted_dict else None,
    } for item in checklist_items]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/employees')
@login_required
def list_employees():
    search_query = request.args.get('search', '').strip()
    filter_by = request.args.get('filter', 'employee_code')

    if session.get('user_role') == 'super_admin':
        all_employees = get_all_employees()
    else:
        all_employees = get_employees_by_companies(session.get('company', []))
    if search_query:
        idx_map = {
            'employee_code': 1,
            'name': 2,
            'department': 4,
            'unit': 5,
            'company': 6,
        }
        idx = idx_map.get(filter_by, 1)
        employees = [emp for emp in all_employees if search_query.lower() in (emp[idx] or '').lower()]
    else:
        employees = all_employees

    return render_template(
        'list_employees.html',
        employees=employees,
        search_query=search_query,
        selected_filter=filter_by,
    )

@app.route('/add', methods=['GET', 'POST'])
@admin_required
def add_employee_route():
    if request.method == 'POST':
        data = [request.form[k] for k in ['employee_code', 'name', 'designation', 'department', 'unit',
                                          'epf', 'esi', 'joining_date', 'retirement_date', 'leaving_date', 'uan']]
        detected_entity = classify_entity(data[0])
        insert_employee((*data, detected_entity))
        generate_qr(data[0])
        log_action(session['username'], 'Add Employee', f"Added employee {data[0]}", data[0])
        return redirect('/employees')
    return render_template('add_employee.html')

@app.route('/delete_employee/<string:employee_code>', methods=['POST'])
@admin_required
def delete_employee(employee_code):
    conn = create_connection()
    cursor = conn.cursor()
    log_action(session['username'], 'Delete Employee', f"Deleted employee {employee_code}", employee_code)
    conn.commit()
    conn.close()
    log_action(session['username'], 'Delete Employee', f"Deleted employee {employee_code}", employee_code)
    return redirect('/employees')

@app.route('/add_checklist/<string:employee_code>', methods=['GET', 'POST'])
@admin_required
def add_checklist(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    if request.method == 'POST':
        verified_by = request.form['verified_by']
        reviewed_by = request.form['reviewed_by']
        verified_date = request.form['verified_date']
        for item in request.form.getlist('checklist_items'):
            uploaded = request.files.get(f'file_{item}')
            if not uploaded or uploaded.filename == '':
                return "File required for selected document", 400
            if not allowed_file(uploaded.filename):
                return "Invalid file type", 400
            ext = os.path.splitext(uploaded.filename)[1]
            label = secure_filename(item.replace(' ', '_'))
            filename = secure_filename(f"{employee_code}_{label}_{int(datetime.now().timestamp())}{ext}")
            save_path = os.path.join(CHECKLIST_FOLDER, filename)
            uploaded.save(save_path)
            rel_path = os.path.join('checklists', filename)
            insert_checklist_entry(
                (
                    employee[0],
                    item,
                    "Yes",
                    verified_by,
                    reviewed_by,
                    verified_date,
                    rel_path,
                    session['username'],
                    datetime.now().strftime('%Y-%m-%d'),
                )
            )
        log_action(session['username'], 'Add Checklist', f"Added checklist for {employee_code}", employee_code)
        return redirect('/employees')
    return render_template('add_checklist.html', employee_code=employee_code,
                           checklist_items=prepare_checklist_status(employee[0]))

@app.route('/add_file_tracking/<string:employee_code>', methods=['GET', 'POST'])
@admin_required
def add_file_tracking(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    if request.method == 'POST':
        documents_taken = ",".join(request.form.getlist('documents_taken'))
        insert_file_tracking_entry(
            (
                employee[0],
                request.form['date_taken'],
                request.form['taken_by'],
                request.form.get('taken_by_email'),
                request.form['file_taken_time'],
                request.form['expected_return_date'],
                documents_taken,
                request.form['status_of_documents'],
            )
        )
        log_action(session['username'], 'Add File Tracking', f"Added file tracking for {employee_code}", employee_code)

        # Send confirmation email to the person taking the file
        taken_by_email = request.form.get('taken_by_email')
        if taken_by_email:
            taken_by_name = request.form['taken_by']
            expected_return = request.form['expected_return_date']
            subject = f"File Taken Confirmation for Employee Code {employee_code}"
            body = (
                f"Hi {taken_by_name},\n\n"
                f"This is a confirmation that you have taken the file related to Employee Code: {employee_code}.\n\n"
                f"Please ensure the file is returned before {expected_return}.\n\n"
                "Thank you,\nAdmin Team"
            )
            send_email(taken_by_email, subject, body)

        return redirect('/employees')
    checklist_items = prepare_checklist_status(employee[0])
    return render_template('add_file_tracking.html', employee_code=employee_code, checklist_items=checklist_items)

@app.route('/delete_tracking/<int:record_id>/<string:employee_code>', methods=['POST'])
@admin_required
def delete_tracking(record_id, employee_code):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM file_tracking WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    log_action(session['username'], 'Delete File Tracking', f"Deleted tracking {record_id} for {employee_code}")
    return redirect(f'/view_file_tracking/{employee_code}')


@app.route('/update_tracking/<int:record_id>/<string:employee_code>', methods=['POST'])
@admin_required
def update_tracking(record_id, employee_code):
    """Update email and expected return date for a file tracking record."""
    email = request.form.get('taken_by_email', '').strip()
    expected_date = request.form.get('expected_return_date', '').strip()

    if not email or not expected_date:
        return "❌ Email and Expected Return Date required", 400

    update_tracking_email_and_return_date(record_id, email, expected_date)
    log_action(session['username'], 'Edit File Tracking', f"Updated tracking {record_id} for {employee_code}", employee_code)
    return redirect(f'/view_file_tracking/{employee_code}')

@app.route('/view_checklist/<string:employee_code>')
@login_required
def view_checklist(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    return render_template('view_checklist.html', checklist=prepare_checklist_status(employee[0]),
                           employee_code=employee_code)

@app.route('/view_file_tracking/<string:employee_code>')
@login_required
def view_file_tracking(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    return render_template('view_file_tracking.html', tracking_records=get_file_tracking_by_employee(employee[0]),
                           employee_code=employee_code)

@app.route('/employee/<string:employee_code>')
@login_required
def view_employee_detail(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    return render_template('employee_detail.html', employee=employee,
                           checklist=prepare_checklist_status(employee[0]),
                           tracking_records=get_file_tracking_by_employee(employee[0]))

@app.route('/locker_info/<string:employee_code>')
@login_required
def locker_info(employee_code):
    """Return locker information for an employee as JSON."""
    group, locker = get_locker_info(employee_code)
    if group:
        return {"match": True, "group": group, "locker": locker}
    return {"match": False}

@app.route('/edit_file_tracking/<string:employee_code>', methods=['GET', 'POST'])
@super_admin_required
def edit_file_tracking(employee_code):
    employee = get_employee_by_code(employee_code)
    if not employee: return "❌ Employee not found", 404
    tracking_records = get_file_tracking_by_employee(employee[0])
    if not tracking_records: return "❌ File tracking record not found", 404
    first_record = tracking_records[0]
    if request.method == 'POST':
        conn = create_connection()
        cursor = conn.cursor()
        documents_taken = ",".join(request.form.getlist('documents_taken'))
        cursor.execute(
            '''
            UPDATE file_tracking
            SET date_taken = ?,
                taken_by = ?,
                taken_by_email = ?,
                file_taken_time = ?,
                expected_return_date = ?,
                documents_taken = ?,
                status_of_documents = ?
            WHERE id = ?
        ''', (
                request.form['date_taken'],
                request.form['taken_by'],
                request.form.get('taken_by_email'),
                request.form['file_taken_time'],
                request.form['expected_return_date'],
                documents_taken,
                request.form['status_of_documents'],
                first_record[0]
        ))
        conn.commit()
        conn.close()
        log_action(session['username'], 'Edit File Tracking', f"Edited tracking for {employee_code}", employee_code)
        return redirect(f'/employee/{employee_code}')
    checklist_items = prepare_checklist_status(employee[0])
    return render_template('edit_file_tracking.html', record=first_record, employee=employee, checklist_items=checklist_items)

@app.route('/view_logs')
@admin_required
def view_logs():
    logs = []
    try:
        with open('logs/activity_log.csv', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                logs.append(row)
    except FileNotFoundError:
        pass
    return render_template('view_logs.html', logs=logs)

from io import BytesIO
import base64
from PIL import Image, ImageOps

@app.route('/upload_ocr', methods=['GET', 'POST'])
@admin_required
def upload_ocr():
    message = None
    ocr_text = None

    if request.method == 'POST':
        image = None

        if 'file' in request.files and request.files['file'].filename != '':
            file = request.files['file']
            image = Image.open(file.stream)

        elif 'camera_image' in request.form and request.form['camera_image']:
            image_data = request.form['camera_image'].split(',')[1]
            image = Image.open(BytesIO(base64.b64decode(image_data)))

        if image:
            try:
                # Preprocess image before OCR (using only PIL)
                image = image.convert('L')  # Grayscale
                image = ImageOps.autocontrast(image)  # Auto contrast
                image = image.point(lambda x: 0 if x < 140 else 255, '1')  # Thresholding

                text = pytesseract.image_to_string(image, config='--psm 6')
                ocr_text = text
                match = re.search(r'(\d{4,})', text)
                if match:
                    code = match.group(1)
                    employee = get_employee_by_code(code)
                    if employee:
                        log_action(session['username'], 'OCR Lookup', f"Found employee {code}", code)
                        return redirect(f"/employee/{code}")
                    else:
                        message = f"Employee code {code} not found."
                else:
                    message = "Employee code not detected in the uploaded image."
            except Exception as e:
                message = f"Error processing image: {e}"
        else:
            message = "No image provided."

    return render_template('upload_ocr.html', message=message, ocr_text=ocr_text)

@app.route('/dashboard', methods=['GET', 'POST'])
@admin_required
def dashboard():
    if session.get('user_role') == 'super_admin':
        counts = get_employee_counts_by_company()
        monthly = get_file_counts_by_month()
    else:
        companies = session.get('company', [])
        counts = get_employee_counts_by_company(companies)
        monthly = get_file_counts_by_month(companies)
    labels = [c[0] for c in counts]
    values = [c[1] for c in counts]
    chart_data = {'labels': labels, 'counts': values}

    m_labels = [m[0] for m in monthly]
    m_values = [m[1] for m in monthly]
    line_chart_data = {'labels': m_labels, 'counts': m_values}
    return render_template(
        'dashboard.html',
        company_counts=counts,
        chart_data=chart_data,
        line_chart_data=line_chart_data,
    )


# Serve uploaded checklist files
@app.route('/uploads/<path:filename>')
@admin_required
def uploaded_file(filename):
    """Serve files from the uploads directory."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)