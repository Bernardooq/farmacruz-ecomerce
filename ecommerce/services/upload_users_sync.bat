@echo off
set "logfile=C:\ecommerce\services\upload_users_sync_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "C:\ecommerce"
echo ===================================================
echo Subiendo ZIP de Usuarios
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\sync_zip\upload_users_sync.py"

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

