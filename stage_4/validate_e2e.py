import os
import sys
import json
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

from stage_4.graph import app
from stage_1.scripts.init_db import init_db
from stage_2.db import ensure_stage_2_columns

def validate_end_to_end():
    """
    Clears test environment, runs the approved flow, and verifies the export result.
    """
    print("--- Stage 4 End-to-End Validation ---")
    
    # 1. Setup test environment
    test_db = "validation_test.db"
    test_file = "validation_confirmed.txt"
    
    os.environ["DB_NAME"] = test_db
    os.environ["CONFIRMED_FILE_PATH"] = test_file
    
    # Remove existing test files
    if os.path.exists(test_db):
        os.remove(test_db)
    if os.path.exists(test_file):
        os.remove(test_file)
        
    # Re-initialize DB
    init_db()
    ensure_stage_2_columns()
    
    print(f"Environment cleared. Using DB: {test_db}, Export file: {test_file}")

    # 2. Define the approved flow input
    inputs = {
        "user_message": "I want to book a spot for my car",
        "reservation_data": {
            "first_name": "Validation",
            "last_name": "User",
            "vehicle_plate": "VALID-888",
            "start_time": "2026-09-01T10:00:00",
            "end_time": "2026-09-01T12:00:00"
        }
    }

    print(f"\nRunning approved flow for: {inputs['reservation_data']['first_name']} {inputs['reservation_data']['last_name']}")
    
    # 3. Run the graph
    result = app.invoke(inputs)
    
    # 4. Verify results
    status = result.get("status")
    admin_decision = result.get("admin_decision")
    res_code = result.get("reservation_code")
    export_result = result.get("export_result", {})
    
    print(f"Final Status: {status}")
    print(f"Admin Decision: {admin_decision}")
    print(f"Reservation Code: {res_code}")
    print(f"Export Success: {export_result.get('success')}")
    
    # 5. Check if the line was written to the file
    validation_passed = False
    if os.path.exists(test_file):
        with open(test_file, "r") as f:
            lines = f.readlines()
            for line in lines:
                # Removed res_code check as it's no longer in the file line
                if "Validation User" in line and "VALID-888" in line:
                    validation_passed = True
                    print(f"VERIFIED: Reservation found in {test_file}")
                    break
    
    if validation_passed:
        print("End-to-End Validation PASSED")
    else:
        print("End-to-End Validation FAILED")
        sys.exit(1)

    # Cleanup
    if os.path.exists(test_db):
        os.remove(test_db)
    if os.path.exists(test_file):
        os.remove(test_file)

if __name__ == "__main__":
    validate_end_to_end()
