import csv
from utils.database import create_connection

def import_file_tracking_from_csv(csv_file):
    conn = create_connection()
    cursor = conn.cursor()

    with open(csv_file, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            emp_code = row['employee_id']  # ✅ match your new header
            date_taken = row['date_taken']
            taken_by = row['taken_by']
            file_taken_time = row['file_taken_time']
            documents_taken = row['documents_taken']
            status_of_documents = row['status_of_documents']
            taken_by_email = row['taken_by_email']
            expected_return_date = row['expected_return_date']

            # ✅ Check if employee exists
            cursor.execute('SELECT id FROM employees WHERE employee_code = ?', (emp_code,))
            employee = cursor.fetchone()

            if employee:
                employee_id = employee[0]
                # ✅ Insert file tracking entry
                cursor.execute('''
                    INSERT INTO file_tracking (
                        employee_id, date_taken, taken_by, file_taken_time, 
                        documents_taken, status_of_documents, taken_by_email, expected_return_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id, date_taken, taken_by, file_taken_time,
                    documents_taken, status_of_documents, taken_by_email, expected_return_date
                ))
            else:
                print(f"❗ Employee with code {emp_code} not found. Skipping entry.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    import_file_tracking_from_csv('records2.csv')
