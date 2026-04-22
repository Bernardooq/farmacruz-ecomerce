@echo off
set "logfile=C:\ecommerce\services\sync_dbf_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
cd /d "C:\ecommerce"
echo ===================================================
echo Iniciando Sincronizacion General de DBF
echo ===================================================

echo Ejecutando script Python...
"C:\ecommerce\servicios\venv\Scripts\python.exe" "C:\ecommerce\servicios\sync_multithread\sync_dbf_to_backend.py"

echo.
echo Proceso finalizado.
echo [%date% %time%] Fin
echo ---------------------------------------------------
goto :eof

