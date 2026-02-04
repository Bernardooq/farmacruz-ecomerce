Instalación de Servicio Gunicorn en EC2 (Amazon Linux 2/2023)
=============================================================

1. Crear el archivo del servicio:
sudo nano /etc/systemd/system/farmacruz.service

2. Pegar el siguiente contenido (Asegura las rutas):
[Unit]
Description=Gunicorn instance to serve FarmaCruz API
After=network.target

[Service]
User=ec2-user
Group=nginx
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000 main:app --access-logfile /var/log/farmacruz_access.log --error-logfile /var/log/farmacruz_error.log

[Install]
WantedBy=multi-user.target


3. Iniciar y Habilitar el servicio:
sudo systemctl start farmacruz
sudo systemctl enable farmacruz
sudo systemctl status farmacruz
