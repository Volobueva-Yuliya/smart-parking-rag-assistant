from stage_3.app.models import ConfirmedReservation
from stage_3.app.file_writer import append_to_file
from stage_3.app.db_reader import read_approved_reservations
from stage_3.app.export_state import load_exported_codes, save_exported_codes

def format_reservation_line(reservation: ConfirmedReservation) -> str:
    """
    Converts a confirmed reservation object into a single text line.
    Required format: Name | Car Number | Reservation Period | Approval Time
    """
    full_name = f"{reservation.first_name} {reservation.last_name}"
    reservation_period = f"{reservation.start_time} to {reservation.end_time}"
    
    # Check if approval_time is string or datetime-like
    if hasattr(reservation.approval_time, 'isoformat'):
        approval_time_str = reservation.approval_time.isoformat()
    else:
        approval_time_str = str(reservation.approval_time)
    
    return f"{full_name} | {reservation.car_number} | {reservation_period} | {approval_time_str}"

def process_confirmed_reservation(reservation: ConfirmedReservation) -> dict:
    """
    Business logic layer for handling confirmed reservations.
    Initializes validation and preparation before persistence.
    """
    # 1. Format reservation line
    formatted_line = format_reservation_line(reservation)
    
    # 2. Append formatted line to file
    success = append_to_file(formatted_line)
    
    return {
        "reservation_code": reservation.reservation_code,
        "success": success,
        "formatted_line": formatted_line,
        "message": "Processed successfully." if success else "Failed to process."
    }

def sync_approved_reservations() -> dict:
    """
    Synchronizes approved reservations from SQLite to the confirmed reservations file.
    Only exports new reservations that have not been processed yet.
    
    Returns:
        dict: Detailed summary of the synchronization process.
    """
    # 1. Load exported codes to avoid duplicates
    exported_codes = load_exported_codes()
    
    # 2. Read all approved reservations from DB
    all_approved = read_approved_reservations()
    
    found_approved_count = len(all_approved)
    already_exported_count = len([res for res in all_approved if res['reservation_code'] in exported_codes])
    
    # 3. Filter only new ones
    new_reservations = [
        res for res in all_approved 
        if res['reservation_code'] not in exported_codes
    ]
    
    if not new_reservations:
        return {
            "success": True,
            "found_approved": found_approved_count,
            "already_exported": already_exported_count,
            "exported_now": 0,
            "exported_codes": [],
            "message": "No new approved reservations to export."
        }
    
    # 4. Process each new reservation
    exported_now_count = 0
    newly_exported_codes_list = []
    
    for res_data in new_reservations:
        try:
            # Create Pydantic model from DB row
            reservation = ConfirmedReservation(**res_data)
            
            # Format and write
            result = process_confirmed_reservation(reservation)
            
            if result["success"]:
                exported_now_count += 1
                newly_exported_codes_list.append(reservation.reservation_code)
        except Exception as e:
            # Skip invalid records but continue the sync
            print(f"Error processing reservation {res_data.get('reservation_code')}: {e}")
            continue
            
    # 5. Update export state
    if newly_exported_codes_list:
        updated_codes = exported_codes.union(set(newly_exported_codes_list))
        save_exported_codes(updated_codes)
        
    return {
        "success": True,
        "found_approved": found_approved_count,
        "already_exported": already_exported_count,
        "exported_now": exported_now_count,
        "exported_codes": newly_exported_codes_list,
        "message": "Sync completed successfully."
    }
