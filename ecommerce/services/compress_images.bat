@echo off
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Compresion de Imagenes a WebP
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\images_service\compress_images_to_webp.py

echo.
echo Proceso finalizado.

