"""
Production-optimized DBF sync client - USERS (SELLERS & CUSTOMERS)
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
    CLIENTES_DBF, AGENTES_DBF
)

# Importar funciones compartidas
from sync_functions import (
    build_vendedor_dict,
    build_cliente_dict,
    dbf_to_dataframe,
    login
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

def process_and_upload_sellers(token):
    print("\n--- STEP 1: SELLERS (AGENTS) ---")
    df_agents = dbf_to_dataframe(AGENTES_DBF)
    
    sellers_list = []
    if not df_agents.empty and 'CVE_AGE' in df_agents.columns:
        df_agents = df_agents[df_agents['CVE_AGE'].notna()]
        
        for _, r in df_agents.iterrows():
            try:
                sellers_list.append(build_vendedor_dict(r))
            except: continue
            
    if sellers_list:
        payload = {"sellers": sellers_list}
        upload_compressed_json("/sync-upload/sellers-json", payload, token)
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
                customers_list.append(build_cliente_dict(r))
            except: continue
            
    if customers_list:
        payload = {"customers": customers_list}
        upload_compressed_json("/sync-upload/customers-json", payload, token)
    else:
        print("  No customers found.")


# ============================================================================
# MAIN
# ============================================================================

def main():
    start = datetime.now()
    sync_time = start.isoformat()
    print(f"STARTING USERS SYNC {start}")
    
    token = login(BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token: return
    
    try:
        process_and_upload_sellers(token)
        process_and_upload_customers(token)
        
        # Cleanup users no sincronizados
        # IMPORTANTE: Restamos 5 minutos para dar tiempo al procesamiento de la cola
        from datetime import timedelta
        cleanup_time = (start - timedelta(minutes=5)).isoformat()
        
        print("\n--- CLEANUP: USERS ---")
        try:
            response = requests.post(
                f"{BACKEND_URL}/sync/cleanup-users",
                json={"last_sync": cleanup_time},
                headers={"Authorization": f"Bearer {token}"},
                timeout=30
            )
            response.raise_for_status()
            print("  ✓ Usuarios no sincronizados desactivados")
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
