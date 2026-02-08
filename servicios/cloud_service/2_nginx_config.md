# Configuración de Nginx (CloudFront Reverse Proxy)

## Arquitectura
```
Usuario → HTTPS → CloudFront → HTTP → EC2 nginx:8000 → Uvicorn:8000
```

**IMPORTANTE:** EC2 **NO** necesita SSL. CloudFront maneja HTTPS.

## 1. Instalar Nginx
```bash
# Amazon Linux
sudo dnf install nginx -y
```

## 2. Configuración Nginx
```bash
# Amazon Linux usa conf.d/ directamente
sudo nano /etc/nginx/conf.d/farmacruz.conf
```

## 3. Contenido de configuración
```nginx
# Límite de tamaño para uploads (sync DBF comprimidos)
client_max_body_size 50M;

# Rate limiting (protección DDoS)
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    listen 8000;
    server_name _;  # Acepta cualquier host (CloudFront lo maneja)

    location / {
        # Rate limit: permite bursts para sync scripts
        limit_req zone=api_limit burst=50 nodelay;

        # Headers de seguridad
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # Proxy a Uvicorn
        proxy_pass http://127.0.0.1:8000;
        
        # Headers importantes
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
}
```

## 4. Activar configuración
```bash
# Amazon Linux: archivo ya está en conf.d/, no necesita symlink
# Solo validar y reiniciar
```

## 5. Validar y reiniciar
```bash
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## 6. Verificar
```bash
# Verificar que nginx escucha en puerto 8000
sudo netstat -tlnp | grep :8000

# Ver logs
sudo tail -f /var/log/nginx/error.log
```

## Security Group en EC2
**IMPORTANTE:** Configura el Security Group para solo aceptar tráfico de CloudFront:

```
Inbound Rules:
- SSH (22)       → Tu IP personal
- HTTP (8000)    → pl-3b927c52 (CloudFront IPv4 prefix list)
```

## Notas
- **No SSL en EC2**: CloudFront maneja HTTPS
- **Rate limiting**: Burst=50 permite sync scripts con ThreadPoolExecutor
- **Puerto 8000**: nginx escucha en 8000, redirige a Uvicorn en 8000

