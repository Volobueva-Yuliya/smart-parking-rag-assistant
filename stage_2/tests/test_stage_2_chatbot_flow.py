import os
import pytest
import sqlite3
from stage_2.db import ensure_stage_2_columns, update_reservation_status
from stage_2.chatbot_flow import (
    handle_booking_confirmation,
    format_pending_response,
    handle_status_check,
    format_status_response
)

# Use a dedicated test database
TEST_DB = "test_chatbot_flow_stage_2.db"

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

def test_handle_booking_confirmation():
    data = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "vehicle_plate": "CB-001",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    
    result = handle_booking_confirmation(data)
    
    assert "summary" in result
    assert "reservation_code" in result
    assert result["status"] == "pending_admin_approval"
    assert result["admin_submission"]["success"] is True

def test_format_pending_response():
    result = {
        "reservation_code": "R-12345678-001",
        "status": "pending_admin_approval"
    }
    msg = format_pending_response(result)
    assert "R-12345678-001" in msg
    assert "pending_admin_approval" in msg

def test_handle_status_check_approved():
    data = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "vehicle_plate": "CB-001",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    confirm_result = handle_booking_confirmation(data)
    code = confirm_result["reservation_code"]
    
    update_reservation_status(code, "approved", comment="Confirmed")
    
    status_result = handle_status_check(code)
    assert status_result["found"] is True
    assert status_result["status"] == "approved"
    assert status_result["admin_comment"] == "Confirmed"
    
    msg = format_status_response(status_result)
    assert "approved" in msg
    assert "Confirmed" in msg

def test_handle_status_check_rejected():
    data = {
        "first_name": "Charlie",
        "last_name": "Brown",
        "vehicle_plate": "CB-001",
        "start_time": "2026-05-01T10:00:00",
        "end_time": "2026-05-01T12:00:00"
    }
    confirm_result = handle_booking_confirmation(data)
    code = confirm_result["reservation_code"]
    
    update_reservation_status(code, "rejected", comment="No slots")
    
    status_result = handle_status_check(code)
    assert status_result["found"] is True
    assert status_result["status"] == "rejected"
    assert status_result["admin_comment"] == "No slots"
    
    msg = format_status_response(status_result)
    assert "not approved" in msg.lower()
    assert "No slots" in msg

def test_handle_status_check_not_found():
    status_result = handle_status_check("INVALID-CODE")
    assert status_result["found"] is False
    
    msg = format_status_response(status_result)
    assert "couldn't find" in msg.lower()
