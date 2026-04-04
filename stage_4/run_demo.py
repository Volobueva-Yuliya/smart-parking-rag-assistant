import sys
from stage_4.graph import app

def run_demo():
    print("--- Stage 4 LangGraph Orchestration Demo ---")
    
    # Example 1: Informational Request
    print("\n[Scenario 1: Informational Request]")
    # Note: RAG requires Weaviate to be running. If it's not, it will return an error message.
    inputs_info = {"user_message": "What are the parking hours?"}
    final_info = app.invoke(inputs_info)
    print("Input:", inputs_info["user_message"])
    print("Final Status:", final_info.get("status"))
    print("Final Response:", final_info.get("response"))
    if final_info.get("export_result"):
        print("Export Result:", final_info.get("export_result"))

    # Example 2: Booking Request (Approved)
    print("\n[Scenario 2: Booking Request - Approved]")
    inputs_booking = {
        "user_message": "I want to reserve a parking space.",
        "reservation_data": {
            "first_name": "Alice",
            "last_name": "Smith",
            "vehicle_plate": "ALICE-100",
            "start_time": "2026-07-01T09:00:00",
            "end_time": "2026-07-01T17:00:00"
        }
    }
    final_booking = app.invoke(inputs_booking)
    print("Input:", inputs_booking["user_message"])
    print("Final Status:", final_booking.get("status"))
    print("Final Response:", final_booking.get("response"))
    if final_booking.get("export_result"):
        print("Export Result:", final_booking.get("export_result"))

    # Example 3: Booking Request (Rejected)
    print("\n[Scenario 3: Booking Request - Rejected]")
    # We simulate rejection by adding "reject" to the message (per our node logic)
    inputs_reject = {
        "user_message": "Please reserve a spot, but reject it.",
        "reservation_data": {
            "first_name": "Bob",
            "last_name": "Jones",
            "vehicle_plate": "BOB-999",
            "start_time": "2026-07-02T10:00:00",
            "end_time": "2026-07-02T12:00:00"
        }
    }
    final_reject = app.invoke(inputs_reject)
    print("Input:", inputs_reject["user_message"])
    print("Final Status:", final_reject.get("status"))
    print("Final Response:", final_reject.get("response"))
    if final_reject.get("export_result"):
        print("Export Result:", final_reject.get("export_result"))

    # Example 4: Greeting
    print("\n[Scenario 4: Greeting]")
    inputs_greet = {"user_message": "Hi there!"}
    final_greet = app.invoke(inputs_greet)
    print("Input:", inputs_greet["user_message"])
    print("Final Status:", final_greet.get("status"))
    print("Final Response:", final_greet.get("response"))

if __name__ == "__main__":
    run_demo()
