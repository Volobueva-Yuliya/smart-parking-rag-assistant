import os
import pytest
import sqlite3
import json
from pathlib import Path
from stage_3.app.auth import validate_token
from stage_3.app.db_reader import read_approved_reservations, get_db_path
from stage_3.app.export_state import load_exported_codes, save_exported_codes, mark_as_exported, get_state_file_path
from stage_3.app.config import API_TOKEN
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import HTTPException

# Test files
TEST_DB_MOD = "test_mod_db.db"
TEST_STATE_MOD = "test_mod_state.json"

@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.setenv("DB_NAME", TEST_DB_MOD)
    monkeypatch.setenv("EXPORT_STATE_FILE_PATH", TEST_STATE_MOD)
    yield
    for f in [TEST_DB_MOD, TEST_STATE_MOD]:
        if os.path.exists(f):
            os.remove(f)

# Auth module tests
def test_validate_token_success():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=API_TOKEN)
    assert validate_token(creds) == API_TOKEN

def test_validate_token_failure():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="wrong_token")
    with pytest.raises(HTTPException) as excinfo:
        validate_token(creds)
    assert excinfo.value.status_code == 401

# DB Reader module tests
def test_read_approved_reservations_empty(clean_env):
    conn = sqlite3.connect(TEST_DB_MOD)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, first_name TEXT, last_name TEXT, vehicle_plate TEXT)")
    cursor.execute("CREATE TABLE reservations (user_id INTEGER, status TEXT, reservation_code TEXT, reservation_start TEXT, reservation_end TEXT, admin_decision_at TEXT)")
    conn.commit()
    conn.close()
    
    results = read_approved_reservations()
    assert results == []

def test_read_approved_reservations_data(clean_env):
    conn = sqlite3.connect(TEST_DB_MOD)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER, first_name TEXT, last_name TEXT, vehicle_plate TEXT)")
    cursor.execute("CREATE TABLE reservations (user_id INTEGER, status TEXT, reservation_code TEXT, reservation_start TEXT, reservation_end TEXT, admin_decision_at TEXT)")
    cursor.execute("INSERT INTO users VALUES (1, 'Alice', 'Smith', 'ABC-123')")
    cursor.execute("INSERT INTO reservations VALUES (1, 'approved', 'R-001', 'start', 'end', 'now')")
    cursor.execute("INSERT INTO reservations VALUES (1, 'pending', 'R-002', 'start', 'end', 'now')")
    conn.commit()
    conn.close()
    
    results = read_approved_reservations()
    assert len(results) == 1
    assert results[0]['reservation_code'] == 'R-001'
    assert results[0]['first_name'] == 'Alice'

# Export State module tests
def test_export_state_load_save(clean_env):
    codes = {"R1", "R2"}
    save_exported_codes(codes)
    loaded = load_exported_codes()
    assert loaded == codes

def test_mark_as_exported(clean_env):
    mark_as_exported("R-NEW")
    loaded = load_exported_codes()
    assert "R-NEW" in loaded

def test_export_state_invalid_json(clean_env):
    with open(TEST_STATE_MOD, "w") as f:
        f.write("invalid json")
    # Should not crash, should return empty set
    assert load_exported_codes() == set()
