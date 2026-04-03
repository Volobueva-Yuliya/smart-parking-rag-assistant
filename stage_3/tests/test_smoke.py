import pytest
from fastapi.testclient import TestClient
from stage_3.app.mcp_server import app
from stage_3.app.config import API_TOKEN

client = TestClient(app)

def test_health_check():
    """
    Smoke test for the /health endpoint.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_confirm_reservation_authenticated(tmp_path, monkeypatch):
    """
    Test the /confirm endpoint with valid authentication.
    """
    test_file = tmp_path / "confirmed_reservations.txt"
    monkeypatch.setattr("stage_3.app.file_writer.CONFIRMED_FILE_PATH", str(test_file))

    payload = {
        "reservation_code": "R-123456",
        "first_name": "Lila",
        "last_name": "Ivanova",
        "car_number": "SDS-100",
        "start_time": "2026-04-02T10:00:00",
        "end_time": "2026-04-02T18:00:00",
        "approval_time": "2026-04-02T09:45:10"
    }
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = client.post("/confirm", json=payload, headers=headers)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert "formatted_line" in response.json()
    
    # Verify file content
    with open(test_file, "r") as f:
        content = f.read()
    assert response.json()["formatted_line"] in content

def test_confirm_reservation_unauthorized():
    """
    Test the /confirm endpoint without or with invalid authentication.
    """
    payload = {
        "reservation_code": "R-123456",
        "first_name": "Lila",
        "last_name": "Ivanova",
        "car_number": "SDS-100",
        "start_time": "2026-04-02T10:00:00",
        "end_time": "2026-04-02T18:00:00",
        "approval_time": "2026-04-02T09:45:10"
    }
    
    # Missing header
    response = client.post("/confirm", json=payload)
    assert response.status_code == 401 # FastAPI's HTTPBearer returns 401 if header is missing
    
    # Invalid token
    headers = {"Authorization": "Bearer wrong_token"}
    response = client.post("/confirm", json=payload, headers=headers)
    assert response.status_code == 401

def test_confirm_reservation_invalid_payload():
    """
    Test the /confirm endpoint with an invalid payload.
    Should return 422 Unprocessable Entity.
    """
    payload = {
        "reservation_code": "R-123456",
        # Missing required fields like first_name, last_name, etc.
    }
    
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = client.post("/confirm", json=payload, headers=headers)
    assert response.status_code == 422
