import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Shared DB strategy: by default, we use a single parking.db at the repository root level.
# This ensures that both stage_1 and stage_2 access the same data consistently.
# We resolve the repository root as the parent of the stage_2 directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = str(PROJECT_ROOT / "parking.db")

DB_NAME = os.getenv("DB_NAME", DEFAULT_DB_PATH)

def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    Sets row_factory for name-based field access.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_stage_2_columns():
    """
    Checks for the existence of new Stage 2 fields in the reservations table 
    and adds them if they are missing.
    Ensures backward compatibility with the Stage 1 database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # List of required fields for Stage 2
    # Some of them (id, user_id, reservation_code, status, etc.) might already exist in Stage 1.
    # We add only those that might be missing or are specific to Stage 2.
    
    # Dynamic schema expansion to support Stage 2 reservation lifecycle
    new_columns = [
        ("status", "TEXT NOT NULL DEFAULT 'pending_admin_approval'"), # Ensure column exists (might be renamed or missing)
        ("created_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("updated_at", "DATETIME DEFAULT CURRENT_TIMESTAMP"),
        ("admin_decision_at", "DATETIME"),
        ("admin_comment", "TEXT")
    ]
    
    # Get existing columns from the SQLite system table
    cursor.execute("PRAGMA table_info(reservations)")
    columns = [column[1] for column in cursor.fetchall()]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            # If the column is missing, add it via ALTER TABLE
            # This allows working with an existing database without deleting it.
            try:
                cursor.execute(f"ALTER TABLE reservations ADD COLUMN {col_name} {col_type}")
            except sqlite3.OperationalError:
                # Field might have been added by another process in a multi-threaded environment.
                pass
                
    conn.commit()
    conn.close()

def create_pending_reservation(first_name, last_name, vehicle_plate, start_time, end_time):
    """
    Creates a new reservation with 'pending_admin_approval' status.
    
    First, finds or creates a user in the users table.
    Then, generates a unique reservation code and saves the record in the reservations table.
    
    Args:
        first_name (str): User's first name.
        last_name (str): User's last name.
        vehicle_plate (str): Vehicle license plate.
        start_time (str/datetime): Reservation start time (ISO format).
        end_time (str/datetime): Reservation end time (ISO format).
        
    Returns:
        tuple: (reservation_id, reservation_code)
    """
    ensure_stage_2_columns()
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Find or create user (logic similar to stage_1)
    cursor.execute('''
        SELECT id FROM users 
        WHERE first_name = ? AND last_name = ? AND vehicle_plate = ?
    ''', (first_name, last_name, vehicle_plate))
    row = cursor.fetchone()
    
    if row:
        user_id = row['id']
    else:
        cursor.execute('''
            INSERT INTO users (first_name, last_name, vehicle_plate)
            VALUES (?, ?, ?)
        ''', (first_name, last_name, vehicle_plate))
        user_id = cursor.lastrowid
    
    # 2. Get default parking ID
    cursor.execute("SELECT id FROM parking LIMIT 1")
    parking_row = cursor.fetchone()
    parking_id = parking_row['id'] if parking_row else 1
    
    # 3. Prepare timestamps
    if isinstance(start_time, str):
        start_dt = datetime.fromisoformat(start_time)
    else:
        start_dt = start_time
        
    if isinstance(end_time, str):
        end_dt = datetime.fromisoformat(end_time)
    else:
        end_dt = end_time

    # 4. Generate reservation code (R-YYYYMMDD-XXX)
    date_part = start_dt.strftime("%Y%m%d")
    date_prefix = start_dt.strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE reservation_start LIKE ?",
        (f"{date_prefix}%",)
    )
    count = cursor.fetchone()[0]
    reservation_code = f"R-{date_part}-{count + 1:03d}"
    
    # 5. Create record in reservations table
    # Default status for Stage 2: pending administrative approval.
    # We also explicitly save created_at and updated_at timestamps.
    status = "pending_admin_approval"
    cursor.execute('''
        INSERT INTO reservations (
            user_id, parking_id, reservation_start, reservation_end, 
            status, reservation_code, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
    ''', (
        user_id, parking_id, start_dt.isoformat(), end_dt.isoformat(), 
        status, reservation_code
    ))
    
    reservation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return reservation_id, reservation_code

def get_reservation_by_code(reservation_code):
    """
    Returns reservation data by its unique code.
    Includes user information (first name, last name, vehicle plate).
    
    Args:
        reservation_code (str): Unique reservation code.
        
    Returns:
        dict: Reservation data or None if not found.
    """
    ensure_stage_2_columns()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT r.*, u.first_name, u.last_name, u.vehicle_plate
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        WHERE r.reservation_code = ?
    ''', (reservation_code,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def update_reservation_status(reservation_code, status, comment=None):
    """
    Updates reservation status (approved/rejected) and saves admin decision.
    
    Automatically sets admin_decision_at and updated_at timestamps.
    
    Args:
        reservation_code (str): Unique reservation code.
        status (str): New status ('approved' or 'rejected').
        comment (str, optional): Administrative comment.
        
    Returns:
        bool: True if update successful, False otherwise.
    """
    # Only approval or rejection statuses are allowed
    if status not in ["approved", "rejected"]:
        raise ValueError("Status must be either 'approved' or 'rejected'.")
        
    ensure_stage_2_columns()
    conn = get_connection()
    cursor = conn.cursor()
    
    # Update status, admin comment, and timestamps
    cursor.execute('''
        UPDATE reservations
        SET status = ?, 
            admin_comment = ?, 
            admin_decision_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE reservation_code = ?
    ''', (status, comment, reservation_code))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success
