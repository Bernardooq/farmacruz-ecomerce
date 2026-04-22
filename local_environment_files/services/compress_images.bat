@echo off
set "logfile=%~dp0compress_images_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "%~dp0.."
echo ===================================================
echo Iniciando Compresion de Imagenes a WebP
echo ===================================================

echo Ejecutando script Python...
.\services\venv\Scripts\python.exe servicios\images_service\compress_images_to_webp.py

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

