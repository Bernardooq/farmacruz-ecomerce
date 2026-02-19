@echo off
cd /d "%~dp0.."
echo ===================================================
echo Subiendo ZIP de Usuarios
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_zip\upload_users_sync.py

echo.
echo Proceso finalizado.
pause
