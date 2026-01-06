"""
Script de Sincronización DBF -> FarmaCruz Backend

Este script lee archivos DBF de listas de precios, productos y relaciones
producto-lista, y los envía al backend en lotes (batches).

ORDEN DE EJECUCIÓN:
1. Sincronizar LISTAS DE PRECIOS (son los contenedores)
2. Sincronizar PRODUCTOS (items del catálogo)
3. Sincronizar RELACIONES PRODUCTO-LISTA (markups)

ARCHIVOS DBF REQUERIDOS:
- LISTAS.DBF: Listas de precios (ID, nombre, descripción)
- PRODUCTOS.DBF: Productos del catálogo (ID, SKU, nombre, precio, etc.)
- PRECIOLIS.DBF: Relación producto-lista con markup (lista_id, producto_id, markup%)

USO:
    python sync_dbf_to_backend.py

CONFIGURACIÓN:
    Modifica las rutas de los archivos DBF y la URL del backend según tu entorno.
"""

import pandas as pd
import requests
from dbfread import DBF
from pathlib import Path
from typing import List, Dict
import logging

# ===== CONFIGURACIÓN =====
BACKEND_URL = "http://localhost:8000/api/v1"
BATCH_SIZE = 100  # Registros a enviar por lote
CREDENTIALS = {
    "username": "farmacruz_admin",
    "password": "farmasaenz123"
}

# RUTAS DE ARCHIVOS DBF (ajustar según tu entorno)
DBF_LISTAS = Path(r"C:\Users\berna\Downloads\desarrollo\LISTAS.DBF")
DBF_PRODUCTOS = Path(r"C:\Users\berna\Downloads\desarrollo\PRODUCTOS.DBF")
DBF_PRECIOLIS = Path(r"C:\Users\berna\Downloads\desarrollo\PRECIOLIS.DBF")

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def login() -> str:
    """
    Autentica en el backend y obtiene el token JWT
    
    Returns:
        str: Token de acceso JWT
    """
    logger.info("🔐 Iniciando sesión...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            data=CREDENTIALS
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        logger.info("✅ Sesión iniciada correctamente")
        return token
    except Exception as e:
        logger.error(f"❌ Error de login: {e}")
        raise


def sync_price_lists(token: str) -> None:
    """
    Sincroniza listas de precios desde DBF
    
    Campos esperados en LISTAS.DBF:
    - CVE_LISTA (int): ID de la lista
    - NOM_LISTA (str): Nombre de la lista
    - DESCRIP (str): Descripción (opcional)
    - ACTIVA (bool): Si está activa (opcional, default True)
    """
    logger.info(f"\n📋 === SINCRONIZANDO LISTAS DE PRECIOS ===")
    
    if not DBF_LISTAS.exists():
        logger.warning(f"⚠️  Archivo no encontrado: {DBF_LISTAS}")
        return
    
    # Leer DBF
    logger.info(f"📖 Leyendo {DBF_LISTAS.name}...")
    try:
        df = pd.DataFrame(iter(DBF(DBF_LISTAS, encoding='latin-1')))
        df = df[df['CVE_LISTA'].notna()].copy()  # Filtrar registros válidos
        logger.info(f"📊 {len(df)} listas encontradas")
    except Exception as e:
        logger.error(f"❌ Error al leer DBF: {e}")
        return
    
    # Preparar datos
    listas = []
    for _, row in df.iterrows():
        lista = {
            "price_list_id": int(row['CVE_LISTA']),
            "list_name": str(row.get('NOM_LISTA', f'Lista {row["CVE_LISTA"]}')).strip(),
            "description": str(row.get('DESCRIP', '')).strip() or None,
            "is_active": bool(row.get('ACTIVA', True))
        }
        listas.append(lista)
    
    # Enviar en lotes
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    for i in range(0, len(listas), BATCH_SIZE):
        batch = listas[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/sync/price-lists",
                json=batch,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            total_created += result['created']
            total_updated += result['updated']
            total_errors += result['errors']
            
            logger.info(
                f"✅ Lote {batch_num}: {result['created']} creadas, "
                f"{result['updated']} actualizadas, {result['errors']} errores"
            )
            
            if result['error_details']:
                for error in result['error_details']:
                    logger.warning(f"   ⚠️  {error}")
                    
        except Exception as e:
            logger.error(f"❌ Error en lote {batch_num}: {e}")
            total_errors += len(batch)
    
    logger.info(
        f"\n📊 RESUMEN LISTAS: {total_created} creadas, "
        f"{total_updated} actualizadas, {total_errors} errores"
    )


def sync_products(token: str) -> None:
    """
    Sincroniza productos desde DBF
    
    Campos esperados en PRODUCTOS.DBF:
    - CVE_ART (int): ID del producto
    - CLAVE (str): SKU del producto
    - DESCR (str): Nombre/descripción
    - PRECIO (float): Precio base
    - IVA (float): % de IVA (0-100)
    - EXISTEN (int): Stock disponible
    - STATUS (str): 'A' = Activo, 'I' = Inactivo
    - CVE_CATEG (int): ID de categoría (opcional)
    """
    logger.info(f"\n📦 === SINCRONIZANDO PRODUCTOS ===")
    
    if not DBF_PRODUCTOS.exists():
        logger.warning(f"⚠️  Archivo no encontrado: {DBF_PRODUCTOS}")
        return
    
    # Leer DBF
    logger.info(f"📖 Leyendo {DBF_PRODUCTOS.name}...")
    try:
        df = pd.DataFrame(iter(DBF(DBF_PRODUCTOS, encoding='latin-1')))
        df = df[df['CVE_ART'].notna()].copy()
        logger.info(f"📊 {len(df)} productos encontrados")
    except Exception as e:
        logger.error(f"❌ Error al leer DBF: {e}")
        return
    
    # Preparar datos
    productos = []
    for _, row in df.iterrows():
        producto = {
            "product_id": int(row['CVE_ART']),
            "sku": str(row.get('CLAVE', f'SKU{row["CVE_ART"]}')).strip(),
            "name": str(row.get('DESCR', 'Producto sin nombre')).strip()[:255],
            "description": str(row.get('DESCRIP', '')).strip() or None,
            "base_price": float(row.get('PRECIO', 0.0)),
            "iva_percentage": float(row.get('IVA', 16.0)),
            "stock_count": int(row.get('EXISTEN', 0)),
            "is_active": str(row.get('STATUS', 'A')).upper() == 'A',
            "category_id": int(row['CVE_CATEG']) if row.get('CVE_CATEG') else None,
            "image_url": None  # No disponible en DBF
        }
        productos.append(producto)
    
    # Enviar en lotes
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    for i in range(0, len(productos), BATCH_SIZE):
        batch = productos[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/sync/products",
                json=batch,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()
            
            total_created += result['created']
            total_updated += result['updated']
            total_errors += result['errors']
            
            logger.info(
                f"✅ Lote {batch_num}: {result['created']} creados, "
                f"{result['updated']} actualizados, {result['errors']} errores"
            )
            
            if result['error_details']:
                for error in result['error_details'][:5]:  # Mostrar máximo 5 errores
                    logger.warning(f"   ⚠️  {error}")
                if len(result['error_details']) > 5:
                    logger.warning(f"   ... y {len(result['error_details']) - 5} errores más")
                    
        except Exception as e:
            logger.error(f"❌ Error en lote {batch_num}: {e}")
            total_errors += len(batch)
    
    logger.info(
        f"\n📊 RESUMEN PRODUCTOS: {total_created} creados, "
        f"{total_updated} actualizados, {total_errors} errores"
    )


def sync_price_list_items(token: str) -> None:
    """
    Sincroniza relaciones producto-lista con markups desde DBF
    
    Campos esperados en PRECIOLIS.DBF:
    - CVE_LISTA (int): ID de la lista de precios
    - CVE_ART (int): ID del producto
    - MARGEN (float): % de markup/margen (0-100)
    """
    logger.info(f"\n💰 === SINCRONIZANDO RELACIONES PRODUCTO-LISTA ===")
    
    if not DBF_PRECIOLIS.exists():
        logger.warning(f"⚠️  Archivo no encontrado: {DBF_PRECIOLIS}")
        return
    
    # Leer DBF
    logger.info(f"📖 Leyendo {DBF_PRECIOLIS.name}...")
    try:
        df = pd.DataFrame(iter(DBF(DBF_PRECIOLIS, encoding='latin-1')))
        df = df[df['CVE_LISTA'].notna() & df['CVE_ART'].notna()].copy()
        logger.info(f"📊 {len(df)} relaciones encontradas")
    except Exception as e:
        logger.error(f"❌ Error al leer DBF: {e}")
        return
    
    # Agrupar por lista de precios
    grouped = df.groupby('CVE_LISTA')
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    for lista_id, group in grouped:
        # Preparar items para esta lista
        items = []
        for _, row in group.iterrows():
            item = {
                "product_id": int(row['CVE_ART']),
                "markup_percentage": float(row.get('MARGEN', 0.0))
            }
            items.append(item)
        
        # Enviar en lotes por lista
        for i in range(0, len(items), BATCH_SIZE):
            batch_items = items[i : i + BATCH_SIZE]
            
            payload = {
                "price_list_id": int(lista_id),
                "items": batch_items
            }
            
            try:
                response = requests.post(
                    f"{BACKEND_URL}/sync/price-list-items",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                result = response.json()
                
                total_created += result['created']
                total_updated += result['updated']
                total_errors += result['errors']
                
                logger.info(
                    f"✅ Lista {lista_id} - Lote: {result['created']} creados, "
                    f"{result['updated']} actualizados, {result['errors']} errores"
                )
                
                if result['error_details']:
                    for error in result['error_details'][:3]:
                        logger.warning(f"   ⚠️  {error}")
                        
            except Exception as e:
                logger.error(f"❌ Error en lista {lista_id}: {e}")
                total_errors += len(batch_items)
    
    logger.info(
        f"\n📊 RESUMEN RELACIONES: {total_created} creadas, "
        f"{total_updated} actualizadas, {total_errors} errores"
    )


def main():
    """Función principal de sincronización"""
    logger.info("🚀 === INICIANDO SINCRONIZACIÓN DBF -> FARMACRUZ ===\n")
    
    try:
        # 1. Login
        token = login()
        
        # 2. Sincronizar en orden (importante el orden!)
        sync_price_lists(token)
        sync_products(token)
        sync_price_list_items(token)
        
        logger.info("\n✨ === SINCRONIZACIÓN COMPLETADA ===")
        
    except Exception as e:
        logger.error(f"\n❌ Error fatal en sincronización: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
