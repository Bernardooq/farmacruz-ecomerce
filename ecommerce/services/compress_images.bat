@echo off
cd /d "C:\ecommerce"
echo ===================================================
echo Iniciando Compresion de Imagenes a WebP
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\images_service\compress_images_to_webp.py"

echo.
echo Proceso finalizado.

