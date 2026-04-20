@echo off
echo --- INICIANDO SERVICIO DE IMAGENES ---
date /t & time /t

echo [1/2] Comprimiendo imagenes...
cd /d "C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\images_service"

:: Usamos el Python del venv de servicios para ejecutar el script de compresion
"C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\venv\Scripts\python.exe" compress_images_to_webp.py

echo [2/2] Sincronizando con AWS S3...
:: Sube solo los archivos .webp nuevos o modificados
:: --cache-control "max-age=2592000" le dice al navegador que guarde la imagen por 1 mes
aws s3 sync "C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\backend\images" s3://farmacruz-images-bucket --exclude "*" --include "*.webp" --cache-control "max-age=2592000"

echo --- FINALIZADO ---
pause
