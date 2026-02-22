Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d C:\Users\User\Projects\telegram-agent && start_telegram.bat", 0, False
