import os
import shutil
import subprocess
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

def create_file(path: str, content: str = "") -> str:
    """Create a new file with specified content."""
    try:
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Sir, I have created the file at '{path}' successfully."
    except Exception as e:
        return f"Sir, I encountered an error creating '{path}': {str(e)}"

def edit_file(path: str, content: str) -> str:
    """Edit or update content of an existing file."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Sir, the file '{path}' does not exist. Would you like me to create it for you?"
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Sir, I have updated the file '{path}' with your new content."
    except Exception as e:
        return f"Sir, error editing '{path}': {str(e)}"

def read_file(path: str) -> str:
    """Read contents of a target file."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Sir, the file '{path}' was not found."
        with open(abs_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(2000)
        return f"File Content ('{path}'):\n{content}"
    except Exception as e:
        return f"Sir, error reading '{path}': {str(e)}"

def delete_file(path: str, confirmed: bool = False) -> str:
    """Safely delete a file or directory with confirmation check."""
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Sir, the file or directory '{path}' does not exist."
        
        if not confirmed:
            return (
                f"⚠️ **Confirmation Required**, Sir.\n"
                f"Are you sure you want me to delete '{path}'? "
                f"Please reply 'Yes, delete {path}' to confirm this action."
            )

        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            return f"Sir, the directory '{path}' and all its contents have been deleted."
        else:
            os.remove(abs_path)
            return f"Sir, the file '{path}' has been deleted successfully."
    except Exception as e:
        return f"Sir, error deleting '{path}': {str(e)}"

def run_cmd(command: str, confirmed: bool = False) -> str:
    """Run shell command with safety check."""
    try:
        dangerous_kw = ["rmdir /s", "del /f", "format", "drop database"]
        if any(dk in command.lower() for dk in dangerous_kw) and not confirmed:
            return f"⚠️ **Safety Warning**, Sir. Executing '{command}' is destructive. Reply 'Confirm command' to proceed."

        res = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=15)
        out = res.stdout.strip() or res.stderr.strip() or "Command completed with no output."
        return f"Command Output ('{command}'):\n{out}"
    except Exception as e:
        return f"Sir, error executing command: {str(e)}"
