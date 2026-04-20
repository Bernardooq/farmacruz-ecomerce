"""
Sincronizador de Productos DBF → PostgreSQL
============================================
Refactored to use centralized sync_functions module.

Lee los archivos DBF del sistema viejo y sincroniza:
- Categorías
- Productos (con stock desde existe.dbf)
- Listas de precios
- Items de listas (markups por producto)

Corre cada X horas via Task Scheduler o como Windows Service.

Autor: Farmacruz Team
"""

from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys

import pandas as pd
import requests
from dbfread import DBF

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    DBF_DIR, IMAGES_FOLDER, CDN_URL,
    PRODUCTOS_BLOQUEADOS, CATEGORIA_BLOQUEADA,
    PRODUCTO_DBF, PRECIPROD_DBF, EXISTE_DBF, PRO_DESC_DBF, BATCH_SIZE
)

# Importar funciones compartidas
from sync_functions import (
    limpiar_texto, limpiar_numero,
    build_producto_dict, build_categoria_dict,
    build_lista_precios_dict, build_item_lista_dict,
    cargar_descripciones_extra, cargar_existencias,
    login, verificar_imagen_existe
)

# Local aliases
DBF_FOLDER = DBF_DIR
PRODUCTOS_DBF = PRODUCTO_DBF
PRECIOS_DBF = PRECIPROD_DBF
EXISTENCIAS_DBF = EXISTE_DBF
DESCRIPCIONES_DBF = PRO_DESC_DBF
USERNAME = ADMIN_USERNAME
PASSWORD = ADMIN_PASSWORD


# ============================================================================
# API - Comunicacion con el backend
# ============================================================================

def enviar_batch(datos, endpoint, token, nombre):
    """Envia un lote de datos al backend"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/{endpoint}",
            json=datos,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"  DEBUG {nombre}: Status {response.status_code}, Content: {response.text[:300]}")
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error in {nombre}: {e}")
        if 'response' in locals():
            print(f"  Response status: {response.status_code}")
            print(f"  Response content (first 500 chars): {response.text[:500]}")
        return {"creados": 0, "actualizados": 0, "errores": len(datos)}


def enviar_en_lotes(datos, batch_size, endpoint, token, nombre, max_workers=5):
    """Divide datos en lotes y los envia al backend en paralelo"""
    if not datos:
        print(f"{nombre}: No data to sync")
        return
    
    total = len(datos)
    num_batches = (total + batch_size - 1) // batch_size
    
    print(f"{nombre}: Syncing {total} records ({num_batches} batches, {max_workers} workers)")
    
    batches = []
    for i in range(0, total, batch_size):
        lote = datos[i:i + batch_size]
        batches.append((lote, endpoint, token, nombre))
    
    creados = 0
    actualizados = 0
    errores = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(enviar_batch, lote, ep, tk, nm): i 
            for i, (lote, ep, tk, nm) in enumerate(batches)
        }
        
        for future in as_completed(futures):
            batch_num = futures[future]
            try:
                resultado = future.result()
                creados += resultado.get('creados', 0)
                actualizados += resultado.get('actualizados', 0)
                errores += resultado.get('errores', 0)
            except Exception as e:
                print(f"  Batch {batch_num + 1}/{num_batches} failed: {e}")
                errores += len(batches[batch_num][0])
    
    print(f"  Done: {creados} created, {actualizados} updated, {errores} errors")


def enviar_fecha_limpieza(fecha, token):
    """Envia la fecha de sync al backend"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup",
            json={"last_sync": fecha},
            headers=headers
        )
        response.raise_for_status()
        print("Cleaned up old records")
    except Exception as e:
        print(f"Cleanup warning: {e}")


# ============================================================================
# PROCESADORES - Lectura y preparacion de datos
# ============================================================================

def procesar_categorias(df_productos, fecha_sync):
    """Extrae categorias unicas de los productos"""
    categorias = df_productos['CSE_PROD'].dropna().apply(limpiar_texto).unique()
    
    categorias = [
        c for c in categorias 
        if c and c.upper() != CATEGORIA_BLOQUEADA and c not in PRODUCTOS_BLOQUEADOS
    ]
    
    return [build_categoria_dict(cat, fecha_sync) for cat in categorias]


def procesar_productos(df_productos, descripciones_extra, stock_map, fecha_sync):
    """Lee productos del DBF y los prepara para el backend"""
    print("Processing products...")
    productos = []
    
    def check_img(pid):
        return verificar_imagen_existe(pid, IMAGES_FOLDER, CDN_URL)
    
    for _, row in df_productos.iterrows():
        categoria = limpiar_texto(row.get('CSE_PROD'))
        if categoria.upper() == CATEGORIA_BLOQUEADA or categoria in PRODUCTOS_BLOQUEADOS:
            continue
        
        cve_tial = limpiar_texto(row.get('CVE_TIAL'))
        if cve_tial in PRODUCTOS_BLOQUEADOS:
            continue
        
        productos.append(build_producto_dict(row, descripciones_extra, stock_map, check_img, fecha_sync))
    
    return productos


def procesar_listas_precios(df_precios, fecha_sync):
    """Extrae listas de precios unicas"""
    listas_ids = df_precios['NLISPRE'].dropna().apply(limpiar_texto).unique()
    
    return [build_lista_precios_dict(lista_id, fecha_sync) for lista_id in listas_ids]


def procesar_items_listas(df_precios, listas_ids, fecha_sync):
    """Procesa los items (productos) de cada lista de precios con sus markups"""
    print("Processing price list items...")
    items = []
    
    for lista_id in listas_ids:
        df_lista = df_precios[df_precios['NLISPRE'].apply(limpiar_texto) == lista_id]
        
        for _, row in df_lista.iterrows():
            items.append(build_item_lista_dict(row, fecha_sync))
    
    return items


# ============================================================================
# MAIN - Ejecucion principal
# ============================================================================

def main():
    """Funcion principal de sincronizacion"""
    inicio = datetime.now(timezone.utc)
    fecha_sync = inicio.isoformat()
    
    print(f"\n{'='*60}")
    print(f"DBF Sync - {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Login
    token = login(BACKEND_URL, USERNAME, PASSWORD)
    if not token:
        print("Authentication failed. Aborting.\n")
        return
    
    # 2. Cargar datos auxiliares
    descripciones_extra = cargar_descripciones_extra(DESCRIPCIONES_DBF)
    stock_map = cargar_existencias(EXISTENCIAS_DBF)
    
    # 3. Leer archivos DBF principales
    print(f"Reading {PRODUCTOS_DBF.name}...")
    df_productos = pd.DataFrame(iter(DBF(PRODUCTOS_DBF, encoding='latin1', ignore_missing_memofile=True)))
    
    print(f"Reading {PRECIOS_DBF.name}...")
    df_precios = pd.DataFrame(iter(DBF(PRECIOS_DBF, encoding='latin1', ignore_missing_memofile=True)))
    
    df_productos = df_productos.map(lambda x: limpiar_texto(x) if isinstance(x, str) else x)
    
    # 4. Procesar y enviar datos
    print()
    
    categorias = procesar_categorias(df_productos, fecha_sync)
    enviar_en_lotes(categorias, BATCH_SIZE["categorias"], "sync/categories", token, "Categorías", max_workers=5)
    
    productos = procesar_productos(df_productos, descripciones_extra, stock_map, fecha_sync)
    enviar_en_lotes(productos, BATCH_SIZE["productos"], "sync/products", token, "Productos", max_workers=8)
    
    listas, listas_ids = procesar_listas_precios(df_precios, fecha_sync), df_precios['NLISPRE'].dropna().apply(limpiar_texto).unique()
    enviar_en_lotes(listas, BATCH_SIZE["listas"], "sync/price-lists", token, "Listas de Precios", max_workers=5)
    
    items = procesar_items_listas(df_precios, listas_ids, fecha_sync)
    enviar_en_lotes(items, BATCH_SIZE["items"], "sync/price-list-items", token, "Items de Listas", max_workers=10)
    
    # 5. Limpieza
    print()
    print("--- CLEANUP: PRODUCTS ---")
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup",
            json={"last_sync": fecha_sync},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        print("  ✓ Productos/categorias/listas limpiados\n")
    except Exception as e:
        print(f"  ⚠ Cleanup warning: {e}\n")
    
    # 6. Resumen final
    fin = datetime.now(timezone.utc)
    duracion = (fin - inicio).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"Completed in {duracion:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
