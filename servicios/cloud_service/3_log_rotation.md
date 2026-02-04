Configuración de Log Rotation (Mantenimiento Automático)
========================================================

Para evitar que los logs llenen el disco duro, configuraremos Logrotate para borrar logs antiguos (más de 30 días).

1. Crear archivo de configuración:
sudo nano /etc/logrotate.d/farmacruz

2. Pegar contenido:
/var/log/farmacruz_*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 nginx nginx
    sharedscripts
    postrotate
        [ -f /var/run/nginx.pid ] && kill -USR1 `cat /var/run/nginx.pid`
    endscript
}

explicación:
- daily: Rota cada día
- rotate 30: Guarda los últimos 30 días (1 mes)
- compress: Comprime los logs viejos (.gz) para ahorrar espacio
- create: Crea el nuevo archivo con permisos correctos (usuario nginx)

3. Probar configuración (Dry Run):
sudo logrotate -d /etc/logrotate.d/farmacruz
