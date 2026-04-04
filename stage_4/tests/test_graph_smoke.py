from stage_4.graph import app

def test_graph_info_flow():
    """
    Smoke test for informational flow.
    """
    inputs = {"user_message": "What are the parking hours?"}
    result = app.invoke(inputs)
    assert result["intent"] == "informational"
    assert result["status"] == "completed"
    assert result["response"]

def test_graph_booking_flow():
    """
    Smoke test for booking flow.
    """
    inputs = {"user_message": "book spot"}
    result = app.invoke(inputs)
    assert result["intent"] == "booking"
    assert result["admin_decision"] == "approved"
    assert result["export_result"]["success"] is True
    assert "has been approved" in result["response"]
    assert result["status"] == "completed"
