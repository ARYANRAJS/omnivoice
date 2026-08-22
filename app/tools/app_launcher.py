import os
import subprocess
import logging

logger = logging.getLogger(__name__)

# Safe whitelist of allowed application launch commands on Windows
SAFE_APPS = {
    "chrome": ["start", "chrome"],
    "google chrome": ["start", "chrome"],
    "vs code": ["code"],
    "vscode": ["code"],
    "visual studio code": ["code"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
    "calc": ["calc"],
    "explorer": ["explorer"],
    "file explorer": ["explorer"],
    "cmd": ["start", "cmd"],
}

def open_application(app_name: str) -> str:
    name_clean = app_name.lower().strip()
    
    matched_key = None
    for key in SAFE_APPS:
        if key in name_clean:
            matched_key = key
            break

    if not matched_key:
        allowed_list = ", ".join(SAFE_APPS.keys())
        return f"App '{app_name}' is not in the allowed safe applications list ({allowed_list})."

    cmd = SAFE_APPS[matched_key]
    try:
        if os.name == "nt":
            subprocess.Popen(cmd, shell=True)
        else:
            subprocess.Popen(cmd)
        return f"Opened {matched_key.title()} successfully."
    except Exception as e:
        logger.error(f"Failed to open application {app_name}: {e}")
        return f"Could not open application {app_name}: {e}"
