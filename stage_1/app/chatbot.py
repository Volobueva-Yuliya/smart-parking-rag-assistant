import os
import sys
import re
from datetime import datetime
from app.rag_pipeline import run_rag_pipeline
from app.embeddings import get_embedding_model, get_embedding
from app.db import create_user, create_reservation, get_parking, get_reservation_status, get_parking_availability, get_or_create_user
from dotenv import load_dotenv
from app.guardrails import classify_intent

load_dotenv()

# --- Booking State Management ---

class BookingState:
    def __init__(self):
        self.active = False
        self.current_step = "first_name"  # [first_name, last_name, vehicle_plate, reservation_start, reservation_end, confirmation]
        self.booking_data = {}
        self.confirmed = False

    def reset(self):
        self.active = False
        self.current_step = "first_name"
        self.booking_data = {}
        self.confirmed = False

    def to_dict(self):
        return {
            "First Name": self.booking_data.get("first_name"),
            "Last Name": self.booking_data.get("last_name"),
            "Vehicle Plate": self.booking_data.get("vehicle_plate"),
            "Start Time": self.booking_data.get("reservation_start"),
            "End Time": self.booking_data.get("reservation_end")
        }

# --- Utility Functions for Extraction and Validation ---

def extract_fields(text, state: BookingState):
    """
    Structured multi-field extraction for booking fields.
    """
    # 1. Name extraction (e.g., "my name is Anna Ivanova")
    name_match = re.search(r"my name is ([\w-]+)\s+([\w-]+)", text, re.IGNORECASE)
    if name_match:
        state.booking_data["first_name"] = name_match.group(1).capitalize()
        state.booking_data["last_name"] = name_match.group(2).capitalize()

    # 2. Plate extraction (e.g., "plate AA123BB")
    plate_match = re.search(r"plate\s+([A-Z0-9-]{3,})", text, re.IGNORECASE)
    if plate_match:
        state.booking_data["vehicle_plate"] = plate_match.group(1).upper()

    # 3. Start time extraction (e.g., "start time is 2026-04-01T10:00:00")
    start_match = re.search(r"start time is (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
    if start_match:
        state.booking_data["reservation_start"] = start_match.group(1)

    # 4. End time extraction (e.g., "end time is 2026-04-01T14:00:00")
    end_match = re.search(r"end time is (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", text, re.IGNORECASE)
    if end_match:
        state.booking_data["reservation_end"] = end_match.group(1)

def validate_name(name):
    """
    Validate first_name or last_name: letters only, single token, reasonable length.
    """
    if not name or not isinstance(name, str):
        return False, "Name must be a non-empty string."
    if not re.match(r"^[A-Za-zА-Яа-я]+$", name):
        return False, "Name must contain only letters."
    if len(name) < 2 or len(name) > 50:
        return False, "Name length must be between 2 and 50 characters."
    return True, ""

def validate_car_number(plate):
    """
    Validate vehicle plate number: reasonable length and alphanumeric characters.
    """
    if not plate or not isinstance(plate, str):
        return False, "Plate must be a non-empty string."
    # Allowing common plate formats: 3 to 15 alphanumeric characters
    if not re.match(r"^[A-Z0-9-]{3,15}$", plate.upper()):
        return False, "Invalid plate format. Please use 3-15 alphanumeric characters."
    return True, ""

def validate_datetime(dt_str):
    """
    Validate datetime string: ISO format YYYY-MM-DDTHH:MM:SS and not in the past.
    """
    try:
        dt = datetime.fromisoformat(dt_str)
        if dt < datetime.now():
            return False, "Time cannot be in the past."
        return True, ""
    except ValueError:
        return False, "Invalid time format. Please use YYYY-MM-DDTHH:MM:SS."

def validate_times(start_str, end_str):
    """
    Validate that end_time is after start_time.
    """
    try:
        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)
        if start >= end:
            return False, "Start time must be earlier than end time."
        return True, ""
    except ValueError:
        return False, "Invalid time format. Please use YYYY-MM-DDTHH:MM:SS."

# --- Session State ---
class SessionState:
    def __init__(self):
        self.booking_active = False
        self.current_step = "first_name"
        self.booking_data = {}
        self.last_reservation_id = None
        self.last_reservation_code = None
        self.last_first_name = None
        self.last_last_name = None
        self.last_vehicle_plate = None

def start_chatbot():
    """
    Main interactive loop for the terminal-based parking assistant.
    """
    print("=" * 50)
    print("Welcome to the Central Plaza Parking Assistant!")
    print("I can help you with information about our services, pricing, and rules.")
    print("I can also help you book a parking space.")
    print("Type 'exit', 'quit', or 'bye' to end the session.")
    print("=" * 50)

    # Ensure OPENAI_API_KEY is present before starting
    if not os.getenv("OPENAI_API_KEY"):
        print("\nError: OPENAI_API_KEY not found in environment.")
        print("Please set it in your .env file or as an environment variable.")
        return

    # Warm up the embedding model
    print("\nBot: Initializing system, please wait...")
    try:
        get_embedding_model()
        # Test embedding to ensure everything is ready
        get_embedding("warmup")
        print("Bot: System is ready!\n")
    except Exception as e:
        print(f"Bot: Warning - Failed to warm up embedding model: {e}\n")

    booking = BookingState()
    session = SessionState()

    while True:
        try:
            # Get user input
            raw_input = input("You: ")
            user_input = raw_input.strip()
            if not user_input:
                continue
            user_input_lower = user_input.lower()

            # 1. EXIT COMMANDS (High Priority)
            if user_input_lower in {"exit", "quit", "bye"}:
                print("\nBot: Goodbye!")
                break

            # 2. CANCEL / RESET / START OVER (High Priority)
            if user_input_lower in {"cancel", "reset", "start over"}:
                if booking.active:
                    booking.reset()
                    print("Bot: Booking process cancelled. How else can I help you?\n")
                else:
                    print("Bot: System reset. How can I help you?\n")
                continue

            # 3. ACTIVE BOOKING SESSION STEP (Highest Priority)
            if booking.active:
                # Multi-field extraction ONLY if explicitly structured
                extract_fields(user_input, booking)

                # Process current step
                if booking.current_step == "first_name":
                    if "first_name" not in booking.booking_data:
                        # Plain reply fills ONLY current expected field
                        # But we must avoid booking triggers or generic phrases
                        is_valid, error_msg = validate_name(user_input)
                        booking_triggers = {"book", "reserve", "reservation", "parking space", "make reservation", "book parking", "i want to reserve a parking space"}
                        if is_valid and user_input_lower not in booking_triggers:
                            booking.booking_data["first_name"] = user_input.capitalize()
                            booking.current_step = "last_name"
                            print("Bot: Please provide your last name.")
                            continue # DONE WITH THIS INPUT
                        else:
                            # If it's a booking trigger, just ask for the name again without error
                            if user_input_lower not in booking_triggers:
                                print(f"Bot: {error_msg}")
                            print("Bot: Please provide your first name.")
                            continue # DONE WITH THIS INPUT
                    else:
                        booking.current_step = "last_name"

                if booking.current_step == "last_name":
                    if "last_name" not in booking.booking_data:
                        is_valid, error_msg = validate_name(user_input)
                        if is_valid:
                            booking.booking_data["last_name"] = user_input.capitalize()
                            booking.current_step = "vehicle_plate"
                            print("Bot: Please provide your vehicle plate number.")
                        else:
                            print(f"Bot: {error_msg}")
                            print("Bot: Please provide your last name.")
                        continue
                    else:
                        booking.current_step = "vehicle_plate"

                if booking.current_step == "vehicle_plate":
                    if "vehicle_plate" not in booking.booking_data:
                        is_valid, error_msg = validate_car_number(user_input)
                        if is_valid:
                            booking.booking_data["vehicle_plate"] = user_input.upper()
                            booking.current_step = "reservation_start"
                            print("Bot: Please provide the reservation start time (format: YYYY-MM-DDTHH:MM:SS).")
                        else:
                            print(f"Bot: {error_msg}")
                            print("Bot: Please provide your vehicle plate number.")
                        continue
                    else:
                        booking.current_step = "reservation_start"

                if booking.current_step == "reservation_start":
                    if "reservation_start" not in booking.booking_data:
                        is_valid, error_msg = validate_datetime(user_input)
                        if is_valid:
                            booking.booking_data["reservation_start"] = user_input
                            booking.current_step = "reservation_end"
                            print("Bot: Please provide the reservation end time (format: YYYY-MM-DDTHH:MM:SS).")
                        else:
                            print(f"Bot: {error_msg}")
                            print("Bot: Please provide the reservation start time (format: YYYY-MM-DDTHH:MM:SS).")
                        continue
                    else:
                        booking.current_step = "reservation_end"

                if booking.current_step == "reservation_end":
                    if "reservation_end" not in booking.booking_data:
                        is_valid, error_msg = validate_datetime(user_input)
                        if is_valid:
                            # Final validation of entire period
                            start_time = booking.booking_data.get("reservation_start")
                            v_valid, v_msg = validate_times(start_time, user_input)
                            if v_valid:
                                booking.booking_data["reservation_end"] = user_input
                                booking.current_step = "confirmation"
                                # Proceed to summary below in same iteration
                            else:
                                print(f"Bot: {v_msg}")
                                print("Bot: Please provide the reservation end time (format: YYYY-MM-DDTHH:MM:SS).")
                                continue
                        else:
                            print(f"Bot: {error_msg}")
                            print("Bot: Please provide the reservation end time (format: YYYY-MM-DDTHH:MM:SS).")
                            continue
                    else:
                        booking.current_step = "confirmation"

                if booking.current_step == "confirmation":
                    if not booking.confirmed:
                        # If they typed anything else that wasn't "confirm", 
                        # we show summary and wait.
                        if user_input_lower != "confirm":
                            summary = booking.to_dict()
                            print("\nBot: Please review your booking details:")
                            for key, value in summary.items():
                                print(f"  - {key}: {value}")
                            print("\nBot: Type 'confirm' to submit, or 'cancel' to start over.")
                            continue # Wait for confirmation or correction
                        
                        if user_input_lower == "confirm":
                            booking.confirmed = True

                    if booking.confirmed:
                        try:
                            parking = get_parking()
                            if not parking:
                                print("Bot: Sorry, I couldn't find any parking location in the system.")
                                booking.reset()
                                continue
                            
                            user_id = get_or_create_user(
                                booking.booking_data["first_name"], 
                                booking.booking_data["last_name"], 
                                booking.booking_data["vehicle_plate"]
                            )
                            res_id, res_code = create_reservation(
                                user_id=user_id,
                                parking_id=parking['id'],
                                reservation_start=booking.booking_data["reservation_start"],
                                reservation_end=booking.booking_data["reservation_end"],
                                status="pending"
                            )
                            # Update session state
                            session.last_reservation_id = res_id
                            session.last_reservation_code = res_code
                            session.last_first_name = booking.booking_data["first_name"]
                            session.last_last_name = booking.booking_data["last_name"]
                            session.last_vehicle_plate = booking.booking_data["vehicle_plate"]
                            
                            print(f"\nBot: Success! Your reservation request (ID: {res_id}, Code: {res_code}) has been submitted.")
                            print(f"Bot: It is currently 'pending' and awaiting administrator confirmation.\n")
                        except Exception as e:
                            print(f"Bot: I encountered an error while saving your reservation: {e}")
                            print("Bot: Resetting booking state due to failure.")
                        
                        booking.reset()
                        continue
                continue

            # 4. INTENT CLASSIFICATION
            intent = classify_intent(user_input)

            # 4. GREETING (Priority 3)
            if intent == "greeting":
                print("Bot: Hello! I can help you with parking information and reservations.\n")
                continue

            # 5. SENSITIVE REQUESTS (Priority 4) - BLOCKED BEFORE RAG
            if intent == "sensitive":
                print("Bot: I cannot provide personal, internal, or restricted data. I can help with parking information, availability, booking, or your own reservation status.\n")
                continue

            # 6. OUT OF SCOPE (Priority 5)
            if intent == "out_of_scope":
                print("Bot: I can help with parking information and reservations. Please ask a relevant question.\n")
                continue

            # 7. RESERVATION STATUS REQUESTS (Priority 6)
            if intent == "reservation_status":
                code_match = re.search(r"R-\d{8}-\d{3}", user_input, re.IGNORECASE)
                res_code = None
                if code_match:
                    res_code = code_match.group(0).upper()
                elif session.last_reservation_code:
                    res_code = session.last_reservation_code
                
                if res_code:
                    status_info = get_reservation_status(res_code)
                    if status_info:
                        print(f"Bot: Reservation {status_info['reservation_code']} status: {status_info['status']}")
                        print(f"Bot: Start: {status_info['reservation_start']}")
                        print(f"Bot: End: {status_info['reservation_end']}")
                        print(f"Bot: Human validation required: {'Yes' if status_info['requires_human_validation'] else 'No'}\n")
                    else:
                        print(f"Bot: I couldn't find any reservation with code {res_code}.\n")
                else:
                    print("Bot: Please provide your reservation code to check its status.\n")
                continue

            # 8. AVAILABILITY REQUESTS (Priority 7)
            if intent == "availability":
                availability = get_parking_availability()
                if availability:
                    if any(kw in user_input_lower for kw in ["ev", "electric", "charging"]):
                        print(f"Bot: {availability['name']} currently has {availability['ev_slots_available']} available EV slots out of {availability['ev_slots_total']}.")
                    elif any(kw in user_input_lower for kw in ["accessible", "disability", "disabled"]):
                        print(f"Bot: {availability['name']} currently has {availability['accessible_slots_available']} available accessible slots out of {availability['accessible_slots_total']}.")
                    else:
                        print(f"Bot: {availability['name']} currently has {availability['available_slots']} available slots out of {availability['total_slots']}.")
                    
                    print(f"Bot: Address: {availability['address']}")
                    print(f"Bot: Working Hours: {availability['working_hours']}\n")
                else:
                    print("Bot: Sorry, I couldn't retrieve parking availability information at the moment.\n")
                continue

            # 9. BOOKING REQUESTS (Priority 8)
            if intent == "booking":
                booking.reset() # Start clean
                booking.active = True
                
                # Booking reuse logic: EXPLICIT ONLY
                reuse_phrases = ["book again", "same car", "same plate", "use my previous details"]
                if any(phrase in user_input_lower for phrase in reuse_phrases) and session.last_first_name:
                    booking.booking_data["first_name"] = session.last_first_name
                    booking.booking_data["last_name"] = session.last_last_name
                    booking.booking_data["vehicle_plate"] = session.last_vehicle_plate
                    print(f"Bot: I will reuse your last booking details: {booking.booking_data['first_name']} {booking.booking_data['last_name']}, plate {booking.booking_data['vehicle_plate']}.")
                
                print("Bot: I can help you with that. I'll need some information to create your reservation.")
                
                # Check what's missing after potential reuse
                if "first_name" not in booking.booking_data:
                    print("Bot: Please provide your first name.")
                    booking.current_step = "first_name"
                elif "last_name" not in booking.booking_data:
                    print("Bot: Please provide your last name.")
                    booking.current_step = "last_name"
                elif "vehicle_plate" not in booking.booking_data:
                    print("Bot: Please provide your vehicle plate number.")
                    booking.current_step = "vehicle_plate"
                else:
                    print("Bot: Please provide the reservation start time (format: YYYY-MM-DDTHH:MM:SS).")
                    booking.current_step = "reservation_start"
                continue

            # 10. INFORMATIONAL REQUESTS -> RAG (Priority 9)
            if intent == "informational":
                print("Bot: Let me check that for you...")
                answer = run_rag_pipeline(user_input)
                print(f"Bot: {answer}\n")
                continue

            # 11. FALLBACK CLARIFICATION (Priority 10)
            print("Bot: Please ask a question about the parking service or say that you want to reserve a parking space.\n")

        except KeyboardInterrupt:
            print("\n\nBot: Session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Bot: I encountered an unexpected error. (Details: {e})")
            print("Please try again or rephrase your question.\n")

if __name__ == "__main__":
    start_chatbot()
