"""
Sincronizador de Usuarios DBF -> PostgreSQL
===========================================
Refactored to use centralized sync_functions module.

Este script lee los archivos DBF del sistema viejo y los sube al backend nuevo.
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
    CLIENTES_DBF, AGENTES_DBF
)

# Importar funciones compartidas
from sync_functions import (
    build_vendedor_dict,
    build_cliente_dict,
    login
)

# Cuantos registros enviar por llamada
BATCH_SIZE = 200


# ============================================================================
# API - Funciones para comunicarse con el backend
# ============================================================================

def sync_vendedores(token, vendedores):
    """Envia vendedores al backend"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/sellers",
            json=vendedores,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error syncing sellers: {e}")
        return {"creados": 0, "actualizados": 0}


def sync_clientes(token, clientes):
    """Envia batch de clientes al backend"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/customers",
            json=clientes,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_detail = e.response.json().get('detail', str(e)) if e.response else str(e)
        print(f"\n  HTTP Error: {error_detail}")
        return {"creados": 0, "actualizados": 0, "errores": len(clientes)}
    except Exception as e:
        print(f"\n  Error: {e}")
        return {"creados": 0, "actualizados": 0, "errores": len(clientes)}


# ============================================================================
# PROCESADORES - Leen DBF y preparan datos
# ============================================================================

def procesar_vendedores():
    """Lee AGENTES.DBF y retorna lista de vendedores"""
    if not AGENTES_DBF.exists():
        print(f"Warning: {AGENTES_DBF.name} not found")
        return []
    
    try:
        df = pd.DataFrame(iter(DBF(AGENTES_DBF, encoding='latin-1', ignore_missing_memofile=True)))
        df = df[df['CVE_AGE'].notna()].copy()
        
        print(f"Found {len(df)} sellers in DBF")
        
        vendedores = []
        sync_time = datetime.now(timezone.utc).isoformat()
        for _, row in df.iterrows():
            try:
                vendedores.append(build_vendedor_dict(row, sync_time))
            except:
                continue
        
        return vendedores
        
    except Exception as e:
        print(f"Error reading sellers: {e}")
        return []


def procesar_clientes():
    """Lee CLIENTES.DBF y retorna lista de clientes"""
    if not CLIENTES_DBF.exists():
        print(f"Warning: {CLIENTES_DBF.name} not found")
        return []
    
    try:
        df = pd.DataFrame(iter(DBF(CLIENTES_DBF, encoding='latin-1', ignore_missing_memofile=True)))
        df = df[df['CVE_CTE'].notna()].copy()
        
        print(f"Found {len(df)} customers in DBF")
        
        clientes = []
        sync_time = datetime.now(timezone.utc).isoformat()
        for _, row in df.iterrows():
            try:
                clientes.append(build_cliente_dict(row, sync_time))
            except Exception as e:
                print(f"⚠️  Cliente {row.get('CVE_CTE')} falló: {e}")
                continue
        
        return clientes
        
    except Exception as e:
        print(f"Error reading customers: {e}")
        return []


# ============================================================================
# MAIN - Ejecucion principal
# ============================================================================

def main():
    """Funcion principal de sincronizacion"""
    inicio = datetime.now(timezone.utc)
    sync_time = inicio.isoformat()
    print(f"\n{'='*60}")
    print(f"User Sync - {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Login
    token = login(BACKEND_URL, ADMIN_USERNAME, ADMIN_PASSWORD)
    if not token:
        print("Authentication failed. Aborting.\n")
        return
    
    # 2. Procesar vendedores
    print("Syncing sellers...")
    vendedores = procesar_vendedores()
    if vendedores:
        resultado = sync_vendedores(token, vendedores)
        print(f"  Done: {resultado.get('creados', 0)} created, {resultado.get('actualizados', 0)} updated\n")
    
    # 3. Procesar clientes
    print("Syncing customers...")
    clientes = procesar_clientes()
    
    if not clientes:
        print("  No customers to sync\n")
    else:
        total_creados = 0
        total_actualizados = 0
        total_errores = 0
        
        num_batches = (len(clientes) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"  Syncing {len(clientes)} records ({num_batches} batches)")
        
        batches_to_send = []
        for i in range(0, len(clientes), BATCH_SIZE):
            batch = clientes[i:i + BATCH_SIZE]
            batches_to_send.append(batch)
        
        max_workers = 5
        print(f"  Using {max_workers} worker threads")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(sync_clientes, token, batch): idx 
                for idx, batch in enumerate(batches_to_send)
            }
            
            for future in as_completed(futures):
                batch_idx = futures[future]
                batch_num = batch_idx + 1
                try:
                    resultado = future.result()
                    total_creados += resultado.get('creados', 0)
                    total_actualizados += resultado.get('actualizados', 0)
                    total_errores += resultado.get('errores', 0)
                    
                    errores_detalle = resultado.get('detalle_errores', [])
                    if errores_detalle:
                        print(f"  Batch {batch_num}/{num_batches}: Error ({len(errores_detalle)} records)")
                except Exception as e:
                    print(f"  Batch {batch_num}/{num_batches} failed: {e}")
                    total_errores += len(batches_to_send[batch_idx])
        
        print(f"\n  Final: {total_creados} created, {total_actualizados} updated")
        if total_errores > 0:
            print(f"  Errors: {total_errores} records")
        print()
    
    # 4. Cleanup usuarios no sincronizados
    print("--- CLEANUP: USERS ---")
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup-users",
            json={"last_sync": sync_time},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30
        )
        response.raise_for_status()
        print("  ✓ Usuarios no sincronizados desactivados\n")
    except Exception as e:
        print(f"  ⚠ Cleanup warning: {e}\n")
    
    # 5. Resumen final
    fin = datetime.now(timezone.utc)
    duracion = (fin - inicio).total_seconds()
    
    print(f"{'='*60}")
    print(f"Completed in {duracion:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
