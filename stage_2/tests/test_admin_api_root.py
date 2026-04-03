import pytest
from fastapi.testclient import TestClient
from stage_2.admin_api import app

client = TestClient(app)

def test_root_endpoint():
    """
    Test that the root endpoint returns 200 OK and contains expected HTML content.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Stage 2 Admin API" in response.text
    assert "/docs" in response.text
    assert "Service Status" in response.text

def test_docs_redirect_hint():
    """
    Check that the response helps discover /docs.
    """
    response = client.get("/")
    assert "Interactive API Documentation" in response.text
    assert 'href="/docs"' in response.text

def test_existing_endpoint_still_works():
    """
    Verify that existing endpoints are not broken.
    Expected to return 404 for a non-existent reservation, not 500 or 404 on the route itself.
    """
    response = client.get("/admin/reservation/NON_EXISTENT_CODE")
    assert response.status_code == 404
    assert "Reservation NON_EXISTENT_CODE not found" in response.json()["detail"]
