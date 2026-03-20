Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\ecommerce\services\sync_users.bat" & Chr(34), 0
Set WshShell = Nothing
