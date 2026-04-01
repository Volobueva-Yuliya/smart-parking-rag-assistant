import os
import sqlite3
from pathlib import Path
from datetime import datetime

# Shared DB strategy: by default, we use a single parking.db at the repository root level.
# This ensures that both stage_1 and stage_2 access the same data consistently.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = str(PROJECT_ROOT / "parking.db")

DB_NAME = os.getenv("DB_NAME", DEFAULT_DB_PATH)

def get_connection():
    """Returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_or_create_user(first_name, last_name, vehicle_plate):
    """
    Finds an existing user by first_name, last_name, and vehicle_plate.
    If not found, creates a new user.
    """
    if not first_name or not last_name or not vehicle_plate:
        raise ValueError("First name, last name, and vehicle plate are required.")

    conn = get_connection()
    cursor = conn.cursor()
    
    # Try to find existing user
    cursor.execute('''
        SELECT id FROM users 
        WHERE first_name = ? AND last_name = ? AND vehicle_plate = ?
    ''', (first_name, last_name, vehicle_plate))
    
    row = cursor.fetchone()
    if row:
        user_id = row['id']
        conn.close()
        return user_id

    # Create new user if not found
    cursor.execute('''
        INSERT INTO users (first_name, last_name, vehicle_plate)
        VALUES (?, ?, ?)
    ''', (first_name, last_name, vehicle_plate))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def create_user(first_name, last_name, vehicle_plate):
    """Creates a new user in the users table."""
    if not first_name or not last_name or not vehicle_plate:
        raise ValueError("First name, last name, and vehicle plate are required.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (first_name, last_name, vehicle_plate)
        VALUES (?, ?, ?)
    ''', (first_name, last_name, vehicle_plate))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id

def get_parking():
    """Returns the details of the default parking location."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parking LIMIT 1")
    parking = cursor.fetchone()
    conn.close()
    return parking

def create_reservation(user_id, parking_id, reservation_start, reservation_end, status="pending"):
    """Creates a new reservation with basic validation."""
    if not user_id or not parking_id or not reservation_start or not reservation_end:
        raise ValueError("User ID, parking ID, start time, and end time are required.")

    # Convert to datetime objects if they are strings
    if isinstance(reservation_start, str):
        start_dt = datetime.fromisoformat(reservation_start)
    else:
        start_dt = reservation_start

    if isinstance(reservation_end, str):
        end_dt = datetime.fromisoformat(reservation_end)
    else:
        end_dt = reservation_end

    if start_dt >= end_dt:
        raise ValueError("Reservation start time must be earlier than end time.")

    conn = get_connection()
    cursor = conn.cursor()

    # Generate reservation code (format: R-YYYYMMDD-XXX, e.g., R-20260410-003)
    date_part = start_dt.strftime("%Y%m%d")
    date_prefix = start_dt.strftime("%Y-%m-%d")

    cursor.execute(
        "SELECT COUNT(*) FROM reservations WHERE reservation_start LIKE ?",
        (f"{date_prefix}%",)
    )
    count = cursor.fetchone()[0]
    reservation_code = f"R-{date_part}-{count + 1:03d}"

    cursor.execute('''
        INSERT INTO reservations (user_id, parking_id, reservation_start, reservation_end, status, reservation_code)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, parking_id, start_dt.isoformat(), end_dt.isoformat(), status, reservation_code))
    reservation_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reservation_id, reservation_code

def list_reservations():
    """Lists all reservations with user and parking information."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT r.*, u.first_name, u.last_name, p.name as parking_name
        FROM reservations r
        JOIN users u ON r.user_id = u.id
        JOIN parking p ON r.parking_id = p.id
    ''')
    reservations = cursor.fetchall()
    conn.close()
    return reservations

def get_reservation_status(id_or_code):
    """Returns reservation status and details by ID or code."""
    conn = get_connection()
    cursor = conn.cursor()
    if isinstance(id_or_code, int) or (isinstance(id_or_code, str) and id_or_code.isdigit()):
        cursor.execute("SELECT * FROM reservations WHERE id = ?", (id_or_code,))
    else:
        cursor.execute("SELECT * FROM reservations WHERE reservation_code = ?", (id_or_code,))
    reservation = cursor.fetchone()
    conn.close()
    return dict(reservation) if reservation else None

def get_parking_availability():
    """Returns the details of the default parking location and its availability."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, total_slots, available_slots, ev_slots_total, ev_slots_available, accessible_slots_total, accessible_slots_available, address, working_hours FROM parking LIMIT 1")
    parking = cursor.fetchone()
    conn.close()
    return dict(parking) if parking else None
