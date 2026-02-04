Configuración de Job Recurrente: Similitud de Productos (Systemd Timer)
=======================================================================

En lugar de usar `cron` (que es difícil de debyeuguear), usaremos **Systemd Timers**. Esto permite ver logs con `journalctl` y es más robusto.

El script se ejecutará automáticamente todas las noches a las **03:00 AM**.

1. Crear el Servicio (Define QUÉ ejecutar):
sudo nano /etc/systemd/system/farmacruz-similarity.service

Pegar contenido:
[Unit]
Description=FarmaCruz Product Similarity Engine
After=network.target

[Service]
Type=oneshot
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
# Pythonpath para que encuentre los modulos
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend"
ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/python3 farmacruz_api/utils/product_similarity.py

[Install]
WantedBy=multi-user.target


2. Crear el Timer (Define CUÁNDO ejecutar):
sudo nano /etc/systemd/system/farmacruz-similarity.timer

Pegar contenido:
[Unit]
Description=Run Product Similarity nightly at 3AM

[Timer]
# Ejecutar cada día a las 03:00:00
OnCalendar=*-*-* 03:00:00
# Si el servidor estaba apagado, ejecutar cuanto antes al prender
Persistent=true
Unit=farmacruz-similarity.service

[Install]
WantedBy=timers.target


3. Activar el Timer:
sudo systemctl daemon-reload
sudo systemctl enable --now farmacruz-similarity.timer

4. Comandos Útiles:
- Ver estado del timer (cuando es la proxima ejecucion):
  systemctl list-timers --all | grep farmacruz

- Ejecutar manualmente AHORA (para probar):
  sudo systemctl start farmacruz-similarity.service

- Ver logs de ejecución:
  journalctl -u farmacruz-similarity.service -n 50 --no-pager
