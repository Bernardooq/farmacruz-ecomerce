"""
Script para sincronizar agentes/vendedores desde DBF al backend

Este script:
1. Lee la tabla de agentes del DBF (ajustar nombre segun DBF real)
2. Crea usuarios de tipo 'seller' con IDs especificos del DBF
3. Actualiza los clientes para vincularlos con sus agentes

NOTA: Ajustar los nombres de campos y tablas segun el DBF real.
"""

import pandas as pd
import requests
from dbfread import DBF
from pathlib import Path
import logging

# ===== CONFIG =====
BACKEND_URL = "http://localhost:8000/api/v1"
CREDENTIALS = {"username": "admin", "password": "farmasaenz123"}

# AJUSTAR ESTOS PATHS SEGUN TU DBF
DBF_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")
DBF_AGENTES = DBF_DIR / "agentes.dbf"  # CAMBIAR POR EL NOMBRE REAL
DBF_CLIENTES = DBF_DIR / "clientes.dbf"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===== UTILIDADES =====
def clean_str(val):
    if val is None:
        return ""
    return str(val).strip()

def clean_numeric(val, default=0):
    try:
        return int(str(val).replace(",", ""))
    except:
        return default

# ===== LOGIN =====
def login() -> str:
    logger.info("Iniciando sesion en el backend...")
    resp = requests.post(f"{BACKEND_URL}/auth/login", data=CREDENTIALS)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Sesion iniciada correctamente")
    return token

# ===== SINCRONIZAR AGENTES =====
def sync_agents(token):
    """
    Sincroniza agentes desde DBF creando usuarios de tipo seller
    
    NOTA: Ajustar nombres de campos segun el DBF real.
    Campos esperados en DBF de agentes:
    - ID o CVE_AGENTE: ID numerico del agente
    - NOMBRE: Nombre del agente
    - EMAIL: Email (opcional)
    """
    logger.info(f"Leyendo agentes desde {DBF_AGENTES}...")
    
    try:
        df_agentes = pd.DataFrame(iter(DBF(DBF_AGENTES, encoding="latin-1", ignore_missing_memofile=True)))
    except FileNotFoundError:
        logger.error(f"Archivo {DBF_AGENTES} no encontrado. Ajusta DBF_AGENTES en el script.")
        return
    except Exception as e:
        logger.error(f"Error al leer DBF de agentes: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    for _, row in df_agentes.iterrows():
        # AJUSTAR ESTOS NOMBRES DE CAMPOS
        agent_id = clean_numeric(row.get('ID') or row.get('CVE_AGENTE'))  # Ajustar nombre del campo
        agent_name = clean_str(row.get('NOMBRE') or row.get('DESC_AGENTE'))  # Ajustar
        agent_email = clean_str(row.get('EMAIL'))  # Opcional
        
        if not agent_id or not agent_name:
            continue
        
        # Crear username basado en ID
        username = f"agente_{agent_id}"
        email = agent_email if agent_email else f"{username}@farmacruz.local"
        
        # Payload para crear usuario seller
        user_payload = {
            "user_id": agent_id,  # ID manual del DBF
            "username": username,
            "email": email,
            "full_name": agent_name,
            "password": "Agente123!",  # Password por defecto, cambiar despues
            "role": "seller",
            "is_active": True
        }
        
        try:
            # Intentar crear el usuario
            resp = requests.post(
                f"{BACKEND_URL}/admin/users",
                json=user_payload,
                headers=headers
            )
            
            if resp.status_code == 201:
                logger.info(f"✓ Agente creado: ID={agent_id}, nombre={agent_name}")
            elif resp.status_code == 400 and "ya existe" in resp.text:
                logger.info(f"- Agente ya existe: ID={agent_id}")
            else:
                logger.warning(f"✗ Error creando agente ID={agent_id}: {resp.text}")
        
        except Exception as e:
            logger.error(f"✗ Exception creando agente ID={agent_id}: {e}")

# ===== VINCULAR CLIENTES CON AGENTES =====
def link_customers_to_agents(token):
    """
    Actualiza clientes para vincularlos con sus agentes
    
    NOTA: Ajustar nombres de campos segun el DBF real.
    Campo esperado en DBF de clientes:
    - AGENTE o CVE_AGENTE: ID del agente asignado
    """
    logger.info(f"Vinculando clientes con agentes...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    try:
        df_clientes = pd.DataFrame(iter(DBF(DBF_CLIENTES, encoding="latin-1", ignore_missing_memofile=True)))
    except Exception as e:
        logger.error(f"Error leyendo clientes DBF: {e}")
        return
    
    for _, row in df_clientes.iterrows():
        # AJUSTAR ESTOS NOMBRES DE CAMPOS
        customer_id = clean_numeric(row.get('ID') or row.get('CVE_CLIENT'))
        agent_id = clean_numeric(row.get('AGENTE') or row.get('CVE_AGENTE'))
        
        if not customer_id or not agent_id:
            continue
        
        # Actualizar customer con agent_id
        # NOTA: Necesitas crear un endpoint en el backend para esto
        # o usar un endpoint existente que permita actualizar agent_id
        
        logger.info(f"Cliente {customer_id} → Agente {agent_id}")
        
        # EJEMPLO (ajustar segun tu API):
        # update_payload = {"agent_id": agent_id}
        # resp = requests.patch(
        #     f"{BACKEND_URL}/customers/{customer_id}",
        #     json=update_payload,
        #     headers=headers
        # )

# ===== MAIN =====
def main():
    logger.info("INICIANDO SINCRONIZACIoN DE AGENTES")
    token = login()
    
    # Paso 1: Crear usuarios sellers desde agentes DBF
    sync_agents(token)
    
    # Paso 2: Vincular clientes con agentes
    # link_customers_to_agents(token)
    # DESCOMENTAR cuando tengas el endpoint de actualizacion
    
    logger.info("SINCRONIZACIoN COMPLETA")

if __name__ == "__main__":
    main()
