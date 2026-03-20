Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\ecommerce\services\upload_users_sync.bat" & Chr(34), 0
Set WshShell = Nothing
