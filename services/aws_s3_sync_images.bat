@echo off
cd /d "%~dp0.."
echo ===================================================
echo Sincronizacion de Imagenes a S3 (farmacruz-imgs)
echo ===================================================
echo.
echo Este script cargara el CONTENIDO de tu carpeta local al bucket.
echo.

set LOCAL_DIR="C:\Users\berna\Downloads\CompressedImg"

if "%LOCAL_DIR%"=="" goto error

echo.
echo Sincronizando: "%LOCAL_DIR%" -> s3://farmacruz-imgs
echo Perfil AWS: s3-sync-farmacruz
echo.

aws s3 sync "%LOCAL_DIR%" s3://farmacruz-imgs --profile s3-sync-farmacruz

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Hubo un problema al sincronizar. Revisa tus credenciales o la ruta.
) else (
    echo.
    echo [EXITO] Sincronizacion completada.
)
goto end

:error
echo.
echo [ERROR] No ingresaste ninguna ruta. Intentalo de nuevo.

:end
echo.

