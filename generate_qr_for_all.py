from utils.database import create_connection
from app import generate_qr  # Make sure generate_qr uses next=/employee/ pattern

def generate_qr_for_all_employees():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT employee_code FROM employees')
    employees = cursor.fetchall()

    for emp in employees:
        generate_qr(emp[0])  # ✅ This will generate QR with login?next=/employee/<code>
        print(f"✅ QR generated for {emp[0]}")

    conn.close()

if __name__ == '__main__':
    generate_qr_for_all_employees()
