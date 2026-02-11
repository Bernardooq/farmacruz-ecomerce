"""
Unified DBF Sync Client (Sequential Flow + Cached Threading)
============================================================
Refactored to use centralized sync_functions module.

Order of Operations (Strictly Sequential):
1. Categories       (Threaded Batches)
2. Products         (Threaded Batches)
3. Price Lists      (Threaded Batches)
4. Price Items      (Threaded Batches)
5. Sellers          (Threaded Batches)
6. Customers        (Threaded Batches)
7. Global Cleanup   (Deactivates records not updated in this run)
"""

from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
import pandas as pd
from dbfread import DBF
import sys

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import (
    BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    DBF_DIR, IMAGES_FOLDER, CDN_URL,
    CLIENTES_DBF, AGENTES_DBF,
    PRODUCTOS_BLOQUEADOS, CATEGORIA_BLOQUEADA,
    PRODUCTO_DBF, PRECIPROD_DBF, EXISTE_DBF, PRO_DESC_DBF, BATCH_SIZE
)

# Importar funciones compartidas
from sync_functions import (
    limpiar_texto, limpiar_numero,
    build_producto_dict, build_categoria_dict,
    build_vendedor_dict, build_cliente_dict,
    build_lista_precios_dict, build_item_lista_dict,
    cargar_descripciones_extra, cargar_existencias,
    dbf_to_dataframe, login, verificar_imagen_existe
)

# Local aliases
DBF_FOLDER = DBF_DIR
PRODUCTOS_DBF = PRODUCTO_DBF  
PRECIOS_DBF = PRECIPROD_DBF
EXISTENCIAS_DBF = EXISTE_DBF
DESCRIPCIONES_DBF = PRO_DESC_DBF

# ============================================================================
# API HELPERS
# ============================================================================

def send_batch(endpoint, data, token, name):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(f"{BACKEND_URL}/{endpoint}", json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"  [ERR] {name} Batch Failed: {e}")
        return {"creados": 0, "actualizados": 0, "errores": len(data)}

def sync_in_parallel(data, batch_size, endpoint, token, name, workers=5):
    """Splits data into batches and sends them using threads."""
    if not data:
        print(f"[{name}] No data to sync.")
        return
    
    total = len(data)
    batches = [data[i:i + batch_size] for i in range(0, total, batch_size)]
    print(f"[{name}] Syncing {total} records -> {len(batches)} batches ({workers} threads)...")
    
    stats = {"creados": 0, "actualizados": 0, "errores": 0}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(send_batch, endpoint, batch, token, name): i for i, batch in enumerate(batches)}
        
        for future in as_completed(futures):
            try:
                res = future.result()
                stats["creados"] += res.get("creados", 0)
                stats["actualizados"] += res.get("actualizados", 0)
                stats["errores"] += res.get("errores", 0)
            except Exception as e:
                print(f"  Batch future failed: {e}")
                
    print(f"[{name}] DONE: {stats['creados']} created, {stats['actualizados']} updated, {stats['errores']} errors")


# ============================================================================
# MAIN SYNC LOGIC
# ============================================================================

def main():
    start_total = datetime.now()
    sync_time = datetime.now(timezone.utc).isoformat()
    
    print(f"=== UNIFIED SEQUENTIAL SYNC START: {start_total} ===")
    print(f"=== SYNC TIMESTAMP: {sync_time} ===")
    
    # 0. Auth
    token = login(BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token: return

    # --- STEP 1: CATEGORIES ---
    print("\n--- STEP 1: CATEGORIES ---")
    df_prod = dbf_to_dataframe(PRODUCTOS_DBF)
    cats_data = []
    if not df_prod.empty:
        # Global Filters
        df_prod = df_prod[df_prod['CSE_PROD'].astype(str).str.upper().str.strip() != CATEGORIA_BLOQUEADA]
        df_prod = df_prod[~df_prod['CSE_PROD'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
        if 'CVE_TIAL' in df_prod.columns:
            df_prod = df_prod[~df_prod['CVE_TIAL'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
        
        cats_uniq = df_prod['CSE_PROD'].dropna().apply(limpiar_texto).unique()
        cats_data = [build_categoria_dict(c, sync_time) for c in cats_uniq if c]
        sync_in_parallel(cats_data, BATCH_SIZE['categorias'], "sync/categories", token, "Categories", 1)
    
    # --- STEP 2: PRODUCTS ---
    print("\n--- STEP 2: PRODUCTS ---")
    stock_map = {}
    desc_map = {}
    
    if not df_prod.empty:
        stock_map = cargar_existencias(EXISTENCIAS_DBF)
        desc_map = cargar_descripciones_extra(DESCRIPCIONES_DBF)
        
        prods_list = []
        
        def check_img(pid):
            return verificar_imagen_existe(pid, IMAGES_FOLDER, CDN_URL)
        
        for _, r in df_prod.iterrows():
            pid = limpiar_texto(r['CVE_PROD'])
            if not pid: continue
            
            prods_list.append(build_producto_dict(r, desc_map, stock_map, check_img, sync_time))
        
        sync_in_parallel(prods_list, BATCH_SIZE['productos'], "sync/products", token, "Products", 8)

    # --- STEP 3: PRICE LISTS ---
    print("\n--- STEP 3: PRICE LISTS ---")
    df_price = dbf_to_dataframe(PRECIOS_DBF)
    if not df_price.empty:
        lids = df_price['NLISPRE'].dropna().unique()
        lists_data = [build_lista_precios_dict(i, sync_time) for i in lids if i]
        sync_in_parallel(lists_data, BATCH_SIZE['listas'], "sync/price-lists", token, "PriceLists", 1)

    # --- STEP 4: PRICE ITEMS ---
    print("\n--- STEP 4: PRICE ITEMS ---")
    if not df_price.empty:
        items_data = []
        for _, r in df_price.iterrows():
            pid = limpiar_texto(r.get('CVE_PROD'))
            lid = limpiar_texto(r.get('NLISPRE'))
            if pid and lid:
                items_data.append(build_item_lista_dict(r, sync_time))
        sync_in_parallel(items_data, BATCH_SIZE['items'], "sync/price-list-items", token, "PriceItems", 10)


    # --- STEP 5: SELLERS (AGENTS) ---
    print("\n--- STEP 5: SELLERS ---")
    df_agents = dbf_to_dataframe(AGENTES_DBF)
    if not df_agents.empty and 'CVE_AGE' in df_agents.columns:
        df_agents = df_agents[df_agents['CVE_AGE'].notna()]
        sellers_list = []
        for _, r in df_agents.iterrows():
            try:
                sellers_list.append(build_vendedor_dict(r, sync_time))
            except: continue
        sync_in_parallel(sellers_list, BATCH_SIZE['users'], "sync/sellers", token, "Sellers", 1)

    # --- STEP 6: CUSTOMERS ---
    print("\n--- STEP 6: CUSTOMERS ---")
    df_cust = dbf_to_dataframe(CLIENTES_DBF)
    if not df_cust.empty and 'CVE_CTE' in df_cust.columns:
        df_cust = df_cust[df_cust['CVE_CTE'].notna()]
        customers_list = []
        for _, r in df_cust.iterrows():
            try:
                customers_list.append(build_cliente_dict(r, sync_time))
            except: continue
        sync_in_parallel(customers_list, BATCH_SIZE['users'], "sync/customers", token, "Customers", 5)

    # --- STEP 7: CLEANUP ---
    print("\n--- STEP 7: CLEANUP ---")
    
    # Cleanup productos/categorias/listas
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup",
            json={"last_sync": sync_time},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        print("  ✓ Productos/categorias/listas limpiados")
    except Exception as e:
        print(f"  ⚠ Products cleanup failed: {e}")
    
    # Cleanup usuarios
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup-users",
            json={"last_sync": sync_time},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        print("  ✓ Usuarios limpiados")
    except Exception as e:
        print(f"  ⚠ Users cleanup failed: {e}")

    end_total = datetime.now()
    print(f"\n{'='*60}")
    print(f"ALL SYNC OPERATIONS COMPLETED IN {(end_total - start_total).total_seconds():.2f}s")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
