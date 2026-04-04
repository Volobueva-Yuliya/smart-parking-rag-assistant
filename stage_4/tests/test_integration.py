import pytest
import os
from unittest.mock import patch, MagicMock
from stage_4.graph import app

@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    test_db = str(tmp_path / "test_stage_4.db")
    test_file = str(tmp_path / "test_confirmed.txt")
    
    monkeypatch.setenv("DB_NAME", test_db)
    monkeypatch.setenv("CONFIRMED_FILE_PATH", test_file)
    
    import stage_2.db
    import stage_3.app.db_reader
    import stage_3.app.config
    import stage_3.app.file_writer
    import stage_1.scripts.init_db
    
    import importlib
    importlib.reload(stage_2.db)
    importlib.reload(stage_3.app.db_reader)
    importlib.reload(stage_3.app.config)
    importlib.reload(stage_3.app.file_writer)
    importlib.reload(stage_1.scripts.init_db)
    
    yield
    
    if os.path.exists(test_db):
        os.remove(test_db)
    if os.path.exists(test_file):
        os.remove(test_file)

def test_informational_flow():
    """Test that informational queries go through RAG pipeline."""
    # We mock run_rag_pipeline to avoid needing Weaviate/OpenAI in tests
    with patch("stage_4.nodes.run_rag_pipeline") as mock_rag:
        mock_rag.return_value = "Parking is open 24/7."
        
        inputs = {"user_message": "What are the working hours?"}
        result = app.invoke(inputs)
        
        assert result["intent"] == "informational"
        assert result["response"] == "Parking is open 24/7."
        assert result["status"] == "completed"
        mock_rag.assert_called_once()

def test_booking_approved_flow():
    """Test full booking flow with approval and export."""
    # Initialize DB for Stage 1/2
    from stage_1.scripts.init_db import init_db
    from stage_2.db import ensure_stage_2_columns
    init_db()
    ensure_stage_2_columns()
    
    inputs = {
        "user_message": "I want to book a spot",
        "reservation_data": {
            "first_name": "Test",
            "last_name": "User",
            "vehicle_plate": "TEST-444",
            "start_time": "2026-08-01T10:00:00",
            "end_time": "2026-08-01T12:00:00"
        }
    }
    
    result = app.invoke(inputs)
    
    assert result["intent"] == "booking"
    assert result["admin_decision"] == "approved"
    assert "reservation_code" in result
    assert result["reservation_code"].startswith("R-")
    assert "has been approved" in result["response"]
    assert result["status"] == "completed"
    
    # Verify export occurred
    assert result["export_result"]["success"] is True
    
    # Check if file was written
    from stage_3.app.config import CONFIRMED_FILE_PATH
    assert os.path.exists(CONFIRMED_FILE_PATH)
    with open(CONFIRMED_FILE_PATH, "r") as f:
        content = f.read()
        assert "Test User" in content
        assert "TEST-444" in content

def test_booking_rejected_flow():
    """Test booking flow when rejected."""
    from stage_1.scripts.init_db import init_db
    from stage_2.db import ensure_stage_2_columns
    init_db()
    ensure_stage_2_columns()
    
    # Trigger rejection via "reject" in message
    inputs = {
        "user_message": "book and reject",
        "reservation_data": {
            "first_name": "Reject",
            "last_name": "Me",
            "vehicle_plate": "BAD-666",
            "start_time": "2026-08-01T10:00:00",
            "end_time": "2026-08-01T12:00:00"
        }
    }
    
    result = app.invoke(inputs)
    
    assert result["intent"] == "booking"
    assert result["admin_decision"] == "rejected"
    assert "was unfortunately rejected" in result["response"]
    assert result["status"] == "completed"

def test_greeting_flow():
    """Test simple greeting intent."""
    inputs = {"user_message": "Hi"}
    result = app.invoke(inputs)
    
    assert result["intent"] == "greeting"
    assert "Hello" in result["response"]
    assert result["status"] == "completed"

def test_stage_3_failure_handling():
    """Test that Stage 3 failures are handled (mocked)."""
    from stage_1.scripts.init_db import init_db
    from stage_2.db import ensure_stage_2_columns
    init_db()
    ensure_stage_2_columns()
    
    with patch("stage_4.nodes.process_confirmed_reservation") as mock_process:
        mock_process.return_value = {"success": False, "message": "Disk full"}
        
        inputs = {
            "user_message": "book spot",
            "reservation_data": {
                "first_name": "Fail",
                "last_name": "Export",
                "vehicle_plate": "FAIL-000",
                "start_time": "2026-08-01T10:00:00",
                "end_time": "2026-08-01T12:00:00"
            }
        }
        
        result = app.invoke(inputs)
        assert result["admin_decision"] == "approved"
        assert result["export_result"]["success"] is False
        # Final response should reflect that it was approved but NOT mention "recorded in ledger"
        assert "has been approved" in result["response"]
        assert "recorded in our secure ledger" not in result["response"]
