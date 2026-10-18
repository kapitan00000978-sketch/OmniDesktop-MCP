@echo off
setlocal
echo Stopping OmniDesktop-MCP background service...

powershell -NoProfile -Command ^
  "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*OmniDesktop-MCP*server.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force; Write-Host ('[OK] Stopped PID ' + $_.ProcessId) }"

echo Done.
pause
