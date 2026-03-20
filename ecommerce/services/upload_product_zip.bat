@echo off
cd /d "C:\ecommerce"
echo ===================================================
echo Subiendo ZIP de Productos
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\sync_zip\upload_products_sync.py"

echo.
echo Proceso finalizado.

