"""
Production-optimized DBF sync client - PRODUCTS & PRICE LISTS
"""

import gzip
import json
from datetime import datetime
import sys

import pandas as pd
import requests
from dbfread import DBF

# Importar configuración centralizada
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))  # Agregar servicios/ al path
from config import (
    BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD,
    DBF_DIR, IMAGES_FOLDER, CDN_URL,
    PRODUCTOS_BLOQUEADOS, CATEGORIA_BLOQUEADA
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

import unicodedata
import re

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

def login() -> str:
    print(f"Authenticating as {ADMIN_USERNAME}...")
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            data={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"Login failed: {e}")
        return None

def limpiar_texto(valor):
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    return str(valor).strip()

def limpiar_numero(valor, default=0.0):
    if pd.isna(valor) or valor == '':
        return default
    try:
        return float(str(valor).replace(",", ""))
    except:
        return default

def verificar_imagen_existe(producto_id):
    if (IMAGES_FOLDER / f"{producto_id}.webp").exists():
        return f"{CDN_URL}/{producto_id}.webp"
    return None

def dbf_to_dataframe(dbf_path):
    print(f"Reading {dbf_path.name}...")
    dbf = DBF(dbf_path, encoding='latin1', ignore_missing_memofile=True)
    return pd.DataFrame(iter(dbf))

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
    
    # Backend con ThreadPoolExecutor retorna HTTP 202 con formato diferente
    result = response.json()
    
    # Verificar si es respuesta asincrona (202) o sincrona (200)
    if response.status_code == 202 or 'status' in result:
        # Respuesta asincrona - thread pool
        print(f"  ✓ Encolado: {result.get('message', 'Procesando en background')}")
    elif 'actualizados' in result:
        # Respuesta sincrona legacy
        print(f"  ✓ Completado: {result['actualizados']} actualizados")
    
    return result


# ============================================================================
# PROCESSORS
# ============================================================================

def process_and_upload_products(token):
    print("\n--- STEP 1: PRODUCTS ---")
    
    # Load DataFrames
    df_prod = dbf_to_dataframe(DBF_DIR / "producto.dbf")
    
    # Descriptions (dict)
    print("Loading descriptions...")
    desc_dbf = DBF(DBF_DIR / "pro_desc.dbf", encoding='latin1', ignore_missing_memofile=True)
    descripciones = {r['CVE_PROD'].strip(): r['DESC1'].strip() for r in desc_dbf if r.get('CVE_PROD') and r.get('DESC1')}
    
    # Stock (dict)
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
    # Convert filtered columns to string to ensure matching works against string sets
    df_prod = df_prod[df_prod['CSE_PROD'].astype(str).str.upper().str.strip() != CATEGORIA_BLOQUEADA]
    df_prod = df_prod[~df_prod['CSE_PROD'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)]
    df_prod = df_prod[~df_prod['CVE_TIAL'].astype(str).str.strip().isin(PRODUCTOS_BLOQUEADOS)] # Assuming CVE_TIAL might also need filtering
    print(f"Products: {initial_count} -> {len(df_prod)}")

    # Build JSON
    productos_list = []
    categorias = set()
    
    for _, row in df_prod.iterrows():
        pid = limpiar_texto(row.get('CVE_PROD'))
        if not pid: continue
        
        cat = limpiar_texto(row.get('CSE_PROD'))
        if cat: categorias.add(cat)
        
        productos_list.append({
            "product_id": pid,
            "codebar": limpiar_texto(row.get('CODBAR')),
            "name": limpiar_texto(row.get('DESC_PROD'))[:255] or "Sin Nombre",
            "description": limpiar_texto(row.get('FACT_PESO')), # Technical desc mapped per user Pref
            "descripcion_2": descripciones.get(pid),
            "stock_count": stock_map.get(pid, 0),
            "base_price": limpiar_numero(row.get('CTO_ENT')),
            "iva_percentage": limpiar_numero(row.get('PORCENIVA'), 16.0),
            "category_name": cat,
            "unidad_medida": limpiar_texto(row.get('UNI_MED')),
            "image_url": verificar_imagen_existe(pid)
        })
    
    payload = {"categorias": list(categorias), "productos": productos_list}
    upload_compressed_json("/sync-upload/productos-json", payload, token)


def process_and_upload_pricelists(token):
    print("\n--- STEP 2: PRICE LISTS (HEADERS) ---")
    df = dbf_to_dataframe(DBF_DIR / "PRECIPROD.DBF")
    
    # Unique headers
    unique_ids = df['NLISPRE'].unique()
    
    listas_payload = []
    for lis_id in unique_ids:
        if not lis_id: continue
        try:
            listas_payload.append({
                "price_list_id": int(lis_id),
                "name": f"Lista {int(lis_id)}"
            })
        except ValueError:
            continue
    
    payload = {"listas": listas_payload}
    upload_compressed_json("/sync-upload/listas-precios-json", payload, token)


def process_and_upload_items(token):
    print("\n--- STEP 3: PRICE LIST ITEMS ---")
    df = dbf_to_dataframe(DBF_DIR / "PRECIPROD.DBF")
    
    items_payload = []
    for _, row in df.iterrows():
        pid = limpiar_texto(row.get('CVE_PROD'))
        lis_id = limpiar_texto(row.get('NLISPRE'))
        
        if not pid or not lis_id: continue
        
        items_payload.append({
            "price_list_id": int(lis_id),
            "product_id": pid,
            "markup_percentage": limpiar_numero(row.get('LMARGEN')),
            "final_price": limpiar_numero(row.get('LPRECPROD'))
        })

    payload = {"items": items_payload}
    upload_compressed_json("/sync-upload/items-precios-json", payload, token)


# ============================================================================
# MAIN
# ============================================================================

def main():
    start = datetime.now()
    print(f"STARTING PRODUCTS SYNC {start}")
    
    token = login()
    if not token: return
    
    try:
        process_and_upload_products(token)
        process_and_upload_pricelists(token)
        process_and_upload_items(token)
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
    
    end = datetime.now()
    print(f"\nCOMPLETED IN {(end - start).total_seconds():.2f}s")

if __name__ == "__main__":
    main()
