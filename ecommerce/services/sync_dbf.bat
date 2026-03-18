@echo off
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Sincronizacion General de DBF
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\sync_multithread\sync_dbf_to_backend.py

echo.
echo Proceso finalizado.

