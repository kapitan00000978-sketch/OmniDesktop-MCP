@echo off
setlocal
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run install.bat first!
    pause
    exit /b 1
)

echo Starting OmniDesktop-MCP server...
venv\Scripts\python.exe server.py
