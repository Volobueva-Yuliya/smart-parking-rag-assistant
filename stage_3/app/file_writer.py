import os
from stage_3.app.config import CONFIRMED_FILE_PATH

def get_confirmed_file_path() -> str:
    return os.getenv("CONFIRMED_FILE_PATH", CONFIRMED_FILE_PATH)

def append_to_file(line: str, file_path: str = None) -> bool:
    """
    Appends a line of text to a file.
    If the directory or file does not exist, it creates them.
    Each entry must end with a newline.
    Uses UTF-8 encoding.
    """
    target_path = file_path if file_path else get_confirmed_file_path()
    
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(target_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        # Ensure it ends with a newline
        if not line.endswith("\n"):
            line += "\n"
        
        with open(target_path, "a", encoding="utf-8") as f:
            f.write(line)
        return True
    except Exception:
        # For this stage, we simple return False on any file error
        return False
