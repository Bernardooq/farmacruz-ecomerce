"""
Unified DBF Sync Client (Sequential Flow + Cached Threading)
============================================================

Order of Operations (Strictly Sequential):
1. Categories       (Threaded Batches)
2. Products         (Threaded Batches)
3. Price Lists      (Threaded Batches)
4. Price Items      (Threaded Batches)
5. Sellers          (Threaded Batches)
6. Customers        (Threaded Batches)
7. Global Cleanup   (Deactivates records not updated in this run)

"""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import requests
import pandas as pd
from dbfread import DBF
import sys

# Importar configuración centralizada
sys.path.insert(0, str(Path(__file__).parent.parent))  # Agregar servicios/ al path
from config import (
    BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    DBF_DIR, IMAGES_FOLDER, CDN_URL,
    CLIENTES_DBF, AGENTES_DBF,
    PRODUCTOS_BLOQUEADOS, CATEGORIA_BLOQUEADA,
    PRODUCTO_DBF, PRECIPROD_DBF, EXISTE_DBF, PRO_DESC_DBF, BATCH_SIZE
)

# Local aliases for consistency with this script
DBF_FOLDER = DBF_DIR
PRODUCTOS_DBF = PRODUCTO_DBF  
PRECIOS_DBF = PRECIPROD_DBF
EXISTENCIAS_DBF = EXISTE_DBF
DESCRIPCIONES_DBF = PRO_DESC_DBF

# Filters
PRODUCTOS_BLOQUEADOS = {'99999', '99998', '100', '99'}
CATEGORIA_BLOQUEADA = 'GASTOS'

# ============================================================================
# DATA HELPERS
# ============================================================================

def clean_text(v): 
    if v is None: return ""
    return str(v).strip()

def clean_num(v, d=0.0):
    try: return float(str(v).replace(",","")) if pd.notna(v) else d
    except: return d

def check_img(pid):
    if (IMAGES_FOLDER / f"{pid}.webp").exists(): return f"{CDN_URL}/{pid}.webp"
    return None

def clean_digits(v): return re.sub(r"\D", "", str(v)) if v else ""
def clean_lada(v):
    v = clean_digits(v)
    if v.startswith(("044","045")): v = v[3:]
    elif v.startswith("01"): v = v[2:]
    return v if len(v) in (2,3) else ""
def build_phone(lada, num):
    num = clean_digits(num)
    lada = clean_lada(lada)
    if len(num) == 10: return f"+52{num}"
    if len(num) == 8 and lada: return f"+52{lada}{num}"
    return None

def norm_txt(t):
    if not t: return ""
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii","ignore").decode("ascii")
    return t.upper()
def clean_name(n):
    n = norm_txt(n)
    n = re.sub(r"\(.*?\)", "", n)
    n = re.sub(r"[^\w\s]", " ", n)
    return re.sub(r"\s+", " ", n).strip()
def create_username(nombre, pid):
    base = clean_name(nombre).lower().replace(" ", "_")
    return f"{base[:40].strip('_')}_{pid}"

def dbf_to_df(path):
    try:
        if not path.exists():
            print(f"[WARN] {path.name} NOT FOUND")
            return pd.DataFrame()
        return pd.DataFrame(iter(DBF(path, encoding='latin1', ignore_missing_memofile=True)))
    except Exception as e:
        print(f"[ERR] Failed reading {path.name}: {e}")
        return pd.DataFrame()

# ============================================================================
# API HELPERS
# ============================================================================

def login() -> str:
    print(f"[AUTH] Authenticating as {ADMIN_USERNAME}...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"[AUTH] Login failed: {e}")
        return None

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
    token = login()
    if not token: return

    # --- STEP 1: CATEGORIES ---
    print("\n--- STEP 1: CATEGORIES ---")
    df_prod = dbf_to_df(PRODUCTOS_DBF)
    cats_data = [] # Keep available for products step
    if not df_prod.empty:
        # Global Filters
        # Convert to string to ensure matching works
        df_prod = df_prod[df_prod['CSE_PROD'].astype(str).str.upper().str.strip() != CATEGORIA_BLOQUEADA]
        df_prod = df_prod[~df_prod['CSE_PROD'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
        # Filter by Obsolete Status (CVE_TIAL) - CRITICAL FIX
        if 'CVE_TIAL' in df_prod.columns:
            df_prod = df_prod[~df_prod['CVE_TIAL'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
        
        cats_uniq = df_prod['CSE_PROD'].dropna().apply(clean_text).unique()
        cats_data = [{"name": c, "updated_at": sync_time} for c in cats_uniq if c]
        sync_in_parallel(cats_data, BATCH_SIZE['categorias'], "sync/categories", token, "Categories", 1)
    
    # --- STEP 2: PRODUCTS ---
    print("\n--- STEP 2: PRODUCTS ---")
    stock_map = {}
    desc_map = {}
    
    # Load aux tables first
    if not df_prod.empty:
        df_stock = dbf_to_df(EXISTENCIAS_DBF)
        if not df_stock.empty:
            stock_map = {clean_text(r['CVE_PROD']): int(clean_num(r['EXISTENCIA'])) for _, r in df_stock.iterrows()}
            
        df_desc = dbf_to_df(DESCRIPCIONES_DBF)
        if not df_desc.empty:
            desc_map = {r['CVE_PROD'].strip(): r['DESC1'].strip() for _, r in df_desc.iterrows() if r.get('CVE_PROD') and r.get('DESC1')}
            
        prods_list = []
        for _, r in df_prod.iterrows():
            pid = clean_text(r['CVE_PROD'])
            if not pid: continue
            
            # Replicate description logic from legacy script
            desc_tecnica_parts = []
            if r.get('FACT_PESO'):
                desc_tecnica_parts.append(f"Costo Público: {clean_text(r.get('FACT_PESO'))}")
            if r.get('DATO_4'):
                desc_tecnica_parts.append(f"Caja: {clean_text(r.get('DATO_4'))}")
            desc_tecnica = " | ".join(desc_tecnica_parts) or None

            prods_list.append({
                "product_id": pid,
                "codebar": clean_text(r.get('CODBAR')) or None,
                "name": clean_text(r.get('DESC_PROD'))[:255] or "Sin Nombre",
                "description": desc_tecnica,
                "descripcion_2": desc_map.get(pid),
                "stock_count": stock_map.get(pid, 0),
                "base_price": clean_num(r.get('CTO_ENT')),
                "iva_percentage": clean_num(r.get('PORCENIVA'), 16.0),
                "category_name": clean_text(r.get('CSE_PROD')) or None,
                "unidad_medida": clean_text(r.get('UNI_MED')) or None,
                "is_active": True,
                "image_url": check_img(pid),
                "updated_at": sync_time
            })
        sync_in_parallel(prods_list, BATCH_SIZE['productos'], "sync/products", token, "Products", 8)

    # --- STEP 3: PRICE LISTS ---
    print("\n--- STEP 3: PRICE LISTS ---")
    df_price = dbf_to_df(PRECIOS_DBF)
    if not df_price.empty:
        lids = df_price['NLISPRE'].dropna().unique()
        lists_data = [{"price_list_id": int(i), "list_name": f"Lista {int(i)}", "updated_at": sync_time} for i in lids if i]
        sync_in_parallel(lists_data, BATCH_SIZE['listas'], "sync/price-lists", token, "PriceLists", 1)

    # --- STEP 4: PRICE ITEMS ---
    print("\n--- STEP 4: PRICE ITEMS ---")
    if not df_price.empty:
        items_data = []
        for _, r in df_price.iterrows():
            pid = clean_text(r.get('CVE_PROD'))
            lid = clean_text(r.get('NLISPRE'))
            if pid and lid:
                items_data.append({
                    "price_list_id": int(lid),
                    "product_id": pid,
                    "markup_percentage": clean_num(r.get('LMARGEN')),
                    "final_price": clean_num(r.get('LPRECPROD')),
                    "updated_at": sync_time
                })
        sync_in_parallel(items_data, BATCH_SIZE['items'], "sync/price-list-items", token, "PriceItems", 10)


    # --- STEP 5: SELLERS (AGENTS) ---
    print("\n--- STEP 5: SELLERS ---")
    df_agents = dbf_to_df(AGENTES_DBF)
    if not df_agents.empty and 'CVE_AGE' in df_agents.columns:
        df_agents = df_agents[df_agents['CVE_AGE'].notna()]
        sellers_list = []
        for _, r in df_agents.iterrows():
            try:
                sellers_list.append({
                    "user_id": int(r['CVE_AGE']),
                    "username": f"seller_{r['CVE_AGE']}",
                    "email": r.get('EMAIL_AGE') or f"seller{r['CVE_AGE']}@farmacruz.com",
                    "full_name": str(r.get('NOM_AGE','')).strip(),
                    "password": "vendedor2026",
                    "is_active": True,
                    "updated_at": sync_time
                })
            except: continue
        sync_in_parallel(sellers_list, BATCH_SIZE['users'], "sync/sellers", token, "Sellers", 1) # Workers=1 to be safe with users

    # --- STEP 6: CUSTOMERS ---
    print("\n--- STEP 6: CUSTOMERS ---")
    df_cust = dbf_to_df(CLIENTES_DBF)
    if not df_cust.empty and 'CVE_CTE' in df_cust.columns:
        df_cust = df_cust[df_cust['CVE_CTE'].notna()]
        customers_list = []
        for _, r in df_cust.iterrows():
            try:
                customers_list.append({
                    "customer_id": int(r['CVE_CTE']),
                    "username": create_username(r.get('NOM_CTE',''), r['CVE_CTE']),
                    "email": r.get('EMAIL_CTE') or f"client{r['CVE_CTE']}@farmacruz.com",
                    "full_name": str(r.get('NOM_CTE','')).strip(),
                    "password": "farmacruz2026",
                    "agent_id": str(r['CVE_AGE']) if r.get('CVE_AGE') else None,
                    "business_name": str(r.get('NOM_FAC', r.get('NOM_CTE',''))).strip(),
                    "rfc": str(r.get('RFC_CTE',''))[:13] or None,
                    "price_list_id": int(float(r['LISTA_PREC'])) if r.get('LISTA_PREC') else None,
                    "address_1": f"{r.get('DIR_CTE','')} {r.get('COL_CTE','')} {r.get('CD_CTE','')}".strip() or None,
                    "telefono_1": build_phone(r.get('LADA_CTE'), r.get('TEL1_CTE')),
                    "updated_at": sync_time
                })
            except: continue
        sync_in_parallel(customers_list, BATCH_SIZE['users'], "sync/customers", token, "Customers", 5)

    # --- STEP 7: CLEANUP ---
    print("\n--- STEP 7: CLEANUP ---")
    try:
        requests.post(f"{BACKEND_URL}/sync/cleanup", json={"last_sync": sync_time}, headers={"Authorization": f"Bearer {token}"})
        print("Cleanup request sent successfully.")
    except Exception as e:
        print(f"Cleanup failed: {e}")

    end_total = datetime.now()
    print(f"\n{'='*60}")
    print(f"ALL SYNC OPERATIONS COMPLETED IN {(end_total - start_total).total_seconds():.2f}s")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
