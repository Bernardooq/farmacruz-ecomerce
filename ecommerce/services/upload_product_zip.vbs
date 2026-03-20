Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\ecommerce\services\upload_product_zip.bat" & Chr(34), 0
Set WshShell = Nothing
