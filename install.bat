@echo off
setlocal
echo ===================================================
echo     OmniDesktop-MCP One-Click Installer
echo ===================================================

where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH! Please install Python 3.10+.
    pause
    exit /b 1
)

echo [*] Creating virtual environment (venv)...
if not exist "venv" (
    python -m venv venv
)

echo [*] Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo [*] Configuring AI Agent integrations...
python setup_agent.py

echo.
echo ===================================================
echo [SUCCESS] OmniDesktop-MCP is ready to use!
echo Run 'run.bat' to start the server manually.
echo ===================================================
pause
