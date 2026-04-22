@echo off
set "logfile=%~dp0sync_dbf_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Sincronizacion General de DBF
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_multithread\sync_dbf_to_backend.py

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

