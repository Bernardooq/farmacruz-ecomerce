# Guía de Monitoreo y Control - Servicios Systemd

## Comandos Esenciales de Servicios

### Ver Estado Actual
```bash
# Backend API
sudo systemctl status farmacruz-api

# Nginx
sudo systemctl status nginx

# Todos los servicios activos
systemctl list-units --type=service --state=running
```

### Controlar Servicios

#### 🚀 Iniciar
```bash
sudo systemctl start farmacruz-api
sudo systemctl start nginx
```

#### 🛑 Detener
```bash
sudo systemctl stop farmacruz-api
sudo systemctl stop nginx
```

#### 🔄 Reiniciar (detiene y vuelve a iniciar)
```bash
sudo systemctl restart farmacruz-api
sudo systemctl restart nginx
```

#### ⚡ Reload (sin downtime - solo config)
```bash
# Solo Nginx soporta reload
sudo systemctl reload nginx

# Para farmacruz-api debes usar restart
sudo systemctl restart farmacruz-api
```

### Habilitar/Deshabilitar Auto-Start

#### Habilitar (iniciar automáticamente en boot)
```bash
sudo systemctl enable farmacruz-api
sudo systemctl enable nginx
```

#### Deshabilitar (NO iniciar en boot)
```bash
sudo systemctl disable farmacruz-api
sudo systemctl disable nginx
```

#### Verificar si está habilitado
```bash
sudo systemctl is-enabled farmacruz-api
sudo systemctl is-enabled nginx
```

---

## Logs y Monitoreo

### Ver Logs de Backend (journalctl)

#### Últimos logs
```bash
# Últimas 50 líneas
sudo journalctl -u farmacruz-api -n 50

# Últimas 200 líneas sin paginado
sudo journalctl -u farmacruz-api -n 200 --no-pager
```

#### Logs en tiempo real
```bash
# Modo "tail -f" (seguir logs)
sudo journalctl -u farmacruz-api -f

# Presionar Ctrl+C para salir
```

#### Filtrar por tiempo
```bash
# Última hora
sudo journalctl -u farmacruz-api --since "1 hour ago"

# Últimas 2 horas
sudo journalctl -u farmacruz-api --since "2 hours ago"

# Desde hoy
sudo journalctl -u farmacruz-api --since today

# Desde ayer
sudo journalctl -u farmacruz-api --since yesterday

# Fecha específica
sudo journalctl -u farmacruz-api --since "2026-02-08 10:00:00"
```

#### Filtrar por severidad
```bash
# Solo errores
sudo journalctl -u farmacruz-api -p err

# Errores y warnings
sudo journalctl -u farmacruz-api -p warning

# Todo excepto debug
sudo journalctl -u farmacruz-api -p info
```

### Ver Logs de Nginx

#### Access logs (peticiones)
```bash
# En tiempo real
sudo tail -f /var/log/nginx/access.log

# Últimas 100 líneas
sudo tail -n 100 /var/log/nginx/access.log
```

#### Error logs
```bash
# En tiempo real
sudo tail -f /var/log/nginx/error.log

# Últimas 50 líneas
sudo tail -n 50 /var/log/nginx/error.log

# Buscar errores específicos
sudo grep "error" /var/log/nginx/error.log | tail -n 20
```

---

## Monitoreo de Recursos

### Verificar Puertos
```bash
# Ver qué proceso usa puerto 8000
sudo netstat -tlnp | grep :8000

# Ver todos los puertos en uso
sudo netstat -tlnp

# Alternativa moderna (si tienes ss)
sudo ss -tlnp | grep :8000
```

### Monitoreo de Procesos
```bash
# Procesos de Python (backend)
ps aux | grep python

# Procesos de Nginx
ps aux | grep nginx

# Ver árbol de procesos
pstree -p | grep farmacruz
```

### Uso de Recursos
```bash
# Vista interactiva (CPU, RAM)
htop

# Presionar 'q' para salir

# Alternativa sin htop
top
```

### Memoria
```bash
# Vista human-readable
free -h

# Ver memoria en MB
free -m
```

### Disco
```bash
# Uso de disco
df -h

# Uso por directorio
du -sh ~/farmacruz-ecomerce/*
```

---

## Verificaciones de Salud

### Test de Conexión Backend
```bash
# Test local
curl http://127.0.0.1:8000/api/v1/health

# Test desde fuera (si tienes endpoint health)
curl https://digheqbxnmxr3.cloudfront.net/api/v1/health
```

### Test de Conexión RDS
```bash
# Conectar a RDS
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d farmacruz_db

# Test rápido (ejecutar query)
psql -h farmacruz.xxxxx.us-east-1.rds.amazonaws.com \
     -U farmacruz_user \
     -d farmacruz_db \
     -c "SELECT version();"
```

### Verificar Nginx Config
```bash
# Test de configuración (sin aplicar)
sudo nginx -t

# Si sale OK, aplicar cambios
sudo systemctl reload nginx
```

---

## Troubleshooting Rápido

### Backend crasheó
```bash
# 1. Ver últimos errores
sudo journalctl -u farmacruz-api -n 100 --no-pager | tail -n 50

# 2. Verificar que RDS esté accesible
psql -h RDS_ENDPOINT -U farmacruz_user -d farmacruz_db -c "SELECT 1"

# 3. Reiniciar
sudo systemctl restart farmacruz-api

# 4. Ver si arrancó
sudo systemctl status farmacruz-api
```

### Nginx devuelve 502 Bad Gateway
```bash
# 1. Verificar backend activo
sudo systemctl status farmacruz-api

# 2. Ver logs de nginx
sudo tail -f /var/log/nginx/error.log

# 3. Test directo al backend
curl http://127.0.0.1:8000/api/v1/health

# 4. Reiniciar ambos
sudo systemctl restart farmacruz-api
sudo systemctl restart nginx
```

### Logs llenando disco
```bash
# Ver tamaño de logs
sudo journalctl --disk-usage

# Limpiar logs mayores a 7 días
sudo journalctl --vacuum-time=7d

# Limpiar manteniendo solo 500MB
sudo journalctl --vacuum-size=500M
```

---

## Comandos de Emergencia

### Reinicio Completo
```bash
# Reiniciar todos los servicios
sudo systemctl restart farmacruz-api nginx

# Ver estado de todo
sudo systemctl status farmacruz-api nginx
```

### Ver Todos los Errores Recientes
```bash
# Últimos 50 errores del sistema
sudo journalctl -p err -n 50 --no-pager

# Errores de hoy
sudo journalctl -p err --since today
```

### Recargar Configuración de Systemd
```bash
# Después de editar archivos .service
sudo systemctl daemon-reload
```

---

## Atajos Útiles

```bash
# Alias útil (agregar a ~/.bashrc)
alias logs-api='sudo journalctl -u farmacruz-api -f'
alias logs-nginx='sudo tail -f /var/log/nginx/error.log'
alias status-all='sudo systemctl status farmacruz-api nginx'
alias restart-all='sudo systemctl restart farmacruz-api nginx'
```

**Aplicar aliases:**
```bash
echo "alias logs-api='sudo journalctl -u farmacruz-api -f'" >> ~/.bashrc
echo "alias logs-nginx='sudo tail -f /var/log/nginx/error.log'" >> ~/.bashrc
source ~/.bashrc
```
