import sqlite3
import csv
import random

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

DEPARTMENTS = [
    "HR",
    "IT",
    "Finance",
    "Logistics",
    "Operations",
    
    "Marketing",
    "Security",
]

DEPT_TO_UNITS = {
    "HR": ["Payroll Unit", "Admin Unit"],
    "IT": ["Network Unit", "Cybersecurity Unit", "Data Entry Unit"],
    "Finance": ["Compliance Unit", "Admin Unit"],
    "Logistics": ["Operations Unit", "Admin Unit"],
    "Operations": ["Operations Unit", "Data Entry Unit"],
    "Marketing": ["Sales Unit", "Data Entry Unit"],
    "Security": ["Cybersecurity Unit", "Admin Unit"],
}

DB_NAME = "employee_records.db"


def ensure_company_column(conn: sqlite3.Connection) -> None:
    """Add company column to the employees table if it doesn't exist."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(employees)")
    columns = [row[1] for row in cur.fetchall()]
    if "company" not in columns:
        cur.execute("ALTER TABLE employees ADD COLUMN company TEXT")
        conn.commit()


def assign_random_details() -> None:
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    ensure_company_column(conn)

    cur.execute("SELECT id FROM employees")
    employees = cur.fetchall()

    for (emp_id,) in employees:
        company = random.choice(COMPANY_NAMES)
        department = random.choice(DEPARTMENTS)
        unit = random.choice(DEPT_TO_UNITS[department])
        cur.execute(
            "UPDATE employees SET company = ?, department = ?, unit = ? WHERE id = ?",
            (company, department, unit, emp_id),
        )

    conn.commit()

    # Export updated table to CSV
    cur.execute("SELECT * FROM employees")
    rows = cur.fetchall()
    headers = [desc[0] for desc in cur.description]
    with open("employees_updated.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    conn.close()


if __name__ == "__main__":
    assign_random_details()