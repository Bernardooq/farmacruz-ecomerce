"""
Production-optimized DBF sync client - PRODUCTS & PRICE LISTS
Refactored to use centralized sync_functions module.
"""

import gzip
import json
from datetime import datetime
import sys
from pathlib import Path

import pandas as pd
import requests
from dbfread import DBF

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    DBF_DIR, IMAGES_FOLDER, CDN_URL,
    PRODUCTOS_BLOQUEADOS, CATEGORIA_BLOQUEADA
)

# Importar funciones compartidas
from sync_functions import (
    build_producto_dict,
    build_lista_precios_dict,
    build_item_lista_dict,
    cargar_descripciones_extra,
    dbf_to_dataframe,
    login,
    verificar_imagen_existe,
    limpiar_texto,
    limpiar_numero
)

# ============================================================================
# UPLOAD HELPERS
# ============================================================================

def upload_compressed_json(endpoint, data, token):
    json_str = json.dumps(data)
    original_size = len(json_str.encode('utf-8'))
    compressed = gzip.compress(json_str.encode('utf-8'))
    compressed_size = len(compressed)
    
    print(f"  Uploading {endpoint}...")
    print(f"  Size: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB ({100 - (compressed_size/original_size)*100:.1f}% savings)")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Encoding": "gzip",
        "Content-Type": "application/json"
    }
    
    response = requests.post(f"{BACKEND_URL}{endpoint}", data=compressed, headers=headers, timeout=300)
    response.raise_for_status()
    
    result = response.json()
    
    if response.status_code == 202 or 'status' in result:
        print(f"  ✓ Encolado: {result.get('message', 'Procesando en background')}")
    elif 'actualizados' in result:
        print(f"  ✓ Completado: {result['actualizados']} actualizados")
    
    return result


# ============================================================================
# PROCESSORS
# ============================================================================

def process_and_upload_products(token, sync_time):
    print("\n--- STEP 1: PRODUCTS ---")
    
    # Load DataFrames
    df_prod = dbf_to_dataframe(DBF_DIR / "producto.dbf")
    
    # Descriptions and stock maps
    descripciones = cargar_descripciones_extra(DBF_DIR / "pro_desc.dbf")
    
    print("Loading stock...")
    stock_df = dbf_to_dataframe(DBF_DIR / "existe.dbf")
    stock_map = {}
    for _, row in stock_df.iterrows():
        pid = limpiar_texto(row.get('CVE_PROD'))
        val = row.get('EXISTENCIA') or row.get('EXISTE') or row.get('STOCK') or 0
        if pid: stock_map[pid] = int(limpiar_numero(val))

    # Filtering
    print("Applying filters...")
    initial_count = len(df_prod)
    df_prod = df_prod[df_prod['CSE_PROD'].astype(str).str.upper().str.strip() != CATEGORIA_BLOQUEADA]
    df_prod = df_prod[~df_prod['CSE_PROD'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
    df_prod = df_prod[~df_prod['CVE_TIAL'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
    print(f"Products: {initial_count} -> {len(df_prod)}")

    # Build JSON
    productos_list = []
    categorias = set()
    
    # Helper closure for image verification
    def check_img(pid):
        return verificar_imagen_existe(pid, IMAGES_FOLDER, CDN_URL)
    
    for _, row in df_prod.iterrows():
        pid = limpiar_texto(row.get('CVE_PROD'))
        if not pid: continue
        
        cat = limpiar_texto(row.get('CSE_PROD'))
        if cat: categorias.add(cat)
        
        productos_list.append(build_producto_dict(row, descripciones, stock_map, check_img, sync_time))
    
    payload = {"categorias": list(categorias), "productos": productos_list}
    upload_compressed_json("/sync-upload/productos-json", payload, token)


def process_and_upload_pricelists(token, sync_time):
    print("\n--- STEP 2: PRICE LISTS (HEADERS) ---")
    df = dbf_to_dataframe(DBF_DIR / "PRECIPROD.DBF")
    
    unique_ids = df['NLISPRE'].unique()
    
    listas_payload = []
    for lis_id in unique_ids:
        if not lis_id: continue
        try:
            listas_payload.append(build_lista_precios_dict(lis_id, sync_time))
        except ValueError:
            continue
    
    payload = {"listas": listas_payload}
    upload_compressed_json("/sync-upload/listas-precios-json", payload, token)


def process_and_upload_items(token, sync_time):
    print("\n--- STEP 3: PRICE LIST ITEMS ---")
    df = dbf_to_dataframe(DBF_DIR / "PRECIPROD.DBF")
    
    items_payload = []
    for _, row in df.iterrows():
        pid = limpiar_texto(row.get('CVE_PROD'))
        lis_id = limpiar_texto(row.get('NLISPRE'))
        
        if not pid or not lis_id: continue
        
        items_payload.append(build_item_lista_dict(row, sync_time))

    payload = {"items": items_payload}
    upload_compressed_json("/sync-upload/items-precios-json", payload, token)


# ============================================================================
# MAIN
# ============================================================================

def main():
    start = datetime.now()
    print(f"STARTING PRODUCTS SYNC {start}")
    sync_time = datetime.now().isoformat()
    
    token = login(BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token: return
    
    try:
        process_and_upload_products(token, sync_time)
        process_and_upload_pricelists(token, sync_time)
        process_and_upload_items(token, sync_time)
        
        # Cleanup productos/categorias/listas no sincronizados
        # IMPORTANTE: Restamos 5 minutos para dar tiempo al procesamiento de la cola
        from datetime import timedelta
        cleanup_time = (start - timedelta(minutes=5)).isoformat()
        
        print("\n--- CLEANUP: PRODUCTS ---")
        try:
            response = requests.post(
                f"{BACKEND_URL}/sync/cleanup",
                json={"last_sync": cleanup_time},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            response.raise_for_status()
            print("  ✓ Productos/categorias/listas no sincronizados limpiados")
        except Exception as e:
            print(f"  ⚠ Cleanup warning: {e}")
            
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
    
    end = datetime.now()
    print(f"\nCOMPLETED IN {(end - start).total_seconds():.2f}s")

if __name__ == "__main__":
    main()
