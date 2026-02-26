# Guía Completa de Deploy - FarmaCruz E-commerce

Esta guía unificada cubre el despliegue en **EC2**, conexión a **Amazon RDS PostgreSQL**, configuración de proxy con **Nginx**, **HTTPS (Let's Encrypt)**, e integración con **CloudFront** para el frontend.

---

## 📋 Tabla de Contenido

1. [Fase 1: Preparación del Servidor (EC2 Base)](#fase-1-preparación-del-servidor-ec2-base)
2. [Fase 2: Conexión a Base de Datos (Amazon RDS)](#fase-2-conexión-a-base-de-datos-amazon-rds)
3. [Fase 3: Entorno Backend (FastAPI)](#fase-3-entorno-backend-fastapi)
4. [Fase 4: Configuración de Servicios (Gunicorn, Nginx, Timers)](#fase-4-configuración-de-servicios-gunicorn-nginx-timers)
5. [Fase 5: Frontend e Integración CloudFront](#fase-5-frontend-e-integración-cloudfront)
6. [Fase 6: Centro de Control y Monitoreo (Cheat Sheet)](#fase-6-centro-de-control-y-monitoreo-cheat-sheet)
7. [Fase 7: Deploy y Actualizaciones](#fase-7-deploy-y-actualizaciones)
8. [Resolución de Problemas (Troubleshooting)](#resolución-de-problemas-troubleshooting)
9. [Limpieza de Base de Datos](#limpieza-de-base-de-datos)
10. [Utils]
---

## Fase 1: Preparación del Servidor (EC2 Base)

### 1.1 Conexión y Repositorio (GitHub via SSH)

1. Conéctate a tu EC2:
   ```bash
   ssh -i tu-llave.pem ec2-user@tu-ec2-ip
   ```
2. Genera una llave SSH (presiona Enter a todo para dejarlo sin password):
   ```bash
   ssh-keygen -t ed25519
   cat ~/.ssh/id_ed25519.pub
   ```
3. Copia el output y agrégalo en GitHub en:
   **Settings** → **Deploy keys** → **Add deploy key**
4. Clona el repositorio:
   ```bash
   cd ~
   git clone git@github.com:tuusuario/farmacruz-ecomerce.git
   cd farmacruz-ecomerce
   ```

### 1.2 Actualización del Sistema e Instalación de Dependencias

Ejecuta lo siguiente para preparar el sistema operativo (Amazon Linux):

```bash
sudo dnf update -y
sudo dnf upgrade -y

# Python y herramientas build
sudo dnf install python3 python3-pip python3-devel gcc gcc-c++ make -y

# Cliente PostgreSQL y Dependencias (para psycopg2)
sudo dnf install postgresql15 postgresql-devel -y

# Servidor Nginx y Git
sudo dnf install nginx git -y
```

---

## Fase 2: Conexión a Base de Datos (Amazon RDS)

### 2.1 Credenciales y Accesos

Tu Instancia RDS está identificada en AWS como `farmacruz-db`.
*   **Endpoint:** `farmacruz.xxxxx.us-east-1.rds.amazonaws.com` *(reemplazar xxxxx con tu endpoint real, por ejemplo ccn22ys0s7ya o c2fcii8uqcxl)*.
*   **Puerto:** `5432`
*   **Security Group:** Asegúrate de que las `Inbound Rules` del Security Group de RDS permiten entrada `PostgreSQL (5432)` desde el Security Group de tu EC2 (`sg-ec2`).

### 2.2 Prueba de Conexión y Creación de DB

Desde tu EC2 ejecuta:

```bash
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d postgres \
     -p 5432
```
Si la conexión es exitosa, dentro de psql ejecuta:
```sql
CREATE DATABASE farmacruz_db;
\c farmacruz_db
```

### 2.3 Ejecutar Migraciones (initv2.sql)

Para cargar tus tablas iniciales (`categories`, `products`, `users`, etc.):

```bash
psql "host=farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
user=farmacruz_user \
dbname=farmacruz_db \
port=5432 \
sslmode=require" \
-f ~/farmacruz-ecomerce/database/db_init_v2.sql
```

---

## Fase 3: Entorno Backend (FastAPI)

### 3.1 Entorno Virtual y Paquetes

```bash
cd ~/farmacruz-ecomerce/backend
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 3.2 Variables de Entorno (.env)

El archivo maneja credenciales sensibles como la cadena a RDS, el JWT secret y reglas de CORS:

```bash
nano ~/farmacruz-ecomerce/backend/.env
```

Agrega estrictamente este contenido (sustituyendo tu password real de RDS y generando tu SECRET_KEY con `openssl rand -hex 32`):

```ini
# Amazon RDS PostgreSQL
DATABASE_URL=postgresql://farmacruz_user:TU_PASSWORD@farmacruz.xxxxx.us-east-1.rds.amazonaws.com:5432/farmacruz_db

# JWT Secret
SECRET_KEY=a1b2c3d4e5f6...tu_secret_generado

# CORS (CloudFront Producción + Dev Local)
ALLOWED_ORIGINS=https://digheqbxnmxr3.cloudfront.net,https://ddyn91nmr858h.cloudfront.net,http://localhost:3000
FRONTEND_URL=https://ddyn91nmr858h.cloudfront.net

# Entorno
ENVIRONMENT=production
```

---

## Fase 4: Configuración de Servicios (Gunicorn, Nginx, Timers)

En esta fase creamos los archivos de sistema que mantendrán la aplicación viva y corriendo procesos secundarios.

### Archivo 1: API Backend (systemd/Gunicorn)

Este servicio levanta FastAPI usando Gunicorn con workers de Uvicorn (mejor rendimiento en producción).

```bash
sudo nano /etc/systemd/system/farmacruz-api.service
```

```ini
[Unit]
Description=FarmaCruz FastAPI Backend
After=network.target

[Service]
Type=simple
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin:/usr/bin"
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend:/home/ec2-user/farmacruz-ecomerce/backend/farmacruz_api"

ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/gunicorn \
    farmacruz_api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120

Restart=always
RestartSec=3
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
```

### Archivo 2: Reverse Proxy y Rate Limiting (Nginx)

Configura Nginx para rutear el tráfico puerto 80 hacia el puerto 8000 (Backend).

```bash
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

> [!WARNING]
> Conflicto: Si Nginx te dice `conflicting server name "_"`, edita `/etc/nginx/nginx.conf` y comenta/elimina el bloque `server { ... }` por defecto de Amazon Linux.

```nginx
client_max_body_size 50M;
# Rate limit usando el IP real detrás del Load Balancer/CloudFront
limit_req_zone $http_x_forwarded_for zone=api_limit:10m rate=50r/s;

server {
    listen 80;
    server_name _;

    location / {
        # Burst de 100 para que React no se bloquee al cargar el dashboard
        limit_req zone=api_limit burst=100 nodelay;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # Timeouts largos para tus procesos de sincronización pesados
        proxy_connect_timeout 90s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### Archivo 3 y 4: Job Diario de Similitud (Systemd Service & Timer)

Usamos un Timer en lugar de cron para ejecutar `product_similarity.py` diariamente a las 3:00 AM, aprovechando `journalctl` para sus logs.

1. **El script de ejecución (.service):**
```bash
sudo nano /etc/systemd/system/farmacruz-similarity.service
```
```ini
[Unit]
Description=FarmaCruz Product Similarity Engine
After=network.target

[Service]
Type=oneshot
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend"
ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/python3 farmacruz_api/utils/product_similarity.py
```

2. **La regla de tiempo (.timer):**
```bash
sudo nano /etc/systemd/system/farmacruz-similarity.timer
```
```ini
[Unit]
Description=Run Product Similarity nightly at 3AM

[Timer]
OnCalendar=*-*-* 03:00:00
Persistent=true
Unit=farmacruz-similarity.service

[Install]
WantedBy=timers.target
```

### Activar Toda la Infraestructura (Sólo primera vez)

```bash
# Recargar configuraciones de systemd
sudo systemctl daemon-reload

# Habilitar e iniciar la API
sudo systemctl enable --now farmacruz-api

# Validar sintaxis, habilitar e iniciar Nginx
sudo nginx -t
sudo systemctl enable --now nginx

# Habilitar e iniciar únicamente el Timer del Job
sudo systemctl enable --now farmacruz-similarity.timer
```

---

## Fase 5: Frontend e Integración CloudFront

### 5.1 Configurar CloudFront para React SPA Routing

React maneja las rutas en el navegador. Si el usuario recarga la página en `/admindash`, CloudFront podría dar `404 AccessDenied` porque busca un archivo físico.
1. En **AWS Console**, ve a tu distribución de **CloudFront**.
2. Da clic en la pestaña **Error pages**.
3. **Create custom error response**:
   * HTTP error code: `403: Forbidden`
   * Customize error response: `Yes`
   * Response page path: `/index.html`
   * HTTP Response code: `200: OK`
4. **Repite el paso** creando otra respuesta igual pero para el código `404: Not Found`.

### 5.2 Apuntar React al Endpoint Correcto (Opcional si usas SSL)

Si en el futuro usas Let's Encrypt o tu IP (`ec2-54-225-140-250.compute-1.amazonaws.com`/`farmacruz.duckdns.org`), asegúrate que `react/src/config/api.js` contenga la base real, por ejemplo `BASE_URL: 'https://api.midominio.com'`. Posteriormente:
```bash
cd ~/farmacruz-ecomerce/react
npm run build
# Subir la carpeta dist/ a S3 / invalidar caché de CloudFront.
```

---

## Fase 6: Centro de Control y Monitoreo (Cheat Sheet)

Esta sección concentra TODOS los comandos para administrar tu infraestructura en un solo lugar.

### 6.1 Estados de Vida (Arranque y Paro)

| Servicio | Empezar | Parar | Recargar Config (Sin Caída) |
| :--- | :--- | :--- | :--- |
| **API Backend** | `sudo systemctl start farmacruz-api` | `sudo systemctl stop farmacruz-api` | `sudo systemctl reload farmacruz-api` |
| **Nginx Proxy** | `sudo systemctl start nginx` | `sudo systemctl stop nginx` | `sudo systemctl reload nginx` |
| **Similarity Job** | `sudo systemctl start farmacruz-similarity.service` (Ejecutar manualmente ahora) | N/A | N/A |

*Nota: Para reiniciar apagando y prendiendo el proceso duro usa `restart`, por ejemplo: `sudo systemctl restart farmacruz-api`.*

### 6.2 Leer Logs y Registros (`journalctl`)

Reemplaza `$SERVICIO` por `farmacruz-api`, o `farmacruz-similarity.service` según corresponda.

*   **Ver tiempo real (En vivo):** `sudo journalctl -u $SERVICIO -f`
*   **Ver los últimos 50 mensajes:** `sudo journalctl -u $SERVICIO -n 50 --no-pager`
*   **Ver sólo ERRORES de hoy:** `sudo journalctl -u $SERVICIO -p err --since today`

**Logs Web de Nginx:**
*   **Tráfico/Conexiones:** `sudo tail -f /var/log/nginx/access.log`
*   **Errores 502/Gateway:** `sudo tail -f /var/log/nginx/error.log`

### 6.3 Validaciones de Recursos Activos

*   **¿Quién usa el puerto 8000?:** `sudo ss -tlnp | grep :8000`
*   **¿A qué hora corre el próximo Job de IA?:** `systemctl list-timers --all | grep farmacruz`
*   **Uso vitalitario (CPU y RAM):** `htop` (o `free -h`)

---

## Fase 7: Deploy y Actualizaciones

Para asegurar que nuevas versiones suban fluidamente, crea un script único:

```bash
nano ~/deploy.sh
```

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy..."

# 1. Pull changes
cd ~/farmacruz-ecomerce
git pull origin main

# 2. Update Backend Dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --quiet

# 3. Reload Configs & Restart Services
sudo systemctl daemon-reload
sudo systemctl restart farmacruz-api

# 4. Check Status
sleep 2
sudo systemctl status farmacruz-api --no-pager

echo "✅ Deploy completado!"
```

Dale permisos de ejecución: `chmod +x ~/deploy.sh`. Cuando necesites actualizar código de GitHub a EC2, simplemente ejecuta:
```bash
~/deploy.sh
```

---

## Resolución de Problemas (Troubleshooting)

### El Backend API da status "Failed" o Error al iniciar
Lo primero es usar el Centro de Control:
1. Revisa logs: `sudo journalctl -u farmacruz-api -n 100 --no-pager`.
2. Prueba manual si no hay pistas:
   ```bash
   cd ~/farmacruz-ecomerce/backend
   source venv/bin/activate
   uvicorn farmacruz_api.main:app --host 127.0.0.1 --port 8000
   ```
3. Valida credenciales faltantes haciendo: `cat ~/farmacruz-ecomerce/backend/.env`

### Fallas base de datos RDS (Errores TimeOut Psycopg2)
1. Has un PING al servidor: `ping farmacruz.xxxxx.us-east-1.rds.amazonaws.com`.
2. Checa si el puerto está respondiendo en AWS: `telnet farmacruz.xxxxx.us-east-1.rds.amazonaws.com 5432`.
   *Si tu telnet bloquea por tiempo, perdiste la regla de entrada en el Security Group de AWS RDS.*

### El sitio Frontend arroja Error 502 Bad Gateway
1. Confirma si la API está viva con el comando local: `curl http://127.0.0.1:8000/api/v1/health`
2. Si la API sí responde, el Nginx la perdió. Lee los errores de la fase 6: `sudo tail -n 50 /var/log/nginx/error.log`

### La Página en CloudFront ni siquiera contacta al EC2
* Revisa en el panel de AWS EC2 que el Security Group de tu máquina tenga permiso de Inbound `HTTP (8000) o (80)` proveniente de un Prefix List de AWS (`pl-xxxxxx`) o IPs de CloudFront.

---

## Limpieza de Base de Datos

psql "host=farmacruz-db.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
user=farmacruzdb \
dbname=postgres \
port=5432 \
sslmode=require"

-- 1. Desactivar triggers (para evitar errores de llaves foráneas al borrar)
SET session_replication_role = 'replica';

-- 2. Limpiar tablas transaccionales (Pedidos, Carrito)
TRUNCATE TABLE orderitems CASCADE;
TRUNCATE TABLE orders CASCADE;
TRUNCATE TABLE cartcache CASCADE;

-- 3. Limpiar catálogo y relaciones (Productos, Categorias, Listas)
TRUNCATE TABLE pricelistitems CASCADE;
TRUNCATE TABLE pricelists CASCADE;
TRUNCATE TABLE product_recommendations CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE categories CASCADE;

-- 4. Limpiar Clientes y Grupos de Ventas
TRUNCATE TABLE customerinfo CASCADE;
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE groupmarketingmanagers CASCADE;
TRUNCATE TABLE groupsellers CASCADE;
TRUNCATE TABLE salesgroups CASCADE;

-- 5. Limpiar Usuarios INTERNOS (manteniendo Admins)
-- Borra todo lo que NO sea admin, marketing o seller creado a mano.
DELETE FROM users WHERE role NOT IN ('admin', 'marketing');

-- 6. Reactivar triggers
SET session_replication_role = 'origin';

-- 7. Verificar limpieza
SELECT 'Usuarios restantes' as tabla, count(*) FROM users
UNION ALL
SELECT 'Productos restantes', count(*) FROM products;

---

## Utils
### User Login to AWS CLI
aws configure --profile s3-sync-farmacruz

### AWS CLI
  s3-sync-farmacruz
  AKIA34YUT6S5EIR4xxxx
  JbZK+X6bJ1QiiMVcje9DtjFuZ6n9aK+0qithxxxx