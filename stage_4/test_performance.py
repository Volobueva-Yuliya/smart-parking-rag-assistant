import time
import os
import sys
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd() + "/smart-parking-rag-assistent")

from stage_4.graph import app
from stage_1.scripts.init_db import init_db
from stage_2.db import ensure_stage_2_columns

def run_performance_test():
    print("--- Stage 4 Performance Validation ---")
    
    # Setup test environment
    test_db = "perf_test.db"
    test_file = "perf_confirmed.txt"
    os.environ["DB_NAME"] = test_db
    os.environ["CONFIRMED_FILE_PATH"] = test_file
    
    if os.path.exists(test_db): os.remove(test_db)
    if os.path.exists(test_file): os.remove(test_file)
    
    init_db()
    ensure_stage_2_columns()
    
    scenarios = [
        ("Informational", {"user_message": "What are the parking hours?"}),
        ("Booking (Approved)", {
            "user_message": "I want to book",
            "reservation_data": {
                "first_name": "Perf", "last_name": "User", "vehicle_plate": "PERF-123",
                "start_time": "2026-06-01T10:00:00", "end_time": "2026-06-01T12:00:00"
            }
        }),
        ("Greeting", {"user_message": "Hello"})
    ]
    
    iterations = 5
    print(f"Running {iterations} iterations for each scenario...\n")
    
    for name, inputs in scenarios:
        start_time = time.time()
        for _ in range(iterations):
            app.invoke(inputs)
        avg_time = (time.time() - start_time) / iterations
        print(f"Scenario: {name}")
        print(f"  Average response time: {avg_time:.4f}s")
    
    # Cleanup
    if os.path.exists(test_db): os.remove(test_db)
    if os.path.exists(test_file): os.remove(test_file)
    print("\n✅ Performance validation completed.")

if __name__ == "__main__":
    run_performance_test()
