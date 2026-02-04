Configuración de Nginx (CloudFront + SSL + Seguridad) - Amazon Linux
========================================================================

Esta configuración asume:
- **CloudFront** maneja el tráfico público y redirige `/api` a este EC2.
- **EC2** tiene una IP Elástica.
- **Certbot** gestionará el SSL para el subdominio `api.farmacruz.com.mx`.

1. Instalar Nginx:
sudo dnf install nginx -y

2. Configuración de Rate Limit y Server Block:
sudo nano /etc/nginx/conf.d/farmacruz.conf

3. Contenido (Copiar y Pegar):
# ----------------------------------------------------------------------
# 1. OPTIMIZACIÓN GZIP Y TAMAÑO DE CARGA
# ----------------------------------------------------------------------
# Permitimos hasta 50MB para soportar tus cargas GZIP de productos/precios.
client_max_body_size 50M;

# ----------------------------------------------------------------------
# 2. IDENTIFICACIÓN DE IP REAL (HÍBRIDO: CloudFront + Sync Directo)
# ----------------------------------------------------------------------
# Tu arquitectura recibe tráfico de dos fuentes:
# A) Usuarios -> CloudFront -> EC2 (Traen header X-Forwarded-For)
# B) Sync Server -> Directo a EC2 (IP Dinámica, conexión directa)

# Como tu Sync Server tiene IP dinámica, NO puedes restringir el Security Group
# solo a CloudFront. Debes dejar abierto el puerto 443 a 0.0.0.0/0.

# Configuración Real IP:
real_ip_header X-Forwarded-For;
# Al poner 0.0.0.0/0 confiamos en cualquier proxy. Esto es necesario
# porque no podemos filtrar IPs, pero Nginx intentará resolver la IP real
# si el header existe (CloudFront), o usará la IP directa (Sync Server).
set_real_ip_from 0.0.0.0/0; 

# ----------------------------------------------------------------------
# 3. RATE LIMITING (Sincronización vs Ciberataques)
# ----------------------------------------------------------------------
# Definimos una zona de memoria de 10MB para trackear IPs.
# Límite Base: 10 peticiones/segundo (suficiente para tus 2500 clientes).
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

server {
    server_name api.farmacruz.com.mx; 

    location / {
        # --- PROTECCIÓN DDOS ---
        # burst=50: Permite una "ráfaga" de 50 peticiones de golpe.
        # Esto es CRÍTICO para tu "Sync Server" local que envía muchos hilos.
        # Si fuera menor, tu propia sincronización fallaría con Error 503.
        limit_req zone=api_limit burst=50 nodelay;

        # --- HEADERS DE SEGURIDAD (Hardening) ---
        # Evitan clickjacking, sniff de tipos MIME, etc.
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # --- PROXY A GUNICORN ---
        proxy_pass http://127.0.0.1:8000;
        
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # --- CORS (CloudFront Compatibility) ---
        # Permitimos que CloudFront pase los headers de origen y método.
        proxy_pass_header Access-Control-Allow-Origin;
        proxy_pass_header Access-Control-Allow-Methods;
        proxy_pass_header Access-Control-Allow-Headers;
    }
}

4. Validar y reiniciar Nginx:
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

5. Instalar Certbot (SSL):
sudo dnf install python3-pip -y
sudo pip3 install certbot certbot-nginx
sudo ln -s /usr/local/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d api.farmacruz.com.mx
