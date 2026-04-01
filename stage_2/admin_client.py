"""
Module for handling admin integration in Stage 2.
This module provides an abstraction layer for forwarding reservation requests
for administrative review. In its current form, it acts as a stub/mock integration.
"""

def format_admin_request(reservation: dict) -> str:
    """
    Produces a clean, human-readable summary of the reservation for an administrator.

    Args:
        reservation (dict): Dictionary containing all required reservation fields.
            Expected keys: reservation_code, first_name, last_name, 
            vehicle_plate, start_time, end_time, status.

    Returns:
        str: A formatted string for admin review.
    """
    # Support both key formats: stage_2 keys (start_time/end_time) 
    # and stage_1 DB keys (reservation_start/reservation_end)
    start_time = reservation.get('start_time') or reservation.get('reservation_start')
    end_time = reservation.get('end_time') or reservation.get('reservation_end')

    summary = (
        "ADMIN APPROVAL REQUEST\n"
        "----------------------\n"
        f"Reservation Code: {reservation.get('reservation_code')}\n"
        f"User: {reservation.get('first_name')} {reservation.get('last_name')}\n"
        f"Vehicle Plate: {reservation.get('vehicle_plate')}\n"
        f"Start Time: {start_time}\n"
        f"End Time: {end_time}\n"
        f"Current Status: {reservation.get('status')}\n"
        "----------------------"
    )
    return summary

def submit_reservation_for_approval(reservation: dict) -> dict:
    """
    Submits a reservation request for administrative approval.
    Currently implemented as a stub that simulates a successful submission.

    In the future, this function will be replaced with a real integration layer
    (e.g., calling a REST API, sending a message to a queue, or an email service).

    Args:
        reservation (dict): Dictionary containing reservation details to be submitted.

    Returns:
        dict: A structured response indicating the result of the submission.
    """
    # This is a stub/mock integration. 
    # It doesn't call any external systems yet.
    
    # Simulate processing (e.g., formatting for admin logs)
    _ = format_admin_request(reservation)
    
    return {
        "success": True,
        "channel": "stub",
        "message": "Reservation request submitted for admin approval."
    }

# Future Integration Note:
# -------------------------
# The current stub implementation is designed to be easily swappable with a 
# production-ready integration. To transition to a REST-based integration:
# 1. Update submit_reservation_for_approval to use a library like 'requests' or 'httpx'.
# 2. Add configuration for the API endpoint URL and authentication (e.g., API keys).
# 3. Implement error handling for network timeouts or non-200 HTTP responses.
# 4. The function signature and return structure should remain consistent 
#    to avoid breaking the calling code.
