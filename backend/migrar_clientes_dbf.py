"""
Script de Migración de Clientes desde DBF

Este script es una migración ONE-TIME (una sola vez) o ejecutar manualmente
cuando se necesite sincronizar clientes desde el archivo DBF.

A diferencia de productos y listas que requieren sincronización frecuente,
los clientes usualmente se agregan de forma esporádica.

ARCHIVO DBF REQUERIDO:
- CLIENTES.DBF: Datos de clientes (ID, nombre, RFC, dirección, etc.)

USO:
    python migrar_clientes_dbf.py

NOTA: Este script está basado en tu script original pero adaptado
      para usar el endpoint batch de customers (si existe) o individual.
"""

import pandas as pd
import requests
from dbfread import DBF
from pathlib import Path
import logging

# ===== CONFIGURACIÓN =====
BACKEND_URL = "http://localhost:8000/api/v1"
DBF_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")

DBF_PATH = DBF_DIR / "clientes.dbf"
BATCH_SIZE = 50  # Clientes a enviar cada llamada
CREDENTIALS = {
    "username": "admin",
    "password": "farmasaenz123"
}

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def migrate():
    """
    Migra clientes desde DBF al backend
    
    Campos esperados en CLIENTES.DBF:
    - CVE_CTE (int): ID del cliente
    - NOM_CTE (str): Nombre completo
    - NOM_FAC (str): Razón social (opcional, usa NOM_CTE si no existe)
    - RFC_CTE (str): RFC del cliente
    - DIR_CTE (str): Dirección principal
    - LISTA_PREC (int): ID de lista de precios asignada
    """
    logger.info("🚀 === INICIANDO MIGRACIÓN DE CLIENTES ===\n")
    
    # === 1. LOGIN ===
    logger.info("🔐 Iniciando sesión...")
    try:
        res_login = requests.post(
            f"{BACKEND_URL}/auth/login",
            data=CREDENTIALS
        )
        res_login.raise_for_status()
        token = res_login.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        logger.info("✅ Sesión iniciada correctamente")
    except Exception as e:
        logger.error(f"❌ Error de login: {e}")
        return 1

    # === 2. LEER DBF ===
    logger.info(f"\n📖 Leyendo {DBF_PATH.name}...")
    
    if not DBF_PATH.exists():
        logger.error(f"❌ Archivo no encontrado: {DBF_PATH}")
        return 1
    
    try:
        df = pd.DataFrame(iter(DBF(DBF_PATH, encoding='latin-1', ignore_missing_memofile=True)))
        df = df[df['CVE_CTE'].notna()].copy()
        logger.info(f"📊 {len(df)} clientes encontrados")
    except Exception as e:
        logger.error(f"❌ Error al leer DBF: {e}")
        return 1

    # === 3. PREPARAR DATOS ===
    logger.info(f"\n🔄 Preparando datos de clientes...")
    lista_clientes = []
    
    for _, row in df.iterrows():
        try:
            # Crear username único y válido
            base_username = str(row.get('NOM_CTE', 'user')).strip()[:50]
            username = base_username.replace(" ", "_").replace(".", "_").lower()
            
            # Construir objeto cliente
            cliente = {
                "customer_id": int(row['CVE_CTE']),
                "username": username or f"cliente_{row['CVE_CTE']}",
                "email": f"cliente{row['CVE_CTE']}@farmacruz.com",
                "full_name": str(row.get('NOM_CTE', 'N/A')).strip(),
                "password": "FarmaCruz2024!",  # Contraseña temporal
                "is_active": True,
                "info": {
                    "business_name": str(row.get('NOM_FAC', row.get('NOM_CTE', ''))).strip(),
                    "rfc": str(row.get('RFC_CTE', ''))[:13] or None,
                    "price_list_id": int(float(row['LISTA_PREC'])) if row.get('LISTA_PREC') else None,
                    "address_1": str(row.get('DIR_CTE', '')) or None,
                    "address_2": None,  # No disponible en DBF
                    "address_3": None,  # No disponible en DBF
                    "sales_group_id": None  # Se asigna manualmente después
                }
            }
            lista_clientes.append(cliente)
            
        except Exception as e:
            logger.warning(f"⚠️  Error preparando cliente ID {row.get('CVE_CTE', 'N/A')}: {e}")
            continue
        
         
    logger.info(f"✅ {len(lista_clientes)} clientes preparados correctamente")

    # === 4. ENVIAR AL BACKEND ===
    logger.info(f"\n📤 Enviando clientes al backend en lotes de {BATCH_SIZE}...")
    
    total_exitosos = 0
    total_errores = 0
    
    for i in range(0, len(lista_clientes), BATCH_SIZE):
        batch = lista_clientes[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        # Usar endpoint de sincronización /sync/customers
        try:
            # Preparar datos en formato CustomerSync
            batch_sync = []
            for cliente in batch:
                cliente_sync = {
                    "customer_id": cliente["customer_id"],
                    "username": cliente["username"],
                    "email": cliente["email"],
                    "full_name": cliente["full_name"],
                    "password": cliente["password"],
                    "business_name": cliente["info"]["business_name"],
                    "rfc": cliente["info"]["rfc"],
                    "price_list_id": cliente["info"]["price_list_id"],
                    "sales_group_id": cliente["info"]["sales_group_id"],
                    "address_1": cliente["info"]["address_1"],
                    "address_2": cliente["info"]["address_2"],
                    "address_3": cliente["info"]["address_3"]
                }
                batch_sync.append(cliente_sync)
            
            # Enviar al endpoint de sincronización
            response = requests.post(
                f"{BACKEND_URL}/sync/customers",
                json=batch_sync,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            # Procesar resultado
            total_exitosos += result.get('creados', 0) + result.get('actualizados', 0)
            total_errores += result.get('errores', 0)
            logger.info(
                f"✅ Lote {batch_num}: {result.get('creados', 0)} creados, "
                f"{result.get('actualizados', 0)} actualizados, {result.get('errores', 0)} errores"
            )
            
            # Mostrar primeros errores si los hay
            if result.get('detalle_errores'):
                for error in result.get('detalle_errores', [])[:3]:
                    logger.warning(f"   ⚠️  {error}")
                    
        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ Error HTTP en lote {batch_num}: {e}")
            logger.error(f"   Respuesta: {e.response.text[:200]}")
            total_errores += len(batch)
        except Exception as e:
            logger.error(f"❌ Error en lote {batch_num}: {e}")
            total_errores += len(batch)

    # === 5. RESUMEN ===
    logger.info(f"\n{'='*60}")
    logger.info(f"✨ MIGRACIÓN COMPLETADA")
    logger.info(f"{'='*60}")
    logger.info(f"📊 Total procesados: {len(lista_clientes)}")
    logger.info(f"✅ Exitosos: {total_exitosos}")
    logger.info(f"❌ Errores: {total_errores}")
    logger.info(f"{'='*60}\n")
    
    if total_errores > 0:
        logger.warning(
            "⚠️  Algunos clientes tuvieron errores. "
            "Revisa los logs arriba para más detalles."
        )
    
    return 0 if total_errores == 0 else 1


if __name__ == "__main__":
    exit(migrate())
