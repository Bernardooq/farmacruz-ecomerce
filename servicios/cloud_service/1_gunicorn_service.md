# Instalación de Servicio Uvicorn en EC2 (Ubuntu/Amazon Linux)

## Arquitectura
- **t3.micro**: 1 vCPU, 1GB RAM
- **Uvicorn**: 1 worker (mejor para instancias pequeñas)
- **ThreadPoolExecutor**: Maneja sync tasks en background (max_workers=2)

## 1. Crear el archivo del servicio
```bash
sudo nano /etc/systemd/system/farmacruz-api.service
```

## 2. Contenido del servicio
```ini
[Unit]
Description=FarmaCruz FastAPI Backend (Uvicorn)
After=network.target postgresql.service

[Service]
Type=notify
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/farmacruz-ecomerce/backend
Environment="PATH=/home/ubuntu/farmacruz-ecomerce/backend/venv/bin"
Environment="PYTHONPATH=/home/ubuntu/farmacruz-ecomerce/backend"

# Uvicorn con 1 worker (óptimo para t3.micro)
ExecStart=/home/ubuntu/farmacruz-ecomerce/backend/venv/bin/uvicorn \
    main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --log-level info \
    --access-log \
    --use-colors

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
sudo chown ubuntu:www-data /var/log/farmacruz
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
