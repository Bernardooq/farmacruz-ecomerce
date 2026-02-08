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
psql -h farmacruzdb.c2fcii8uqcxl.us-east-1.rds.amazonaws.com \
     -U manuel \
     -d postgres \
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
- [ ] CloudFront apuntando a EC2
- [ ] Security Group EC2: CloudFront prefix list
- [ ] Primer deploy exitoso

**¡Listo para producción!** 🎯
