import os
import sqlite3
import pytest
from pathlib import Path
from stage_3.app.service import sync_approved_reservations
from stage_3.app.db_reader import get_db_path
from stage_3.app.export_state import get_state_file_path
from stage_3.app.file_writer import get_confirmed_file_path

# Temporary test paths
TEST_DB = "test_sync_db.db"
TEST_STATE = "test_export_state.json"
TEST_CONFIRMED = "test_confirmed.txt"

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Sets up a clean environment for each test."""
    # Monkeypatch configuration to use test files
    monkeypatch.setenv("DB_NAME", TEST_DB)
    monkeypatch.setenv("EXPORT_STATE_FILE_PATH", TEST_STATE)
    monkeypatch.setenv("CONFIRMED_FILE_PATH", TEST_CONFIRMED)
    
    # Initialize test DB
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT, vehicle_plate TEXT)")
    cursor.execute('''
        CREATE TABLE reservations (
            id INTEGER PRIMARY KEY, 
            user_id INTEGER, 
            parking_id INTEGER, 
            reservation_start TEXT, 
            reservation_end TEXT, 
            status TEXT, 
            reservation_code TEXT,
            admin_decision_at TEXT
        )
    ''')
    
    # Add test user
    cursor.execute("INSERT INTO users (id, first_name, last_name, vehicle_plate) VALUES (1, 'John', 'Doe', 'CAR-123')")
    
    conn.commit()
    conn.close()
    
    yield
    
    # Cleanup
    for f in [TEST_DB, TEST_STATE, TEST_CONFIRMED]:
        if os.path.exists(f):
            os.remove(f)

def test_sync_reads_approved_ignoring_others():
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    # 1. Approved
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end, admin_decision_at)
        VALUES (1, 'approved', 'R-APP-001', '2026-04-02T10:00:00', '2026-04-02T12:00:00', '2026-04-02T09:00:00')
    ''')
    # 2. Pending (should be ignored)
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end)
        VALUES (1, 'pending_admin_approval', 'R-PEN-002', '2026-04-02T13:00:00', '2026-04-02T15:00:00')
    ''')
    # 3. Rejected (should be ignored)
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end, admin_decision_at)
        VALUES (1, 'rejected', 'R-REJ-003', '2026-04-02T16:00:00', '2026-04-02T18:00:00', '2026-04-02T15:30:00')
    ''')
    conn.commit()
    conn.close()
    
    result = sync_approved_reservations()
    assert result["success"] is True
    assert result["exported_now"] == 1
    assert result["found_approved"] == 1
    assert result["already_exported"] == 0
    assert "R-APP-001" in result["exported_codes"]
    
    # Check file content
    with open(TEST_CONFIRMED, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 1
        assert "John Doe | CAR-123 | 2026-04-02T10:00:00 to 2026-04-02T12:00:00 | 2026-04-02T09:00:00" in lines[0]

def test_sync_skips_already_exported():
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end, admin_decision_at)
        VALUES (1, 'approved', 'R-OLD-001', '2026-04-02T10:00:00', '2026-04-02T12:00:00', '2026-04-02T09:00:00')
    ''')
    conn.commit()
    conn.close()
    
    # First sync
    sync_approved_reservations()
    
    # Add another approved reservation
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end, admin_decision_at)
        VALUES (1, 'approved', 'R-NEW-002', '2026-04-02T14:00:00', '2026-04-02T16:00:00', '2026-04-02T13:00:00')
    ''')
    conn.commit()
    conn.close()
    
    # Second sync
    result = sync_approved_reservations()
    assert result["exported_now"] == 1
    assert result["found_approved"] == 2
    assert result["already_exported"] == 1
    assert "R-NEW-002" in result["exported_codes"]
    assert "Sync completed successfully." in result["message"]
    
    # Third sync (repeated - idempotent)
    result_repeat = sync_approved_reservations()
    assert result_repeat["exported_now"] == 0
    assert result_repeat["found_approved"] == 2
    assert result_repeat["already_exported"] == 2
    assert result_repeat["exported_codes"] == []
    assert "No new approved reservations to export." in result_repeat["message"]
    
    # Check file has exactly 2 lines
    with open(TEST_CONFIRMED, 'r') as f:
        lines = f.readlines()
        assert len(lines) == 2
        assert "John Doe" in lines[0]
        assert "R-OLD-001" not in lines[0] # R-OLD-001 is NOT in the formatted line based on stage_3/app/service.py:15
        assert "R-NEW-002" not in lines[1]
        assert "CAR-123" in lines[1]

def test_sync_state_persistence():
    conn = sqlite3.connect(TEST_DB)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reservations (user_id, status, reservation_code, reservation_start, reservation_end, admin_decision_at)
        VALUES (1, 'approved', 'R-PERS-001', '2026-04-02T10:00:00', '2026-04-02T12:00:00', '2026-04-02T09:00:00')
    ''')
    conn.commit()
    conn.close()
    
    sync_approved_reservations()
    
    # Check if state file exists and contains the code
    import json
    with open(TEST_STATE, 'r') as f:
        data = json.load(f)
        assert "R-PERS-001" in data
