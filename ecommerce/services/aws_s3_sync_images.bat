@echo off
set "logfile=C:\ecommerce\services\aws_s3_sync_images.txt"

:: Redirigir toda la salida al log y también mostrarla en consola si se desea
:: (En Task Scheduler lo importante es el archivo)
call :main >> "%logfile%" 2>&1
exit /b

:main
echo [%date% %time%] Inicio de Sincronizacion
setlocal
cd /d "C:\ecommerce"

:: Credenciales de AWS (Para Task Scheduler)
set AWS_ACCESS_KEY_ID=PONER_AQUI_ACCESS_KEY
set AWS_SECRET_ACCESS_KEY=PONER_AQUI_SECRET_KEY
set AWS_DEFAULT_REGION=us-east-1

echo ===================================================
echo Sincronizacion de Imagenes a S3 (farmacruz-imgs)
echo ===================================================
echo.

set LOCAL_DIR="C:\ecommerce\compressedIMG"

echo Sincronizando: %LOCAL_DIR% a s3://farmacruz-imgs
echo.

:: Ejecucion usando variables de entorno
aws s3 sync %LOCAL_DIR% s3://farmacruz-imgs --exclude "*" --include "*.webp" --cache-control "max-age=2592000"

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
