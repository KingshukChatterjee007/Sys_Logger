' Sys_Logger - Ghost Runner
' Runs boot_start.bat with zero console visibility
Set WshShell = CreateObject("WScript.Shell")
strPath = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptPosition)
WshShell.CurrentDirectory = strPath
WshShell.Run "cmd.exe /c boot_start.bat", 0, False
