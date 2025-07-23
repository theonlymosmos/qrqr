import csv
import os
from datetime import datetime
from utils.database import insert_activity_log

LOG_FILE = 'logs/activity_log.csv'

def log_action(user, action, target="", employee_code=None):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, user, action, target, employee_code or ""])