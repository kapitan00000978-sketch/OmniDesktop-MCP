@echo off
setlocal
echo Checking OmniDesktop-MCP service status...

powershell -NoProfile -Command ^
  "$procs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*OmniDesktop-MCP*server.py*' }; if ($procs) { Write-Host '[STATUS: ACTIVE]' -ForegroundColor Green; $procs | Select-Object ProcessId, CommandLine | Format-Table -AutoSize } else { Write-Host '[STATUS: INACTIVE / NOT RUNNING]' -ForegroundColor Yellow }"

pause
