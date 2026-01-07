"""
Script de Sincronización DBF -> FarmaCruz Backend (simulado)

Este script lee archivos DBF de listas de precios, productos y relaciones
producto-lista, y muestra cómo se prepararían los payloads por lotes
(batches) sin enviarlos al backend.
"""

import pandas as pd
from dbfread import DBF
from pathlib import Path
import logging

# ===== CONFIG =====
BATCH_SIZE_CAT = 100
BATCH_SIZE_PROD = 100
BATCH_SIZE_LIST = 100  
BATCH_SIZE_RELATIONS = 100  

DBF_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")

# Archivos DBF
DBF_PRODUCTOS = DBF_DIR / "producto.dbf"
DBF_PRECIOLIS = DBF_DIR / "PRECIPROD.DBF"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===== SINCRONIZAR CATEGORÍAS =====
def sync_categories_from_products(df_productos: pd.DataFrame):
    logger.info("Extrayendo categorías únicas de productos...")
    categorias_unicas = df_productos['CSE_PROD'].dropna().unique()
    categorias_unicas = [str(cat).strip() for cat in categorias_unicas if str(cat).strip()]
    
    
    categorias_payload = [{"name": cat, "description": None} for cat in categorias_unicas]

    for i in range(0, len(categorias_payload), BATCH_SIZE_CAT):
        batch = categorias_payload[i:i+BATCH_SIZE_CAT]
        logger.info(f"Ejemplo batch de categorías ({i}-{i+len(batch)}): {batch[:3]}...")  # solo los primeros 3 para no saturar

# ===== SINCRONIZAR PRODUCTOS =====
def sync_products(df_productos: pd.DataFrame):
    logger.info("Preparando productos para sincronización...")
    productos_payload = []

    for _, row in df_productos.iterrows():
        descripcion = ""
        if row.get('FACT_PESO'): descripcion += f" | Peso: {row['FACT_PESO']}"
        if row.get('DATO_4'): descripcion += f" | Unidad: {row['DATO_4']}"
        descripcion = descripcion or None

        try:
            stock_count = int(float(str(row.get('DATO_1', 0)).replace(',', '')))
        except:
            stock_count = 10

        producto = {
            "product_id": str(row['CVE_PROD']).strip(),
            "codebar": str(row.get('CODBAR', '')).strip(),
            "name": str(row.get('DESC_PROD', 'Producto sin nombre')).strip()[:255],
            "description": descripcion,
            "base_price": float(row.get('CTO_ENT', 0.0)),
            "iva_percentage": float(row.get('PORCENIVA', 16.0)),
            "stock_count": stock_count,
            "category_name": str(row.get('CVE_PROD', '')).strip() or None,
            "is_active": True,
            "image_url": None
        }
        productos_payload.append(producto)

    logger.info(f"Head de productos_payload:\n{productos_payload[:3]}")  # primeros 3 productos

    for i in range(0, len(productos_payload), BATCH_SIZE_PROD):
        batch = productos_payload[i:i+BATCH_SIZE_PROD]
        logger.info(f"Ejemplo batch de productos ({i}-{i+len(batch)}): {batch[:3]}...")  # solo los primeros 3

# ===== SINCRONIZAR LISTAS =====
def sync_price_lists(df_preciprod: pd.DataFrame):
    logger.info("Preparando listas de precios...")
    listas_unicas = df_preciprod['NLISPRE'].dropna().unique()
    listas_payload = [{"price_list_id": int(lista), "name": f"Lista {lista}", "description": None} for lista in listas_unicas]
    
    logger.info(f"Head de df_preciprod:\n{df_preciprod.head()}")
    
    for i in range(0, len(listas_payload), BATCH_SIZE_LIST):
        batch = listas_payload[i:i+BATCH_SIZE_LIST]
        logger.info(f"Ejemplo batch de listas ({i}-{i+len(batch)}): {batch[:3]}...")  # primeros 3

# ===== SINCRONIZAR RELACIONES PRODUCTO-LISTA =====
def sync_price_list_items(df_preciprod: pd.DataFrame):
    logger.info("💰 Preparando relaciones producto-lista...")
    grouped = df_preciprod.groupby('NLISPRE')

    for lista_id, group in grouped:
        items = [{"product_id": str(r['CVE_PROD']), "markup_percentage": float(r.get('LMARGEN', 0.0))} for _, r in group.iterrows()]
        for i in range(0, len(items), BATCH_SIZE_RELATIONS):
            batch_items = items[i:i+BATCH_SIZE_RELATIONS]
            payload = {"price_list_id": int(lista_id), "items": batch_items}
            logger.info(f"Ejemplo batch de relaciones lista {lista_id} ({i}-{i+len(batch_items)}): {batch_items[:3]}...")  # primeros 3

# ===== MAIN =====
def main():
    logger.info("INICIANDO SIMULACIÓN DE SINCRONIZACIÓN DBF -> FARMACRUZ")
    
    # Leer DBF productos
    df_productos = pd.DataFrame(iter(DBF(DBF_PRODUCTOS, encoding="latin-1")))
    df_preciprod = pd.DataFrame(iter(DBF(DBF_PRECIOLIS, encoding="latin-1")))

    # Simular sincronización
    sync_categories_from_products(df_productos)
    sync_products(df_productos)
    sync_price_lists(df_preciprod)
    sync_price_list_items(df_preciprod)

    logger.info("✨ SIMULACIÓN COMPLETADA ✅")

if __name__ == "__main__":
    main()