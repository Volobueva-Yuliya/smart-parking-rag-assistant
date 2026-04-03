import sqlite3
import os
from pathlib import Path

# Use the shared parking.db at the repository root
# This follows the same strategy as Stage 1 and Stage 2
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# We use a lambda or a property-like approach to allow env var changes during tests
def get_db_path():
    return os.getenv("DB_NAME", str(PROJECT_ROOT / "parking.db"))

def get_connection():
    """Returns a connection to the shared SQLite database."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def read_approved_reservations():
    """
    Reads all reservations with status 'approved' from the shared database.
    Joins with the users table to get required user details.
    
    Returns:
        list[dict]: A list of approved reservation records.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # We select all necessary fields for Stage 3 export
    cursor.execute('''
        SELECT 
            r.reservation_code,
            u.first_name,
            u.last_name,
            u.vehicle_plate as car_number,
            r.reservation_start as start_time,
            r.reservation_end as end_time,
            r.admin_decision_at as approval_time
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE r.status = 'approved'
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]
