@echo off
set "logfile=%~dp0aws_s3_sync_images_log.txt"

call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio
setlocal
cd /d "%~dp0.."

:: Credenciales de AWS (Para Task Scheduler)
set AWS_ACCESS_KEY_ID=PONER_AQUI_ACCESS_KEY
set AWS_SECRET_ACCESS_KEY=PONER_AQUI_SECRET_KEY
set AWS_DEFAULT_REGION=us-east-1

echo ===================================================
echo Sincronizacion de Imagenes a S3 (farmacruz-imgs)
echo ===================================================

set LOCAL_DIR="C:\Users\berna\Downloads\CompressedImg"

echo Sincronizando: %LOCAL_DIR% -> s3://farmacruz-imgs
echo.

:: Ejecucion usando variables de entorno
aws s3 sync %LOCAL_DIR% s3://farmacruz-imgs

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema al sincronizar.
) else (
    echo.
    echo [EXITO] Sincronizacion completada con exito.
)

echo.
echo [%date% %time%] FIN
endlocal
echo ---------------------------------------------------
goto :eof

