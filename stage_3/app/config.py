import os
from pathlib import Path

# Base directory for stage_3
BASE_DIR = Path(__file__).resolve().parent.parent

# Output file path for confirmed reservations
# Defaults to storage/confirmed_reservations.txt
CONFIRMED_FILE_PATH = os.getenv(
    "CONFIRMED_FILE_PATH", 
    str(BASE_DIR / "storage" / "confirmed_reservations.txt")
)

# API Token for basic bearer authentication
# Placeholder for simple token validation
API_TOKEN = os.getenv("STAGE_3_API_TOKEN", "default_secret_token")
