"""
Production-optimized DBF sync client - USERS (SELLERS & CUSTOMERS)
"""

import gzip
import json
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import requests
from dbfread import DBF


# ============================================================================
# CONFIGURATION
# ============================================================================

BACKEND_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "farmasaenz123"

# Adjust paths as needed
DBF_DIR = Path("C:\\Users\\berna\\Documents\\GitProjects\\farmacruz-ecomerce\\backend\\dbfs")
IMAGES_FOLDER = Path("C:\\Users\\berna\\Documents\\GitProjects\\farmacruz-ecomerce\\backend\\images")
CDN_URL = "https://digheqbxnmxr3.cloudfront.net/images"

# User DBFs
CLIENTES_DBF = DBF_DIR / "clientes.dbf"
AGENTES_DBF = DBF_DIR / "agentes.dbf"

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
    return response.json()


# ============================================================================
# PROCESSORS
# ============================================================================

def process_and_upload_sellers(token):
    print("\n--- STEP 1: SELLERS (AGENTS) ---")
    df_agents = dbf_to_dataframe(AGENTES_DBF)
    
    sellers_list = []
    if not df_agents.empty and 'CVE_AGE' in df_agents.columns:
        df_agents = df_agents[df_agents['CVE_AGE'].notna()]
        
        for _, r in df_agents.iterrows():
            try:
                sellers_list.append({
                    "user_id": int(r['CVE_AGE']),
                    "username": f"seller_{r['CVE_AGE']}",
                    "email": r.get('EMAIL_AGE') or f"seller{r['CVE_AGE']}@farmacruz.com",
                    "full_name": str(r.get('NOM_AGE','')).strip(),
                    "password": "vendedor2026",
                    "is_active": True
                })
            except: continue
            
    if sellers_list:
        payload = {"sellers": sellers_list}
        result = upload_compressed_json("/sync-upload/sellers-json", payload, token)
        print(f"  Success: {result['actualizados']} updated, {result['creados']} created")
    else:
        print("  No sellers found.")


def process_and_upload_customers(token):
    print("\n--- STEP 2: CUSTOMERS ---")
    df_cust = dbf_to_dataframe(CLIENTES_DBF)
    
    customers_list = []
    if not df_cust.empty and 'CVE_CTE' in df_cust.columns:
        df_cust = df_cust[df_cust['CVE_CTE'].notna()]
        
        for _, r in df_cust.iterrows():
            try:
                cid = int(r['CVE_CTE'])
                customers_list.append({
                    "customer_id": cid,
                    "username": create_username(r.get('NOM_CTE',''), cid),
                    "email": r.get('EMAIL_CTE') or f"client{cid}@farmacruz.com",
                    "full_name": str(r.get('NOM_CTE','')).strip(),
                    "password": "farmacruz2026",
                    "agent_id": str(r['CVE_AGE']) if r.get('CVE_AGE') else None,
                    "business_name": str(r.get('NOM_FAC', r.get('NOM_CTE',''))).strip(),
                    "rfc": str(r.get('RFC_CTE',''))[:13] or None,
                    "price_list_id": int(float(r['LISTA_PREC'])) if r.get('LISTA_PREC') else None,
                    "address_1": f"{r.get('DIR_CTE','')} {r.get('COL_CTE','')} {r.get('CD_CTE','')}".strip() or None,
                    "telefono_1": build_phone(r.get('LADA_CTE'), r.get('TEL1_CTE'))
                })
            except: continue
            
    if customers_list:
        payload = {"customers": customers_list}
        result = upload_compressed_json("/sync-upload/customers-json", payload, token)
        print(f"  Success: {result['actualizados']} updated, {result['creados']} created")
    else:
        print("  No customers found.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    start = datetime.now()
    print(f"STARTING USERS SYNC {start}")
    
    token = login()
    if not token: return
    
    try:
        process_and_upload_sellers(token)
        process_and_upload_customers(token)
    except Exception as e:
        print(f"\nCRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
    
    end = datetime.now()
    print(f"\nCOMPLETED IN {(end - start).total_seconds():.2f}s")

if __name__ == "__main__":
    main()
