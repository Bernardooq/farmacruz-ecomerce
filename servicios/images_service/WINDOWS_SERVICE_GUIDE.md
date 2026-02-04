Configuración de Servicio de Imágenes (Daily + AWS S3)
======================================================

Este servicio tiene dos partes:
1.  **Compresión:** Convierte imágenes nuevas a WebP.
2.  **AWS Sync:** Sube las imágenes procesadas a la nube (S3).

---

### Paso 0: Instalar Librerías en el Venv

Asegurate de activar el venv de servicios (creado en la guía de Sync) e instalar Pillow:

```cmd
cd C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios
venv\Scripts\activate
pip install pillow
```

---

### Paso 1: Configurar Usuario AWS (IAM)

*(Igual que antes...)*

---

### Paso 2: Instalar AWS CLI

*(Igual que antes...)*

---

### Paso 3: Crear Script Maestro (`run_daily_images.bat`)

Crearemos un script que haga todo el trabajo junto.

1.  En la carpeta `servicios\images_service`, crea un archivo `run_daily_images.bat`.
2.  Pega este contenido:

```bat
@echo off
echo --- INICIANDO SERVICIO DE IMAGENES ---
date /t & time /t

echo [1/2] Comprimiendo imagenes...
cd /d "C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\images_service"
:: Usamos el Python del venv de servicios
"C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\venv\Scripts\python.exe" compress_images_to_webp.py

echo [2/2] Sincronizando con AWS S3...
:: Reemplaza 'farmacruz-images-bucket' con el bucket real
aws s3 sync "C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\backend\images" s3://farmacruz-images-bucket --exclude "*" --include "*.webp" --cache-control "max-age=31536000"

echo --- FINALIZADO ---
```

---

### Paso 4: Programar Tarea Diaria

1.  Abre **Programador de Tareas**.
2.  Crear Tarea: `FarmaCruz_Images_Daily`.
3.  **General:** Ejecutar tanto si el usuario inició sesión como si no.
4.  **Desencadenadores:**
    *   Iniciar: Al inicio del sistema? No, mejor a una hora específica.
    *   Iniciar: **Según una programación**.
    *   Diariamente.
    *   Inicio: **02:00:00 AM** (Cuando la tienda está tranquila).
5.  **Acciones:**
    *   Programa: `run_daily_images.bat`
    *   Iniciar en: `C:\Users\berna\Documents\GitProjects\farmacruz-ecomerce\servicios\images_service`


### Extra: Cache-Control imagenes de ecommerce
1.  Ir a la carpeta donde esta el bucket de s3
2.  Seleccionar todas las imagenes
3.  Acción -> Propiedades -> Metadatos -> Agregar metadatos
4.  Agregar:
    *   Type: System defined.
    *   Key: Cache-Control.
    *   Value: max-age=2592000.