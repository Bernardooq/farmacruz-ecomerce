# Instalación de Servicio Uvicorn en EC2 (Amazon Linux)

## Arquitectura
- **t3.micro**: 1 vCPU, 1GB RAM
- **Gunicorn+Uvicorn**: 4 workers (configuración robusta)
- **ThreadPoolExecutor**: Maneja sync tasks en background (max_workers=2)

## 1. Crear el archivo del servicio
```bash
sudo nano /etc/systemd/system/farmacruz-api.service
```

## 2. Contenido del servicio
```ini
[Unit]
Description=FarmaCruz FastAPI Backend (Gunicorn + Uvicorn)
After=network.target

[Service]
Type=simple
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend"

ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/gunicorn \
    farmacruz_api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8000 \
    --timeout 120

# Restart automático
Restart=always
RestartSec=3

# Límites de recursos
LimitNOFILE=4096

[Install]
WantedBy=multi-user.target
```

## 3. Crear directorio de logs
```bash
sudo mkdir -p /var/log/farmacruz
sudo chown ec2-user:nginx /var/log/farmacruz
```

## 4. Activar el servicio
```bash
sudo systemctl daemon-reload
sudo systemctl enable farmacruz-api
sudo systemctl start farmacruz-api
```

## 5. Verificar estado
```bash
# Ver estado
sudo systemctl status farmacruz-api

# Ver logs en tiempo real
sudo journalctl -u farmacruz-api -f

# Ver últimos 50 logs
sudo journalctl -u farmacruz-api -n 50 --no-pager
```

## 6. Comandos útiles
```bash
# Reiniciar después de cambios en código
sudo systemctl restart farmacruz-api

# Detener servicio
sudo systemctl stop farmacruz-api

# Ver logs de errores
sudo journalctl -u farmacruz-api -p err
```

## Notas
- **1 worker** es suficiente para t3.micro (1 vCPU)
- **ThreadPoolExecutor** en el código maneja tareas pesadas (sync DBF)
- Logs van a `journalctl` (systemd), no a archivos separados
