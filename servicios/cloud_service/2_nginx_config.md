# Configuración de Nginx con HTTPS (Let's Encrypt)

## Arquitectura

### Opción 1: Con CloudFront (HTTP)
```
Usuario → HTTPS → CloudFront → HTTP → EC2 nginx:80 → Uvicorn:8000
```

### Opción 2: Directo EC2 HTTPS (Recomendado)
```
Usuario → HTTPS → EC2 nginx:443 → Uvicorn:8000
```

## Pre-requisitos para HTTPS

1. **Dominio apuntando a EC2**
   - Tipo A: `api.tudominio.com` → IP EC2
   - O usar DuckDNS (gratis): `farmacruz.duckdns.org`

2. **Puertos abiertos en Security Group**
   ```
   Inbound Rules:
   - SSH (22)    → Tu IP
   - HTTP (80)   → 0.0.0.0/0
   - HTTPS (443) → 0.0.0.0/0
   ```

---

## Configuración HTTP Simple (Sin SSL)

### 1. Instalar Nginx
```bash
sudo dnf install nginx -y
```

### 2. Crear configuración
```bash
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

### 3. Contenido HTTP

> [!WARNING]
> **Importante:** Asegúrate de que no haya otros bloques `server` activos en `/etc/nginx/nginx.conf` que escuchen en el puerto 80. Si es así, coméntalos o elimínalos para evitar conflictos.

```nginx
client_max_body_size 50M;
limit_req_zone $http_x_forwarded_for zone=api_limit:10m rate=50r/s;

server {
    listen 80;
    server_name _;

    location / {
        limit_req zone=api_limit burst=100 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 4. Activar
```bash
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

---

## Configuración HTTPS con Let's Encrypt

### 1. Instalar Certbot

#### Amazon Linux 2023:
```bash
sudo dnf install -y certbot python3-certbot-nginx
```

#### Amazon Linux 2:
```bash
sudo yum install -y epel-release
sudo yum install -y certbot python3-certbot-nginx
```

### 2. Obtener Certificado SSL

**Reemplaza `api.tudominio.com` con tu dominio real:**

```bash
sudo certbot --nginx -d api.tudominio.com
```

**Durante instalación:**
1. Email: tu@email.com
2. Terms: Y (aceptar)
3. Share email: N
4. Redirect HTTP → HTTPS: 2 (Sí)

### 3. Configuración HTTPS Completa

Certbot configura automáticamente, pero puedes optimizar:

```bash
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

```nginx
client_max_body_size 50M;
limit_req_zone $http_x_forwarded_for zone=api_limit:10m rate=50r/s;

# Redirigir HTTP → HTTPS
server {
    listen 80;
    server_name api.tudominio.com;
    return 301 https://$server_name$request_uri;
}

# Servidor HTTPS
server {
    listen 443 ssl http2;
    server_name api.tudominio.com;

    # Certificados SSL (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.tudominio.com/privkey.pem;
    
    # Configuración SSL segura
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;

    # Proxy a FastAPI
    location / {
        limit_req zone=api_limit burst=100 nodelay;
        
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

### 4. Validar y Recargar
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Verificar Auto-Renovación
```bash
# Ver timer de renovación
sudo systemctl status certbot.timer

# Probar renovación (dry-run)
sudo certbot renew --dry-run
```

---

## Testing

### Probar HTTP
```bash
curl http://localhost/api/v1/
```

### Probar HTTPS
```bash
curl https://api.tudominio.com/api/v1/
```

### Ver certificado
```bash
openssl s_client -connect api.tudominio.com:443 -servername api.tudominio.com
```

---

## Troubleshooting

### Error: Port 443 already in use
```bash
sudo lsof -i :443
sudo systemctl stop nginx
sudo certbot --nginx -d api.tudominio.com
```

### Error: DNS no resuelve
```bash
nslookup api.tudominio.com
# Debe mostrar la IP de tu EC2
```

### Renovación falla
```bash
sudo certbot renew --dry-run
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

---

## Alternativa: DuckDNS (Sin dominio propio)

1. Ir a [duckdns.org](https://www.duckdns.org)
2. Login con GitHub/Google
3. Crear: `farmacruz.duckdns.org`
4. Actualizar IP a tu EC2
5. Usar en certbot:

```bash
sudo certbot --nginx -d farmacruz.duckdns.org
```
