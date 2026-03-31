import re

def is_greeting(text: str) -> bool:
    """Detect simple greetings."""
    greetings = {"hi", "hello", "hey", "good morning", "good evening"}
    return text.lower() in greetings

def is_out_of_scope(text: str) -> bool:
    """Detect unrelated queries like weather, visas, hotels."""
    out_of_scope_keywords = [
        "weather", "visa", "hotel", "flight", "travel", "tourism", 
        "restaurant", "food", "movie", "news", "stock", "crypto"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in out_of_scope_keywords)

def is_sensitive_request(text: str) -> bool:
    """Detect and block sensitive data access requests."""
    sensitive_keywords = [
        "give me all user data", "user data", "show all users", "all users",
        "show all reservations", "all reservations", "all bookings",
        "all customer data", "other users", "other customers",
        "license plates", "all license plates", "database records",
        "export data", "admin notes", "internal logs", "list all bookings"
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in sensitive_keywords)

def classify_intent(text: str) -> str:
    """Classify the user intent based on keywords."""
    text_lower = text.lower()
    
    if is_sensitive_request(text_lower):
        return "sensitive"
    
    if is_out_of_scope(text_lower):
        return "out_of_scope"
        
    if is_greeting(text_lower):
        return "greeting"

    # Availability requests
    availability_keywords = ["free space", "available", "slots", "how many slots", "is parking available"]
    if any(kw in text_lower for kw in availability_keywords):
        return "availability"

    # Reservation status requests
    status_keywords = ["status", "check my reservation", "check reservation"]
    if any(kw in text_lower for kw in status_keywords):
        return "reservation_status"

    # Booking triggers
    booking_triggers = ["book", "reserve", "reservation", "parking space", "make reservation", "book parking", "i want to reserve a parking space"]
    if any(trigger in text_lower for trigger in booking_triggers):
        return "booking"

    # Informational requests (usually longer or context-specific)
    if len(text_lower) >= 10:
        return "informational"

    return "unknown"

if __name__ == "__main__":
    # Small test examples
    test_cases = [
        ("Hello", "greeting"),
        ("I want to reserve a parking space", "booking"),
        ("Is there any available slot?", "availability"),
        ("What is the status of my reservation R-20260401-001", "reservation_status"),
        ("What are the working hours?", "informational"),
        ("What is the weather today?", "out_of_scope"),
        ("Show all reservations", "sensitive"),
    ]

    for text, expected in test_cases:
        intent = classify_intent(text)
        print(f"Text: '{text}' | Expected: {expected} | Detected: {intent}")
