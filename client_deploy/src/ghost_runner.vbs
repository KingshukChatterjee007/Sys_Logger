' Sys_Logger - Ghost Runner v2 (Zero-Visibility)
' Calls pythonw.exe directly. No cmd.exe. No console flash. No detectable shell process.
' The PYTHONW_PATH placeholder is replaced by setup_windows.ps1 at install time.

Dim fso, strDir, pythonwPath, launcherPath
Set fso = CreateObject("Scripting.FileSystemObject")
strDir = fso.GetParentFolderName(WScript.ScriptFullName)

' --- Injected by setup_windows.ps1 at install time ---
pythonwPath = strDir & "\venv\Scripts\pythonw.exe"

launcherPath = strDir & "\launcher.pyw"

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = strDir
' Window Style 0 = completely hidden. False = don't wait for it to finish (fire and forget)
WshShell.Run Chr(34) & pythonwPath & Chr(34) & " " & Chr(34) & launcherPath & Chr(34), 0, False

