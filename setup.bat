@echo off
TITLE OmniVoice Local AI Agent — Windows Setup
echo ========================================================
echo   OmniVoice — Local Personal Voice AI Setup
echo ========================================================
echo.

:: 1. Check Python version
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python is not installed or not in PATH.
    echo     Please install Python 3.10 or Python 3.11 from python.org
    pause
    exit /b 1
)

echo [✓] Python detected.

:: 2. Create virtual environment
if not exist venv (
    echo [*] Creating virtual environment (venv)...
    python -m venv venv
) else (
    echo [✓] Virtual environment already exists.
)

:: 3. Activate virtual environment
call venv\Scripts\activate.bat

:: 4. Upgrade pip & Install requirements
echo [*] Installing dependencies from requirements.txt...
python -m pip install --upgrade pip
pip install -r requirements.txt

:: 5. Create required directories & .env file
if not exist voices mkdir voices
if not exist data mkdir data

if not exist .env (
    echo [*] Creating default .env from .env.example...
    copy .env.example .env
)

:: 6. Check Ollama installation
echo [*] Checking Ollama local LLM status...
python -c "import httpx; res=httpx.get('http://localhost:11434/api/tags'); print('[✓] Ollama server is running!') if res.status_code==200 else print('[!] Ollama is not running on http://localhost:11434')" 2>nul
if %errorlevel% neq 0 (
    echo [!] WARNING: Ollama connection failed.
    echo     Please download Ollama from https://ollama.com and run:
    echo     ollama pull qwen3:1.7b
)

echo.
echo ========================================================
echo   [✓] Setup completed successfully!
echo   Run 'run.bat' to start your local Voice AI Agent.
echo ========================================================
echo.
pause
