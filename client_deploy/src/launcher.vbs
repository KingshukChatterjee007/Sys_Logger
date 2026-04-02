' Sys_Logger - Ghost Launcher
' Runs PM2 resurrect with zero console visibility
Set WshShell = CreateObject("WScript.Shell")
' 0 = Hidden window, False = Don't wait for command to exit
WshShell.Run "pm2 resurrect", 0, False
