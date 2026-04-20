# Arquitectura FarmaCruz E-commerce
## CloudFront + EC2 + RDS PostgreSQL

```
┌─────────────────────────────────────────────────────────────────┐
│                    ARQUITECTURA AWS                             │
└─────────────────────────────────────────────────────────────────┘

┌──────────┐
│ Frontend │  React (S3 + CloudFront)
│ (React)  │  URL: https://digheqbxnmxr3.cloudfront.net
└────┬─────┘
     │ HTTPS
     ↓
┌────────────┐
│ CloudFront │  ← CDN de AWS (HTTPS termination aquí)
│ (AWS)      │  
└────┬───────┘
     │ HTTP (interno AWS)
     ↓
┌─────────────────────────────────────────────────────────────────┐
│                          VPC                                    │
│  ┌────────────────┐              ┌─────────────────┐            │
│  │ EC2 t3.micro   │   Postgres   │ RDS PostgreSQL  │            │
│  │ nginx:8000     │──────────────▶│ (Managed AWS)   │            │
│  │ uvicorn:8000   │   Protocol   │ Port: 5432      │            │
│  │                │              │                 │            │
│  │ - FastAPI      │              │ - Automated     │            │
│  │ - ThreadPool   │              │   backups       │            │
│  │ - Sync scripts │              │ - Multi-AZ      │            │
│  └────────────────┘              └─────────────────┘            │
└─────────────────────────────────────────────────────────────────┘

```

## Servicios

### 1. **Amazon RDS PostgreSQL**
- Base de datos gestionada por AWS
- Endpoint: `farmacruz.xxxxx.us-east-1.rds.amazonaws.com:5432`
- **NO está en EC2** - servicio separado en VPC
- Backups automáticos, alta disponibilidad

### 2. **EC2 t3.micro**
- **Uvicorn (Puerto 8000)**: FastAPI backend
- **nginx (Puerto 8000)**: Reverse proxy
- **ThreadPoolExecutor**: Sync tasks background
- Se conecta a RDS via VPC

### 3. **CloudFront**
- CDN global
- HTTPS termination
- Cacheo de assets estáticos

### 4. **Systemd Timers**
- `farmacruz-similarity.timer`: Recalcula similitudes (3 AM)

## Security Groups

### EC2 Security Group
```
Inbound Rules:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SSH (22)       │ Tu IP              │ Admin SSH
HTTP (8000)    │ pl-3b927c52 (CF)   │ CloudFront → API
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Outbound Rules:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
All traffic    │ 0.0.0.0/0          │ Internet + RDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### RDS Security Group
```
Inbound Rules:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PostgreSQL (5432) │ sg-ec2-xxxxx    │ Solo EC2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**CRÍTICO:** RDS solo acepta conexiones del Security Group de EC2

## Flujo de Datos

### Usuario → API
```
Usuario → HTTPS → CloudFront → HTTP → EC2 nginx:8000 → Uvicorn → RDS
```

### Sincronización DBF
```
PC Local → SSH → EC2 → Python sync scripts → RDS PostgreSQL
```

### Deploy
```
GitHub → Deploy Key → git pull en EC2 → systemctl restart → Conecta a RDS
```

## Variables de Entorno (.env)

```bash
# RDS PostgreSQL (NO localhost)
DATABASE_URL=postgresql://farmacruz_user:PASSWORD@farmacruz.xxxxx.us-east-1.rds.amazonaws.com:5432/farmacruz_db

# JWT
SECRET_KEY=tu_secret_key_hex

# CORS
ALLOWED_ORIGINS=https://digheqbxnmxr3.cloudfront.net
```

