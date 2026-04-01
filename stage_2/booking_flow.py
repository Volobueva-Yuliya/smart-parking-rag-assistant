"""
Module for handling the booking flow in Stage 2.
This module contains logic for validating booking data, building summaries,
and finalizing reservations after user confirmation.
"""

from stage_2.db import create_pending_reservation, get_reservation_by_code
from stage_2.admin_client import submit_reservation_for_approval

def is_booking_data_complete(data: dict) -> bool:
    """
    Checks if all required booking fields are present in the provided data.

    Required fields:
    - first_name
    - last_name
    - vehicle_plate
    - start_time
    - end_time

    Args:
        data (dict): Dictionary containing user-provided booking information.

    Returns:
        bool: True if all required fields are present and have non-empty values, False otherwise.
    """
    required_fields = ["first_name", "last_name", "vehicle_plate", "start_time", "end_time"]
    for field in required_fields:
        value = data.get(field)
        # Check if field exists and value is not empty (None, empty string, etc.)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
    return True

def build_booking_summary(data: dict) -> str:
    """
    Returns a human-readable summary of the booking data for user confirmation.

    Args:
        data (dict): Dictionary containing booking information.

    Returns:
        str: A formatted string summarizing the booking details.
    """
    summary = (
        "Booking Summary:\n"
        f"- Name: {data.get('first_name')} {data.get('last_name')}\n"
        f"- Vehicle Plate: {data.get('vehicle_plate')}\n"
        f"- Start Time: {data.get('start_time')}\n"
        f"- End Time: {data.get('end_time')}\n"
        "\nPlease confirm if these details are correct."
    )
    return summary

def finalize_pending_reservation(data: dict) -> dict:
    """
    Creates a pending reservation in the database and automatically submits it for admin approval.
    This function should only be called after explicit user confirmation.

    The flow is:
    1. Create reservation in DB (status = 'pending_admin_approval').
    2. Retrieve full record by reservation_code.
    3. Submit the record for admin approval via admin_client.
    4. Return a structured result combining reservation details and submission status.

    Args:
        data (dict): Dictionary containing complete booking information.
            Required keys: first_name, last_name, vehicle_plate, start_time, end_time.

    Returns:
        dict: A structured response containing the reservation_code, its status,
              and the result of the admin submission attempt.
    """
    # This function must be called only after explicit user confirmation.
    # Reservation must NOT be created before confirmation.

    # 1. Create the reservation in DB
    _, reservation_code = create_pending_reservation(
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        vehicle_plate=data.get("vehicle_plate"),
        start_time=data.get("start_time"),
        end_time=data.get("end_time")
    )

    # 2. Retrieve the full reservation record by reservation_code
    # This ensures we have all fields including any DB-level defaults or auto-generated values
    full_reservation = get_reservation_by_code(reservation_code)

    # 3. Submit for admin approval
    # We attempt submission to the admin integration layer.
    try:
        admin_submission = submit_reservation_for_approval(full_reservation)
    except Exception as e:
        # If admin submission fails unexpectedly, we do NOT delete the reservation from DB.
        # Instead, we report the failure but keep the reservation record.
        admin_submission = {
            "success": False,
            "channel": "error",
            "message": f"Unexpected error during admin submission: {str(e)}"
        }

    # 4. Return the combined result
    return {
        "reservation_code": reservation_code,
        "status": full_reservation.get("status", "pending_admin_approval"),
        "admin_submission": admin_submission
    }
