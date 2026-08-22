@echo off
TITLE OmniVoice Local AI Agent — Launcher
echo ========================================================
echo   OmniVoice — Local Personal Voice AI Agent Launcher
echo ========================================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

set PYTHONPATH=.

:: Launch browser in background
start "" http://localhost:8000

:: Start application server
python app/main.py

pause
