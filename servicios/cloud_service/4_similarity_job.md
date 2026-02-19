# 🔄 Servicio de Similitud de Productos (Systemd Timer)

Este servicio se encarga de calcular y actualizar la similitud entre productos de manera periódica. En lugar de usar `cron`, utilizamos **Systemd Timers** por su robustez, mejor manejo de logs y gestión de dependencias.

---

## 📋 Arquitectura y Funcionamiento

El sistema se compone de dos unidades de systemd:
1.  **`farmacruz-similarity.service`**: Define **QUÉ** se debe ejecutar (el script de Python).
2.  **`farmacruz-similarity.timer`**: Define **CUÁNDO** se debe ejecutar (la programación horaria).

### Ventajas sobre Cron
- **Logs Centralizados**: Integración nativa con `journalctl`.
- **Persistencia**: Si el servidor está apagado a la hora programada, se ejecuta al arrancar (`Persistent=true`).
- **Gestión de Recursos**: Control preciso del entorno de ejecución y usuario.

---

## 1. Definición del Servicio (`.service`)

Este archivo describe cómo ejecutar el script de similitud. No tiene programación horaria, solo sabe *cómo* correr la tarea.

**Archivo:** `/etc/systemd/system/farmacruz-similarity.service`

```ini
[Unit]
Description=FarmaCruz Product Similarity Engine
# Se inicia después de que la red esté lista para evitar errores de conexión
After=network.target

[Service]
# Type=oneshot es ideal para scripts que se ejecutan y terminan (no demonios)
Type=oneshot
User=ec2-user
Group=nginx

# Directorio de trabajo y variables de entorno
WorkingDirectory=/home/ec2-user/farmacruz-ecomerce/backend
Environment="PATH=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin"
Environment="PYTHONPATH=/home/ec2-user/farmacruz-ecomerce/backend"

# Comando para ejecutar el script
ExecStart=/home/ec2-user/farmacruz-ecomerce/backend/venv/bin/python3 farmacruz_api/utils/product_similarity.py

[Install]
WantedBy=multi-user.target
```

---

## 2. Definición del Timer (`.timer`)

Este archivo controla la ejecución periódica del servicio definido anteriormente.

**Archivo:** `/etc/systemd/system/farmacruz-similarity.timer`

```ini
[Unit]
Description=Run Product Similarity nightly at 3AM

[Timer]
# Ejecutar cada día a las 03:00:00 AM
OnCalendar=*-*-* 03:00:00

# Si el servidor estaba apagado a esa hora, ejecutar inmediatamente al arrancar
Persistent=true

# Unidad a la que referencia este timer
Unit=farmacruz-similarity.service

[Install]
WantedBy=timers.target
```

---

## 🛠️ Instalación y Activación

Para instalar y activar el timer en el sistema, sigue estos pasos:

1.  **Crear los archivos**:
    ```bash
    sudo nano /etc/systemd/system/farmacruz-similarity.service
    sudo nano /etc/systemd/system/farmacruz-similarity.timer
    ```

2.  **Recargar el demonio de systemd**:
    Para que el sistema reconozca los nuevos archivos.
    ```bash
    sudo systemctl daemon-reload
    ```

3.  **Habilitar y arrancar el Timer**:
    ⚠️ **Nota**: Solo habilitamos el `.timer`, no el `.service`, ya que el timer es quien disparará el servicio.
    ```bash
    sudo systemctl enable --now farmacruz-similarity.timer
    ```

---

## 🔍 Monitoreo y Mantenimiento

Comandos útiles para verificar que todo funcione correctamente.

### Ver estado del Timer
Comprueba cuándo será la próxima ejecución y cuándo fue la última.
```bash
systemctl list-timers --all | grep farmacruz
```

### Ejecutar manualmente (Prueba)
Si necesitas forzar una ejecución inmediata (por ejemplo, después de un deploy o para testear).
```bash
sudo systemctl start farmacruz-similarity.service
```

### Ver Logs de Ejecución
Consulta la salida del script y posibles errores.
```bash
# Ver logs en tiempo real (si se está ejecutando)
sudo journalctl -u farmacruz-similarity.service -f

# Ver los últimos 50 registros
sudo journalctl -u farmacruz-similarity.service -n 50 --no-pager

# Ver logs solo de errores (prioridad err)
sudo journalctl -u farmacruz-similarity.service -p err
```
