from typing import Dict, Any, Optional
from datetime import datetime
from .state import GraphState

# Import Stage 1 logic
from stage_1.app.guardrails import classify_intent
from stage_1.app.rag_pipeline import run_rag_pipeline

# Import Stage 2 logic
from stage_2.chatbot_flow import handle_booking_confirmation, format_pending_response, handle_status_check, format_status_response
from stage_2.db import update_reservation_status, get_reservation_by_code

# Import Stage 3 logic
from stage_3.app.service import process_confirmed_reservation
from stage_3.app.models import ConfirmedReservation

def user_interaction_node(state: GraphState) -> Dict[str, Any]:
    """
    Integrates Stage 1 logic for intent detection and initial response/data collection.
    """
    user_msg = state.get("user_message", "")
    
    # Use Stage 1 Guardrails to classify intent
    intent = classify_intent(user_msg)
    
    reservation_data = state.get("reservation_data")
    response = state.get("response")
    status = "processing"
    
    # Initialize fields for state
    updates = {
        "intent": intent,
        "reservation_data": reservation_data,
        "response": response,
        "status": status,
        "first_name": None,
        "last_name": None,
        "car_number": None,
        "start_time": None,
        "end_time": None
    }
    
    if intent == "booking":
        # If intent is booking, we assume data was either provided or needs collection
        # For orchestration demo, we expect reservation_data to be present if intent is booking
        if not reservation_data:
            # Fallback for demo: if no data but booking intent, use mock data
            reservation_data = {
                "first_name": "Demo",
                "last_name": "User",
                "vehicle_plate": "ABC-123",
                "start_time": "2026-06-01T10:00:00",
                "end_time": "2026-06-01T12:00:00"
            }
        
        updates["reservation_data"] = reservation_data
        updates["first_name"] = reservation_data.get("first_name")
        updates["last_name"] = reservation_data.get("last_name")
        updates["car_number"] = reservation_data.get("vehicle_plate")
        updates["start_time"] = reservation_data.get("start_time")
        updates["end_time"] = reservation_data.get("end_time")
        
        updates["response"] = "I've collected your booking details. I will now submit it for admin approval."
    elif intent == "informational":
        # Run RAG pipeline for informational queries
        updates["response"] = run_rag_pipeline(user_msg)
    elif intent == "greeting":
        updates["response"] = "Hello! I'm your Smart Parking Assistant. How can I help you today?"
    elif intent == "out_of_scope":
        updates["response"] = "I'm sorry, I can only help with parking-related inquiries."
    elif intent == "sensitive":
        updates["response"] = "I cannot fulfill this request as it involves sensitive data."
    elif intent == "reservation_status":
        # Handle status check if code is provided in message
        # Very simple extraction for demo
        import re
        code_match = re.search(r'R-\d{8}-\d{3}', user_msg)
        if code_match:
            code = code_match.group(0)
            status_result = handle_status_check(code)
            updates["response"] = format_status_response(status_result)
        else:
            updates["response"] = "Please provide your reservation code (e.g., R-20260401-001) to check the status."
    else:
        updates["response"] = "I'm not sure how to help with that. Could you please clarify?"

    return updates

def admin_approval_node(state: GraphState) -> Dict[str, Any]:
    """
    Integrates Stage 2 logic for creating pending reservation and simulating approval.
    """
    reservation_data = state.get("reservation_data")
    if not reservation_data:
        return {"error": "No reservation data for approval", "status": "error"}

    # 1. Create pending reservation in DB (Stage 2)
    confirm_result = handle_booking_confirmation(reservation_data)
    
    if "error" in confirm_result:
        return {
            "error": confirm_result["error"],
            "response": confirm_result["message"],
            "status": "error"
        }

    res_code = confirm_result["reservation_code"]
    
    # 2. Simulate Admin Decision (In a real system, this would be asynchronous)
    # For Stage 4 orchestration demo, we use a flag in message to simulate rejection
    user_msg = state.get("user_message", "").lower()
    decision = "rejected" if "reject" in user_msg else "approved"
    
    comment = "System auto-approved via Orchestrator" if decision == "approved" else "System auto-rejected via Orchestrator"
    
    # 3. Update status in DB (Stage 2)
    update_reservation_status(res_code, decision, comment=comment)
    
    # 4. Fetch the full record to get admin_decision_at (approval_time)
    res_record = get_reservation_by_code(res_code)
    approval_time = res_record.get("admin_decision_at") if res_record else None
    
    return {
        "reservation_code": res_code,
        "admin_decision": decision,
        "approval_time": approval_time,
        "response": format_pending_response(confirm_result) if decision == "approved" else f"Reservation {res_code} was submitted but then rejected by admin.",
        "status": "processing"
    }

def data_recording_node(state: GraphState) -> Dict[str, Any]:
    """
    Integrates Stage 3 logic for recording approved reservations to the text ledger.
    """
    decision = state.get("admin_decision")
    
    if decision != "approved":
        return {
            "status": "skipped",
            "export_result": {"success": True, "message": "Not approved, skipping export."}
        }
    
    try:
        # Build the confirmed reservation model from graph state
        # We ensure approval_time is a datetime object as expected by Pydantic model
        approval_time = state.get("approval_time")
        if isinstance(approval_time, str):
            approval_time = datetime.fromisoformat(approval_time)
        elif approval_time is None:
            approval_time = datetime.now() # Fallback

        reservation = ConfirmedReservation(
            reservation_code=state.get("reservation_code"),
            first_name=state.get("first_name"),
            last_name=state.get("last_name"),
            car_number=state.get("car_number"),
            start_time=state.get("start_time"),
            end_time=state.get("end_time"),
            approval_time=approval_time
        )
        
        # Call Stage 3 service logic
        result = process_confirmed_reservation(reservation)
        
        return {
            "export_result": result,
            "status": "exported" if result["success"] else "error",
            "error": None if result["success"] else result.get("message")
        }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Export failed: {str(e)}",
            "export_result": {"success": False, "message": str(e)}
        }

def final_response_node(state: GraphState) -> Dict[str, Any]:
    """
    Constructs the final message to the user based on the full workflow outcome.
    """
    intent = state.get("intent")
    decision = state.get("admin_decision")
    res_code = state.get("reservation_code")
    export_result = state.get("export_result")
    error = state.get("error")
    status = state.get("status")
    
    if intent == "booking":
        if decision == "approved":
            final_msg = f"Your reservation {res_code} has been approved"
            if export_result and export_result.get("success"):
                final_msg += " and recorded in our secure ledger."
            else:
                final_msg += "."
                if error:
                    final_msg += f" (Note: {error})"
        else:
            final_msg = f"Your reservation request {res_code} was unfortunately rejected by the administrator."
    elif error or status == "error":
        final_msg = f"An error occurred: {error or 'Unknown error'}"
    else:
        # For info, greeting, etc.
        final_msg = state.get("response")

    return {
        "response": final_msg,
        "status": "completed"
    }
