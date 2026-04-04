import os
import pytest
from datetime import datetime
from stage_3.app.models import ConfirmedReservation
from stage_3.app.service import format_reservation_line, process_confirmed_reservation
from stage_3.app.file_writer import append_to_file

@pytest.fixture
def sample_reservation():
    return ConfirmedReservation(
        reservation_code="R-TEST-001",
        first_name="Lila",
        last_name="Ivanova",
        car_number="SDS-100",
        start_time="2026-04-02T10:00:00",
        end_time="2026-04-02T18:00:00",
        approval_time=datetime(2026, 4, 2, 9, 45, 10)
    )

def test_format_reservation_line(sample_reservation):
    """Test that reservation line is formatted exactly as required."""
    expected = "Lila Ivanova | SDS-100 | 2026-04-02T10:00:00 to 2026-04-02T18:00:00 | 2026-04-02T09:45:10"
    result = format_reservation_line(sample_reservation)
    assert result == expected

def test_full_name_composition(sample_reservation):
    """Test that full name is composed correctly."""
    result = format_reservation_line(sample_reservation)
    assert "Lila Ivanova |" in result

def test_file_writing_creates_file(tmp_path):
    """Test that writing creates the file automatically."""
    test_file = tmp_path / "test_storage.txt"
    test_line = "Test data line"
    
    # Ensure it doesn't exist yet
    assert not os.path.exists(test_file)
    
    success = append_to_file(test_line, file_path=str(test_file))
    
    assert success is True
    assert os.path.exists(test_file)
    
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == test_line + "\n"

def test_append_multiple_lines(tmp_path):
    """Test that writing appends multiple lines correctly."""
    test_file = tmp_path / "multi_test.txt"
    line1 = "Line 1"
    line2 = "Line 2"
    
    append_to_file(line1, file_path=str(test_file))
    append_to_file(line2, file_path=str(test_file))
    
    with open(test_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    assert len(lines) == 2
    assert lines[0] == line1 + "\n"
    assert lines[1] == line2 + "\n"

def test_process_confirmed_reservation_integration(sample_reservation, tmp_path, monkeypatch):
    """Integration test for service logic with a temporary file."""
    test_file = tmp_path / "integration_storage.txt"
    
    # Monkeypatch CONFIRMED_FILE_PATH in file_writer
    monkeypatch.setattr("stage_3.app.file_writer.CONFIRMED_FILE_PATH", str(test_file))
    
    result = process_confirmed_reservation(sample_reservation)
    
    assert result["success"] is True
    assert "formatted_line" in result
    assert os.path.exists(test_file)
    
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content.strip() == result["formatted_line"]
