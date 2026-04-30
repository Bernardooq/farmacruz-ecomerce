#!/bin/bash
# ============================================================================
# FarmaCruz - Script de Despliegue Automatizado
# ============================================================================
set -e

# Configuración de rutas
REPO_DIR="/home/ec2-user/farmacruz-ecomerce"
BACKEND_DIR="$REPO_DIR/backend"

echo "--------------------------------------------------"
echo "[$(date)] Iniciando despliegue automatizado..."
echo "--------------------------------------------------"

# 1. Navegar al repositorio
cd $REPO_DIR

# 2. Sincronizar con GitHub
# Limpiamos cualquier cambio local y traemos lo nuevo
echo "Bajando cambios de GitHub..."
git fetch origin main
git reset --hard origin main

# 3. Actualizar entorno virtual del Backend
echo "Actualizando dependencias de Python..."
if [ -d "$BACKEND_DIR/venv" ]; then
    source $BACKEND_DIR/venv/bin/activate
    pip install -r $BACKEND_DIR/requirements.txt --quiet
else
    echo "Venv no encontrado en $BACKEND_DIR/venv. ¿Es la primera vez?"
fi

# 4. Recargar y reiniciar servicios
echo "Reiniciando servicios de sistema..."
sudo systemctl daemon-reload
sudo systemctl restart farmacruz-api.service

# 5. Verificar estado
sleep 2
if systemctl is-active --quiet farmacruz-api.service; then
    echo "--------------------------------------------------"
    echo "[$(date)] Despliegue completado con éxito."
    echo "--------------------------------------------------"
else
    echo "[$(date)] ERROR: El servicio farmacruz-api no inició correctamente."
    sudo journalctl -u farmacruz-api.service -n 20 --no-pager
    exit 1
fi
