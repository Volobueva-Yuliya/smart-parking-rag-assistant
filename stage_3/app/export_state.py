import json
import os
from pathlib import Path

# Path for the local export state file in stage_3 storage
# Defaults to storage/exported_codes.json
BASE_DIR = Path(__file__).resolve().parent.parent

def get_state_file_path() -> str:
    return os.getenv(
        "EXPORT_STATE_FILE_PATH", 
        str(BASE_DIR / "storage" / "exported_codes.json")
    )

def load_exported_codes() -> set:
    """
    Loads reservation codes that have already been exported.
    
    Returns:
        set: A set of exported reservation codes.
    """
    state_path = get_state_file_path()
    if not os.path.exists(state_path):
        return set()
    
    try:
        with open(state_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data)
    except (json.JSONDecodeError, IOError):
        # Fallback in case of corruption or read error
        return set()

def save_exported_codes(codes: set):
    """
    Saves the list of exported reservation codes to the state file.
    
    Args:
        codes (set): Set of reservation codes.
    """
    state_path = get_state_file_path()
    # Ensure directory exists
    directory = os.path.dirname(state_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    
    with open(state_path, 'w', encoding='utf-8') as f:
        json.dump(list(codes), f, indent=4)

def mark_as_exported(reservation_code: str):
    """
    Marks a single reservation as exported.
    
    Args:
        reservation_code (str): The reservation code to mark.
    """
    codes = load_exported_codes()
    codes.add(reservation_code)
    save_exported_codes(codes)
