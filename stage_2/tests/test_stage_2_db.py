import os
import pytest
import sqlite3
from datetime import datetime
from stage_2.db import (
    get_connection,
    ensure_stage_2_columns,
    create_pending_reservation,
    get_reservation_by_code,
    update_reservation_status
)

# Use a dedicated test database
TEST_DB = "test_parking_stage_2.db"

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Sets up a clean test database before each test."""
    # Ensure stage_2.db uses our test database
    import stage_2.db
    monkeypatch.setattr(stage_2.db, "DB_NAME", TEST_DB)
    
    # Initialize basic structure (simulating stage_1 init)
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS reservations")
    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS parking")
    
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            vehicle_plate TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT NOT NULL,
            working_hours TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            ev_slots_total INTEGER NOT NULL DEFAULT 0,
            ev_slots_available INTEGER NOT NULL DEFAULT 0,
            accessible_slots_total INTEGER NOT NULL DEFAULT 0,
            accessible_slots_available INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            parking_id INTEGER NOT NULL,
            reservation_start DATETIME NOT NULL,
            reservation_end DATETIME NOT NULL,
            status TEXT NOT NULL,
            reservation_code TEXT UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (parking_id) REFERENCES parking (id)
        )
    ''')
    
    # Insert default parking
    cursor.execute("INSERT INTO parking (name, address, working_hours, total_slots, available_slots) VALUES (?, ?, ?, ?, ?)",
                   ("Test Parking", "Test Addr", "00-24", 10, 10))
    
    conn.commit()
    conn.close()
    
    # Run stage_2 column expansion
    ensure_stage_2_columns()
    
    yield
    
    # Teardown: remove test database file
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_create_pending_reservation():
    """Test that create_pending_reservation creates a record with correct status."""
    res_id, res_code = create_pending_reservation(
        "John", "Doe", "ABC-123", 
        "2026-05-01T10:00:00", "2026-05-01T12:00:00"
    )
    
    assert res_id is not None
    assert res_code.startswith("R-20260501-")
    
    reservation = get_reservation_by_code(res_code)
    assert reservation["first_name"] == "John"
    assert reservation["status"] == "pending_admin_approval"
    assert "admin_comment" in reservation
    assert "updated_at" in reservation

def test_get_reservation_by_code_not_found():
    """Test get_reservation_by_code with non-existing code."""
    res = get_reservation_by_code("NON-EXISTENT")
    assert res is None

def test_update_reservation_status_approved():
    """Test updating reservation status to approved."""
    _, res_code = create_pending_reservation(
        "Jane", "Smith", "XYZ-789", 
        "2026-05-02T10:00:00", "2026-05-02T12:00:00"
    )
    
    success = update_reservation_status(res_code, "approved", comment="Looks good")
    assert success is True
    
    updated = get_reservation_by_code(res_code)
    assert updated["status"] == "approved"
    assert updated["admin_comment"] == "Looks good"
    assert updated["admin_decision_at"] is not None

def test_update_reservation_status_rejected():
    """Test updating reservation status to rejected."""
    _, res_code = create_pending_reservation(
        "Bob", "Brown", "BOB-001", 
        "2026-05-03T10:00:00", "2026-05-03T12:00:00"
    )
    
    success = update_reservation_status(res_code, "rejected", comment="Full")
    assert success is True
    
    updated = get_reservation_by_code(res_code)
    assert updated["status"] == "rejected"
    assert updated["admin_comment"] == "Full"

def test_update_reservation_status_invalid_value():
    """Test that invalid status raises ValueError."""
    _, res_code = create_pending_reservation(
        "Test", "User", "T-1", 
        "2026-05-04T10:00:00", "2026-05-04T12:00:00"
    )
    
    with pytest.raises(ValueError, match="Status must be either 'approved' or 'rejected'"):
        update_reservation_status(res_code, "pending")

def test_update_reservation_status_non_existing_code():
    """Test that updating non-existing code returns False."""
    success = update_reservation_status("R-99991231-999", "approved")
    assert success is False
