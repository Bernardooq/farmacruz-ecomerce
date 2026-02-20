# Guía Completa de Deploy - FarmaCruz E-commerce

## CloudFront + EC2 + Amazon RDS PostgreSQL

---

## 📋 Tabla de Contenido

1. [Preparación GitHub y SSH](#1-preparación-github-y-ssh)
2. [Configuración Inicial EC2](#2-configuración-inicial-ec2)
3. [Instalación Backend (FastAPI)](#3-instalación-backend-fastapi)
4. [Conexión a Amazon RDS](#4-conexión-a-amazon-rds)
5. [Configuración Servicios (systemd)](#5-configuración-servicios-systemd)
6. [Monitoreo y Control de Servicios](#6-monitoreo-y-control-de-servicios)
7. [Deploy y Actualizaciones](#7-deploy-y-actualizaciones)
8. [Troubleshooting](#8-troubleshooting)
9. [Configurar HTTPS con Let's Encrypt](#9-configurar-https-con-lets-encrypt-opcional-pero-recomendado)
10. [Configurar CloudFront para React (SPA Routing)](#10-configurar-cloudfront-para-react-spa-routing)

---

## 1. Preparación GitHub y SSH

### Generar SSH Key en EC2

```bash
# Conectarse a EC2 (Amazon Linux)
ssh -i tu-llave.pem ec2-user@tu-ec2-ip

# Generar llave SSH para GitHub
ssh-keygen -t ed25519
# Presionar Enter en todas las preguntas (sin passphrase)

# Ver la llave pública
cat ~/.ssh/id_ed25519.pub
# Copiar TODO el output
wkasytznlnxeieix
```

### Agregar Deploy Key en GitHub

1. GitHub repo: `https://github.com/tuusuario/farmacruz-ecomerce`
2. **Settings** → **Deploy keys** → **Add deploy key**
3. **Title**: `EC2 Production Server`
4. **Key**: Pegar llavepública completa
5. ✅ **Allow write access** (opcional, solo si necesitas push desde EC2)
6. **Add key**

### Clonar Repositorio

```bash
cd ~
git clone git@github.com:tuusuario/farmacruz-ecomerce.git
cd farmacruz-ecomerce
git status
```

---

## 2. Configuración Inicial EC2

### Actualizar Sistema

```bash
sudo dnf update -y
sudo dnf upgrade -y
```

### Instalar Dependencias

```bash
# Python y herramientas
sudo dnf install python3 python3-pip python3-devel -y

# Build tools (para psycopg2, pandas, etc.)
sudo dnf install gcc gcc-c++ make postgresql-devel -y

# Nginx
sudo dnf install nginx -y

# PostgreSQL client (para conectarse a RDS)
sudo dnf install postgresql15 -y

# Git
sudo dnf install git -y
```

---

## 3. Instalación Backend (FastAPI)

### Crear Virtual Environment

```bash
cd ~/farmacruz-ecomerce/backend
python3 -m venv venv
source venv/bin/activate
```

### Instalar Dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configurar Variables de Entorno

```bash
nano ~/farmacruz-ecomerce/backend/.env
```

**Contenido del `.env`:**

```ini
# Amazon RDS PostgreSQL (NO localhost)
DATABASE_URL=postgresql://farmacruz_user:TU_PASSWORD@farmacruz.xxxxx.us-east-1.rds.amazonaws.com:5432/farmacruz_db

# JWT Secret (generar con: openssl rand -hex 32)
SECRET_KEY=a1b2c3d4e5f6...tu_secret_generado

# CORS (CloudFront + dev local)
ALLOWED_ORIGINS=https://digheqbxnmxr3.cloudfront.net,http://localhost:3000

# Environment
ENVIRONMENT=production
```

**Generar SECRET_KEY:**

```bash
openssl rand -hex 32
# Copiar output al .env
```

---

## 4. Conexión a Amazon RDS

### Obtener Endpoint de RDS

1. AWS Console → **RDS** → **Databases**
2. Click en tu instancia `farmacruz-db`
3. **Connectivity & security**
4. Copiar **Endpoint**: `farmacruz.xxxxx.us-east-1.rds.amazonaws.com`

### Verificar Security Group de RDS

```
RDS Security Group Inbound Rules:
┌──────────────────────────────────────────────┐
│ PostgreSQL (5432) │ sg-ec2 │ Solo desde EC2 │
└──────────────────────────────────────────────┘
```

**Verificar que el security group de EC2 pueda acceder a RDS.**

### Conectarse a RDS desde EC2

```bash
# Test de conexión
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d postgres \
     -p 5432

# Ingresar password cuando lo pida
# Si conecta: estás listo ✅
```

### Crear Base de Datos (si no existe)

```bash
# Conectado a psql (comando anterior)
CREATE DATABASE farmacruz_db;
\c farmacruz_db
```

### Ejecutar initv2.sql

```bash
# Opción 1: Desde EC2 con psql
psql "host=farmacruz-db.ccn22ys0s7ya.us-east-1.rds.amazonaws.com \
user=farmacruzdb \
dbname=postgres \
port=5432 \
sslmode=require" \
-f ~/farmacruz-ecomerce/database/db_init_v2.sql


# Opción 2: Copiar y pegar interactivamente
psql -h farmacruzdb.c2fcii8uqcxl.us-east-1.rds.amazonaws.com \
     -U manuel \
     -d postgres

# Dentro de psql, copiar contenido de initv2.sql
```

### Verificar Tablas Creadas

```sql
-- Dentro de psql
\dt

-- Debería mostrar:
-- categories, products, users, customers, price_lists, etc.
```

---

## 5. Configuración Servicios (systemd)

### A. Servicio FastAPI (Uvicorn)

```bash
sudo nano /etc/systemd/system/farmacruz-api.service
```

**Contenido:**

```ini
[Unit]
Description=FarmaCruz FastAPI Backend
After=network.target

[Service]
Type=notify
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend/farmacruz_api
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend"

ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/uvicorn \
    main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --log-level info

Restart=always
RestartSec=3
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
```

**Activar:**

```bash
sudo systemctl daemon-reload
sudo systemctl enable farmacruz-api
sudo systemctl start farmacruz-api
sudo systemctl status farmacruz-api
```

### B. Nginx (Reverse Proxy)

```bash
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

**Contenido:**

```nginx
client_max_body_size 50M;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 80;
    server_name _;

    location / {
        limit_req zone=api_limit burst=50 nodelay;
    
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

> [!WARNING]
> **Conflicto con configuración por defecto**
> Es posible que el archivo `/etc/nginx/nginx.conf` tenga un bloque `server { ... }` por defecto que entre en conflicto. Si al reiniciar Nginx ves errores como `conflicting server name "_"`, debes editar `/etc/nginx/nginx.conf` y comentar o eliminar ese bloque `server` por defecto.

**Activar:**

```bash
# Amazon Linux usa conf.d/, no sites-available/enabled
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

### C. Job de Similitud (cron diario 3 AM)

Ver: `servicios/cloud_service/4_similarity_job.md`

---

## 6. Monitoreo y Control de Servicios

### Ver Estado de Servicios

```bash
# Backend API
sudo systemctl status farmacruz-api

# Nginx
sudo systemctl status nginx

# Todos los servicios
systemctl list-units --type=service --state=running | grep farma
```

### Control de Servicios

#### Farmacruz API (Backend)

```bash
# Iniciar
sudo systemctl start farmacruz-api

# Detener
sudo systemctl stop farmacruz-api

# Reiniciar
sudo systemctl restart farmacruz-api

# Recargar (sin downtime)
sudo systemctl reload farmacruz-api

# Ver si está habilitado (auto-start en boot)
sudo systemctl is-enabled farmacruz-api

# Habilitar auto-start
sudo systemctl enable farmacruz-api

# Deshabilitar auto-start
sudo systemctl disable farmacruz-api
```

#### Nginx

```bash
# Iniciar
sudo systemctl start nginx

# Detener
sudo systemctl stop nginx

# Reiniciar
sudo systemctl restart nginx

# Recargar config (sin downtime)
sudo systemctl reload nginx

# Test config antes de aplicar
sudo nginx -t
```

### Ver Logs en Tiempo Real

#### Logs de Backend

```bash
# Últimos 50 logs
sudo journalctl -u farmacruz-api -n 50 --no-pager

# En tiempo real (follow)
sudo journalctl -u farmacruz-api -f

# Solo errores
sudo journalctl -u farmacruz-api -p err

# Desde hace 1 hora
sudo journalctl -u farmacruz-api --since "1 hour ago"

# Hoy
sudo journalctl -u farmacruz-api --since today
```

#### Logs de Nginx

```bash
# Access log en tiempo real
sudo tail -f /var/log/nginx/access.log

# Error log en tiempo real
sudo tail -f /var/log/nginx/error.log

# Últimas 100 líneas de error
sudo tail -n 100 /var/log/nginx/error.log
```

### Verificar Puertos y Conexiones

```bash
# Ver qué escucha en puerto 8000
sudo netstat -tlnp | grep :8000

# Ver todas las conexiones activas
sudo netstat -tlnp

# Alternativa moderna (requiere net-tools)
sudo ss -tlnp | grep :8000
```

### Monitoreo de Recursos

```bash
# CPU, RAM, procesos
htop

# Uso de disco
df -h

# Memoria disponible
free -h

# Ver procesos de Python
ps aux | grep python

# Ver procesos de Nginx
ps aux | grep nginx
```

### Verificar Conexión a RDS

```bash
# Test rápido
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d farmacruz_db \
     -c "SELECT version();"

# Ver tablas
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d farmacruz_db \
     -c "\dt"
```

---

## 7. Deploy y Actualizaciones

### Script de Deploy Automatizado

```bash
nano ~/deploy.sh
```

**Contenido:**

```bash
#!/bin/bash
set -e

echo "🚀 Iniciando deploy..."

# 1. Git pull
cd ~/farmacruz-ecomerce
echo "📦 Pulling latest code..."
git pull origin main

# 2. Actualizar dependencias backend
cd backend
source venv/bin/activate
echo "📚 Instalando dependencias..."
pip install -r requirements.txt --quiet

# 3. Ejecutar migraciones (si existen)
if [ -f "initv2.sql" ]; then
    echo "🗄️  Ejecutando migraciones..."
    # psql -h RDS_ENDPOINT -U farmacruz_user -d farmacruz_db -f initv2.sql
fi

# 4. Reiniciar servicio
echo "🔄 Reiniciando backend..."
sudo systemctl restart farmacruz-api

# 5. Verificar
sleep 2
sudo systemctl status farmacruz-api --no-pager

echo "✅ Deploy completado!"
```

**Darle permisos:**

```bash
chmod +x ~/deploy.sh
```

**Ejecutar:**

```bash
~/deploy.sh
```

### Deploy Manual

```bash
cd ~/farmacruz-ecomerce
git pull
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart farmacruz-api
```

---

## 8. Troubleshooting

### Backend no inicia

```bash
# Ver errores detallados
sudo journalctl -u farmacruz-api -n 200 --no-pager

# Probar manualmente
cd ~/farmacruz-ecomerce/backend
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Verificar .env
cat ~/farmacruz-ecomerce/backend/.env
```

### No conecta a RDS

```bash
# Test básico
ping farmacruz.xxxxx.us-east-1.rds.amazonaws.com

# Test PostgreSQL
telnet farmacruz.xxxxx.us-east-1.rds.amazonaws.com 5432

# Verificar variables
cd ~/farmacruz-ecomerce/backend
source venv/bin/activate
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('DATABASE_URL'))"
```

### Nginx devuelve 502

```bash
# Verificar backend activo
sudo systemctl status farmacruz-api

# Test local
curl http://127.0.0.1:8000/api/v1/health

# Ver logs nginx
sudo tail -f /var/log/nginx/error.log
```

### CloudFront no conecta a EC2

```bash
# Verificar Security Group permite prefix list CloudFront
# AWS Console → EC2 → Security Groups → Inbound rules
# Debe tener: HTTP (8000) → pl-3b927c52

# Test desde EC2
curl -I http://localhost:8000/api/v1/health
```

### Comandos de Emergencia

```bash
# Reiniciar todo
sudo systemctl restart farmacruz-api nginx

# Ver últimos errores
sudo journalctl -p err -n 50 --no-pager

# Limpiar logs viejos (liberar espacio)
sudo journalctl --vacuum-time=7d
```

## 9. Configurar HTTPS con Let's Encrypt (Opcional pero Recomendado)

### Pre-requisitos

1. **Dominio apuntando a EC2**

   - Configura DNS tipo A: `api.tudominio.com` → IP de tu EC2
   - O usa DuckDNS (gratis): `farmacruz.duckdns.org`
2. **Puertos abiertos en Security Group**

   ```
   Inbound Rules:
   - SSH (22)    → Tu IP
   - HTTP (80)   → 0.0.0.0/0
   - HTTPS (443) → 0.0.0.0/0
   ```

### Instalar Certbot

#### Amazon Linux 2023:

```bash
sudo dnf install -y certbot python3-certbot-nginx
```

#### Amazon Linux 2:

```bash
sudo yum install -y epel-release
sudo yum install -y certbot python3-certbot-nginx
```

### Obtener Certificado SSL

**Reemplaza con tu dominio:**

```bash
sudo certbot --nginx -d api.tudominio.com
```

**Responder:**

1. Email: `tu@email.com` (notificaciones de renovación) ntkw hjll nnaf vrpm 
2. Terms of Service: `Y`
3. Share email: `N`
4. Redirect HTTP to HTTPS: `2` (Sí)

**Resultado esperado:**

```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/api.tudominio.com/fullchain.pem
```

### Actualizar Configuración Nginx

Certbot configura automáticamente, pero verifica:

```bash
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

**Debe quedar así:**

```nginx
client_max_body_size 50M;
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# HTTP → HTTPS redirect
server {
    listen 80;
    server_name api.tudominio.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name api.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/api.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tudominio.com/privkey.pem;
  
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    location / {
        limit_req zone=api_limit burst=50 nodelay;
    
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

**Recargar:**

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### Verificar Auto-Renovación

```bash
# Ver timer (renueva automáticamente)
sudo systemctl status certbot.timer

# Probar renovación (dry-run)
sudo certbot renew --dry-run
```

### Actualizar Frontend

Cambiar BASE_URL en `react/src/config/api.js`:

```javascript
// Antes (HTTP)
BASE_URL: 'http://ec2-54-225-140-250.compute-1.amazonaws.com',

// Después (HTTPS con dominio)
BASE_URL: 'https://api.tudominio.com',
```

Rebuild y deploy:

```bash
npm run build
# Subir dist/ a S3 y invalidar CloudFront
```

### Actualizar CORS en Backend

Editar `.env`:

```ini
# Permitir frontend CloudFront
FRONTEND_URL=https://ddyn91nmr858h.cloudfront.net
```

Reiniciar backend:

```bash
sudo systemctl restart farmacruz-api
```

### Testing

```bash
# Verificar HTTPS funciona
curl https://api.tudominio.com/api/v1/

# Ver certificado
openssl s_client -connect api.tudominio.com:443

# Logs
sudo tail -f /var/log/nginx/access.log
```

---

## Checklist de Deploy

- [ ] SSH Key generada en EC2
- [ ] Deploy Key agregada en GitHub
- [ ] Repositorio clonado
- [ ] Virtual environment creado
- [ ] Dependencias instaladas
- [ ] RDS PostgreSQL creado y accesible
- [ ] Security Group RDS permite EC2
- [ ] Conectado a RDS exitosamente
- [ ] initv2.sql ejecutado
- [ ] Archivo `.env` configurado con RDS endpoint
- [ ] Servicio `farmacruz-api` activo
- [ ] Nginx configurado y activo
- [ ] **[Opcional] Dominio DNS configurado**
- [ ] **[Opcional] Certificado SSL instalado**
- [ ] **[Opcional] Nginx HTTPS configurado**
- [ ] CloudFront frontend apuntando correctamente
- [ ] Primer deploy exitoso

**¡Listo para producción!** 🎯

---

## 10. Configurar CloudFront para React (SPA Routing)

Si al recargar la página en una ruta como `/admindash` recibes un error `AccessDenied` (XML) o `404`, es porque CloudFront busca un archivo físico que no existe. React maneja el ruteo en el cliente, por lo que debemos redirigir todo al `index.html`.

### Pasos en AWS Console:

1.  Ve a **CloudFront** y selecciona tu distribución.
2.  Ve a la pestaña **Error pages** (Páginas de error).
3.  Haz clic en **Create custom error response**.

#### Configuración para Error 403 (Access Denied):
Esto pasa porque S3 deniega acceso a archivos no existentes.

*   **HTTP error code**: `403: Forbidden`
*   **Customize error response**: `Yes`
*   **Response page path**: `/index.html`
*   **HTTP response code**: `200: OK`
*   Haz clic en **Create**.

#### Configuración para Error 404 (Not Found):
Opcional, pero recomendado para manejar rutas no existentes vía React.

*   **HTTP error code**: `404: Not Found`
*   **Customize error response**: `Yes`
*   **Response page path**: `/index.html`
*   **HTTP response code**: `200: OK`
*   Haz clic en **Create**.

**Resultado:**
Ahora CloudFront servirá `index.html` para cualquier ruta que no sea un archivo físico, permitiendo que `react-router` tome el control y muestre la página correcta.

**AWS CLI**
s3-sync-farmacruz
AKIA34YUT6S5EIR4xxxx
JbZK+X6bJ1QiiMVcje9DtjFuZ6n9aK+0qithxxxx


**Database**
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