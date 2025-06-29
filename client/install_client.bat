@echo off

if not exist "%APPDATA%\MonitorClient" mkdir "%APPDATA%\MonitorClient"

copy "monitor_client.exe" "%APPDATA%\MonitorClient\"

reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "MonitorClient" /t REG_SZ /d "\"%APPDATA%\MonitorClient\monitor_client.exe\"" /f

pause 