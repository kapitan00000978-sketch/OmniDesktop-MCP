@echo off
setlocal
echo ===================================================
echo     OmniDesktop-MCP Windows Auto-Start Installer
echo ===================================================

set "SCRIPT_DIR=%~dp0"
set "VBS_PATH=%SCRIPT_DIR%service_start_silent.vbs"
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\OmniDesktop-MCP.lnk"

echo [*] Creating Windows startup shortcut...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = 'wscript.exe'; $s.Arguments = '\"%VBS_PATH%\"'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.Description = 'OmniDesktop-MCP Background Daemon'; $s.Save()"

if exist "%SHORTCUT_PATH%" (
    echo [OK] Auto-start shortcut successfully created!
    echo      Location: %SHORTCUT_PATH%
    echo.
    echo [*] Starting background service now...
    wscript.exe "%VBS_PATH%"
    echo [OK] OmniDesktop-MCP is now running in the background!
) else (
    echo [ERROR] Failed to create startup shortcut.
)

echo ===================================================
pause
