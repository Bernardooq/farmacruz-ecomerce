@echo off
cd /d "C:\ecommerce"
echo ===================================================
echo Iniciando Sincronizacion de Usuarios (DBF)
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\sync_multithread\sync_users_dbf.py"

echo.
echo Proceso finalizado.

