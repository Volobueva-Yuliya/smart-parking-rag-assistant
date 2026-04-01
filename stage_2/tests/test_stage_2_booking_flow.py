import os
import pytest
import sqlite3
from stage_2.db import ensure_stage_2_columns
from stage_2.booking_flow import (
    is_booking_data_complete,
    finalize_pending_reservation
)

# Use a dedicated test database
TEST_DB = "test_booking_flow_stage_2.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a clean test database before each test."""
    import stage_2.db
    monkeypatch.setattr(stage_2.db, "DB_NAME", TEST_DB)
    
    # Initialize basic structure
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reservations")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS parking")
    
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT, vehicle_plate TEXT)")
    cursor.execute("CREATE TABLE parking (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, address TEXT, working_hours TEXT, total_slots INTEGER, available_slots INTEGER)")
    cursor.execute('''
        CREATE TABLE reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            parking_id INTEGER,
            reservation_start DATETIME,
            reservation_end DATETIME,
            status TEXT,
            reservation_code TEXT UNIQUE
        )
    ''')
    cursor.execute("INSERT INTO parking (name, address, working_hours, total_slots, available_slots) VALUES (?, ?, ?, ?, ?)",
                   ("Test Parking", "Addr", "24/7", 10, 10))
    conn.commit()
    conn.close()
    
    ensure_stage_2_columns()
    
    yield
    
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_is_booking_data_complete_valid():
    data = {
        "first_name": "Alice",
        "last_name": "Wonder",
        "vehicle_plate": "ALICE-1",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    assert is_booking_data_complete(data) is True

def test_is_booking_data_complete_missing_key():
    data = {
        "first_name": "Alice",
        "last_name": "Wonder",
        "vehicle_plate": "ALICE-1",
        "start_time": "2026-05-01T10:00:00"
        # end_time missing
    }
    assert is_booking_data_complete(data) is False

def test_is_booking_data_complete_empty_string():
    data = {
        "first_name": "Alice",
        "last_name": "",
        "vehicle_plate": "ALICE-1",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    assert is_booking_data_complete(data) is False

def test_is_booking_data_complete_whitespace():
    data = {
        "first_name": "Alice",
        "last_name": "Wonder",
        "vehicle_plate": "   ",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    assert is_booking_data_complete(data) is False

def test_finalize_pending_reservation_success():
    data = {
        "first_name": "Alice",
        "last_name": "Wonder",
        "vehicle_plate": "ALICE-1",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    
    result = finalize_pending_reservation(data)
    
    assert "reservation_code" in result
    assert result["status"] == "pending_admin_approval"
    assert result["admin_submission"]["success"] is True
    assert result["admin_submission"]["channel"] == "stub"
