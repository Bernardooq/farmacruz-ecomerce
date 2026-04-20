Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "c:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\services\aws_s3_sync_images.bat" & Chr(34), 0
Set WshShell = Nothing
