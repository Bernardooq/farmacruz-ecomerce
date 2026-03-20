@echo off
cd /d "C:\ecommerce"
echo ===================================================
echo Iniciando Sincronizacion General de DBF
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\sync_multithread\sync_dbf_to_backend.py"

echo.
echo Proceso finalizado.

