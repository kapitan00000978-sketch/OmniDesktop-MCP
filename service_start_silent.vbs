' OmniDesktop-MCP Silent Background Launcher
' Runs the server invisibly in the background without opening any command prompt windows.
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

strScriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
strPython = strScriptDir & "\venv\Scripts\pythonw.exe"
strServer = strScriptDir & "\server.py"

' Check if pythonw exists (pythonw runs without console window)
If Not fso.FileExists(strPython) Then
    strPython = strScriptDir & "\venv\Scripts\python.exe"
End If

' Launch server with SSE transport in background (0 = hide window, False = don't wait)
strCmd = """" & strPython & """ """ & strServer & """ --transport sse --port 8765"
WshShell.Run strCmd, 0, False
