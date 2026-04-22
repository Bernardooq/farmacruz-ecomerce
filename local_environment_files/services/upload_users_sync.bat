@echo off
set "logfile=%~dp0upload_users_sync_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "%~dp0.."
echo ===================================================
echo Subiendo ZIP de Usuarios
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_zip\upload_users_sync.py

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

