@echo off
set "logfile=%~dp0sync_users_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Sincronizacion de Usuarios (DBF)
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_multithread\sync_users_dbf.py

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

