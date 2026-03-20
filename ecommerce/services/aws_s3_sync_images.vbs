Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\ecommerce\services\aws_s3_sync_images.bat" & Chr(34), 0
Set WshShell = Nothing
