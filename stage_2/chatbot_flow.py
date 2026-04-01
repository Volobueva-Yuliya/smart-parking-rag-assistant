"""
Module for handling user-facing chatbot behavior in Stage 2.
This module provides helper functions for booking confirmation, status checks,
and formatting human-readable responses.
"""

from stage_2.booking_flow import is_booking_data_complete, build_booking_summary, finalize_pending_reservation
from stage_2.db import get_reservation_by_code

def handle_booking_confirmation(data: dict) -> dict:
    """
    Handles the complete flow of booking confirmation after user approval.
    
    The flow is:
    1. Validate data completeness.
    2. Build a human-readable summary.
    3. Finalize the pending reservation (DB + Admin notification).
    
    Args:
        data (dict): Dictionary containing all required booking fields.
        
    Returns:
        dict: A structured result including summary, reservation_code, 
              status, and admin_submission result.
              If data is incomplete, returns an error message.
    """
    if not is_booking_data_complete(data):
        return {
            "error": "Incomplete booking data.",
            "message": "Some required information is missing. Please provide all details."
        }
    
    summary = build_booking_summary(data)
    result = finalize_pending_reservation(data)
    
    return {
        "summary": summary,
        "reservation_code": result["reservation_code"],
        "status": result["status"],
        "admin_submission": result["admin_submission"]
    }

def format_pending_response(result: dict) -> str:
    """
    Returns a clean, user-facing message for a successfully submitted 
    pending reservation.
    
    Args:
        result (dict): The dictionary returned by handle_booking_confirmation.
        
    Returns:
        str: A formatted message for the user.
    """
    reservation_code = result.get("reservation_code")
    status = result.get("status", "pending_admin_approval")
    
    response = (
        "Your reservation request has been submitted for admin approval.\n"
        f"Reservation code: {reservation_code}\n"
        f"Current status: {status}."
    )
    
    # If there was an error with admin notification, we can optionally mention it
    admin_submission = result.get("admin_submission", {})
    if not admin_submission.get("success"):
        response += "\n(Note: There was a delay in notifying the administrator, but your request is saved.)"
        
    return response

def handle_status_check(reservation_code: str) -> dict:
    """
    Looks up the status of a reservation by its unique code.
    
    Args:
        reservation_code (str): The reservation code (e.g., R-20260401-001).
        
    Returns:
        dict: A dictionary containing:
              - found (bool)
              - status (str, optional)
              - admin_comment (str, optional)
    """
    reservation = get_reservation_by_code(reservation_code)
    
    if not reservation:
        return {"found": False}
    
    return {
        "found": True,
        "status": reservation.get("status"),
        "admin_comment": reservation.get("admin_comment")
    }

def format_status_response(status_result: dict) -> str:
    """
    Returns a clean, user-facing status message based on the lookup result.
    
    Args:
        status_result (dict): The dictionary returned by handle_status_check.
        
    Returns:
        str: A formatted status message for the user.
    """
    if not status_result.get("found"):
        return "I'm sorry, I couldn't find a reservation with that code. Please check the code and try again."
    
    status = status_result.get("status")
    comment = status_result.get("admin_comment")
    
    if status == "pending_admin_approval":
        return "Your reservation is still awaiting admin approval. Please check back later."
    
    elif status == "approved":
        response = "Great news! Your reservation has been approved."
        if comment:
            response += f"\nAdmin note: {comment}"
        return response
    
    elif status == "rejected":
        response = "I'm sorry, your reservation request was not approved."
        if comment:
            response += f"\nReason: {comment}"
        return response
    
    # Fallback for unexpected statuses
    return f"Your reservation status is: {status}."
