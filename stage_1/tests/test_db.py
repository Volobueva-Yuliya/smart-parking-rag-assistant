import os
import sqlite3
import pytest
from stage_1.app.db import get_or_create_user, create_reservation, get_reservation_status, get_parking_availability
from stage_1.scripts.init_db import init_db

@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_parking.db"
    monkeypatch.setenv("DB_NAME", str(db_file))
    init_db()
    return db_file

def test_get_or_create_user():
    user_id = get_or_create_user("John", "Doe", "AA123BB")
    assert isinstance(user_id, int)
    assert user_id > 0
    
    # Reuse user
    user_id_2 = get_or_create_user("John", "Doe", "AA123BB")
    assert user_id == user_id_2
    
    # Different user
    user_id_3 = get_or_create_user("Jane", "Doe", "BB321AA")
    assert isinstance(user_id_3, int)
    assert user_id_3 > 0
    assert user_id_3 != user_id

def test_create_reservation():
    user_id = get_or_create_user("John", "Doe", "AA123BB")
    res_id, res_code = create_reservation(user_id, 1, "2026-05-01T10:00:00", "2026-05-01T12:00:00")
    
    assert res_id is not None
    assert res_code.startswith("R-20260501-")
    
    status = get_reservation_status(res_code)
    assert status['status'] == "pending"

def test_get_parking_availability():
    availability = get_parking_availability()
    assert availability['name'] == "Central Plaza Parking"
    assert availability['total_slots'] == 120
    assert availability['available_slots'] == 120
    assert availability['ev_slots_total'] == 10
