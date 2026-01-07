"""
Sincronización DBF -> FarmaCruz Backend
Procesa DBF grandes en batches y sincroniza categorías, productos,
listas de precios y relaciones producto-lista.
"""

import pandas as pd
import requests
from dbfread import DBF
from pathlib import Path
import logging

# ===== CONFIG =====
BACKEND_URL = "http://localhost:8000/api/v1"
BATCH_SIZE_CAT = 100
BATCH_SIZE_PROD = 100
BATCH_SIZE_LIST = 100
BATCH_SIZE_RELATIONS = 100
CREDENTIALS = {"username": "admin", "password": "farmasaenz123"}

DBF_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")
DBF_PRODUCTOS = DBF_DIR / "producto.dbf"
DBF_PRECIOLIS = DBF_DIR / "PRECIPROD.DBF"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ===== UTILIDADES =====
def clean_str(val):
    if val is None:
        return ""
    return str(val).strip()

def clean_numeric(val, default=0.0):
    try:
        return float(str(val).replace(",", ""))
    except:
        return default

# ===== LOGIN =====
def login() -> str:
    logger.info("Iniciando sesión en el backend...")
    resp = requests.post(f"{BACKEND_URL}/auth/login", data=CREDENTIALS)
    resp.raise_for_status()
    token = resp.json()["access_token"]
    logger.info("Sesión iniciada correctamente")
    return token

# ===== ENVÍO EN BATCHES =====
def send_in_batches(payload_list, batch_size, endpoint, token, entity_name):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created, total_updated, total_errors = 0, 0, 0

    for i in range(0, len(payload_list), batch_size):
        batch = payload_list[i:i+batch_size]
        try:
            resp = requests.post(f"{BACKEND_URL}/{endpoint}", json=batch, headers=headers)
            resp.raise_for_status()
            res = resp.json()
            total_created += res.get('creados',0)
            total_updated += res.get('actualizados',0)
            total_errors += res.get('errores',0)
            logger.info(f"{entity_name} - Lote {i+1}-{i+len(batch)}: {res.get('creados',0)} creados, {res.get('actualizados',0)} actualizados, {res.get('errores',0)} errores")
            
            # Mostrar primeros 5 errores si los hay
            if res.get('errores', 0) > 0 and res.get('detalle_errores'):
                logger.warning(f"{entity_name} - Primeros errores del lote:")
                for error_msg in res.get('detalle_errores', [])[:5]:
                    logger.warning(f"  → {error_msg}")
                    
        except Exception as e:
            logger.error(f"{entity_name} - Error lote {i+1}-{i+len(batch)}: {e}")
            total_errors += len(batch)

    logger.info(f"{entity_name} - RESUMEN TOTAL: {total_created} creados, {total_updated} actualizados, {total_errors} errores")

# ===== SINCRONIZAR CATEGORÍAS =====
def sync_categories(df_productos, token):
    logger.info("Extrayendo categorías únicas de productos...")
    categorias_unicas = df_productos['CSE_PROD'].dropna().apply(clean_str).unique()
    
    # FILTRAR: Excluir GASTOS y 99999
    categorias_unicas = [cat for cat in categorias_unicas if cat and cat.upper() != 'GASTOS' and cat != '99999']
    
    categorias_payload = [{"name": cat, "description": None} for cat in categorias_unicas]
    send_in_batches(categorias_payload, BATCH_SIZE_CAT, "sync/categories", token, "Categorías")

# ===== SINCRONIZAR PRODUCTOS =====
def sync_products(df_productos, token):
    logger.info("Preparando productos...")
    productos_payload = []

    for _, row in df_productos.iterrows():
        # FILTRAR: Excluir productos de categorías GASTOS y 99999
        categoria = clean_str(row.get('CSE_PROD'))
        if categoria.upper() == 'GASTOS' or categoria == '99999':
            continue  # Saltar este producto
        
        descripcion = " | ".join(filter(None, [
            f"Peso: {clean_str(row.get('FACT_PESO'))}" if row.get('FACT_PESO') else None,
            f"Unidad: {clean_str(row.get('DATO_4'))}" if row.get('DATO_4') else None
        ])) or None

        stock_count = int(clean_numeric(row.get('DATO_1'), 10))
        
        # Convertir codebar vacío a None para evitar violación de unicidad
        codebar_value = clean_str(row.get('CODBAR'))
        if not codebar_value or codebar_value.strip() == "":
            codebar_value = None

        producto = {
            "product_id": clean_str(row.get('CVE_PROD')),
            "codebar": codebar_value,  # Ahora puede ser None
            "name": clean_str(row.get('DESC_PROD'))[:255] or "Producto sin nombre",
            "description": descripcion,
            "base_price": clean_numeric(row.get('CTO_ENT')),
            "iva_percentage": clean_numeric(row.get('PORCENIVA'), 16.0),
            "stock_count": stock_count,
            "category_name": categoria or None,
            "is_active": True,
            "image_url": None,
            "descripcion_2": None,
            "unidad_medida": clean_str(row.get('DATO_4')) or None
        }
        productos_payload.append(producto)

    send_in_batches(productos_payload, BATCH_SIZE_PROD, "sync/products", token, "Productos")

# ===== SINCRONIZAR LISTAS DE PRECIOS =====
def sync_price_lists(df_preciprod, token):
    logger.info("Preparando listas de precios...")
    listas_unicas = df_preciprod['NLISPRE'].dropna().apply(clean_str).unique()
    listas_payload = [
        {"price_list_id": int(clean_numeric(lista)), "list_name": f"Lista {lista}", "description": None, "is_active": True}
        for lista in listas_unicas if lista
    ]
    send_in_batches(listas_payload, BATCH_SIZE_LIST, "sync/price-lists", token, "Listas de precios")

# ===== SINCRONIZAR RELACIONES PRODUCTO-LISTA =====
def sync_price_list_items(df_preciprod, token):
    logger.info("Preparando relaciones producto-lista...")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created, total_updated, total_errors = 0,0,0

    grouped = df_preciprod.groupby('NLISPRE')
    for lista_id, group in grouped:
        items = [
            {"product_id": clean_str(r['CVE_PROD']), "markup_percentage": clean_numeric(r.get('LMARGEN',0))}
            for _, r in group.iterrows()
        ]

        # Enviar items de esta lista en batches
        for i in range(0, len(items), BATCH_SIZE_RELATIONS):
            batch_items = items[i:i+BATCH_SIZE_RELATIONS]
            batch_payload = {"price_list_id": int(clean_numeric(lista_id)), "items": batch_items}
            try:
                resp = requests.post(f"{BACKEND_URL}/sync/price-list-items", json=batch_payload, headers=headers)
                resp.raise_for_status()
                res = resp.json()
                total_created += res.get('creados',0)
                total_updated += res.get('actualizados',0)
                total_errors += res.get('errores',0)
                logger.info(f"Relaciones lista {lista_id} - Lote {i+1}-{i+len(batch_items)}: {res.get('creados',0)} creados, {res.get('actualizados',0)} actualizados, {res.get('errores',0)} errores")
            except Exception as e:
                logger.error(f"Relaciones lista {lista_id} - Error lote {i+1}-{i+len(batch_items)}: {e}")
                total_errors += len(batch_items)

    logger.info(f"Relaciones producto-lista - RESUMEN TOTAL: {total_created} creados, {total_updated} actualizados, {total_errors} errores")

# ===== MAIN =====
def main():
    logger.info("INICIANDO SINCRONIZACIÓN DBF -> FARMACRUZ")
    token = login()

    logger.info("Cargando DBFs...")
    df_productos = pd.DataFrame(iter(DBF(DBF_PRODUCTOS, encoding="latin-1")))
    df_preciprod = pd.DataFrame(iter(DBF(DBF_PRECIOLIS, encoding="latin-1")))

    # Limpiar strings de todos los DataFrames
    df_productos = df_productos.applymap(lambda x: clean_str(x) if isinstance(x,str) else x)
    df_preciprod = df_preciprod.applymap(lambda x: clean_str(x) if isinstance(x,str) else x)

    # Sincronización paso a paso, batch por batch
    sync_categories(df_productos, token)
    sync_products(df_productos, token)
    sync_price_lists(df_preciprod, token)
    sync_price_list_items(df_preciprod, token)

    logger.info("SINCRONIZACIÓN COMPLETA: Todos los registros procesados en batches")

if __name__ == "__main__":
    main()