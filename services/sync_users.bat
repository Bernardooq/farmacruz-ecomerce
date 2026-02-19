@echo off
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Sincronizacion de Usuarios (DBF)
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_multithread\sync_users_dbf.py

echo.
echo Proceso finalizado.
pause
