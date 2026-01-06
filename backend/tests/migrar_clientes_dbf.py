import requests
import pandas as pd
from dbfread import DBF
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN BÁSICA
# ==========================================
API_URL = "http://localhost:8000/api/v1"
DBF_FILE = Path(r"C:\Users\berna\Downloads\desarrollo\CLIENTES.DBF")
BATCH_SIZE = 50  # Mandamos de 50 en 50 para no saturar
ADMIN_AUTH = {"username": "manuel.saenz.admin", "password": "farmasaenz123"}

def obtener_token():
    """ Paso 1: Pedir permiso al server para entrar """
    print("Logueando en el sistema...")
    r = requests.post(f"{API_URL}/auth/login", data=ADMIN_AUTH)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        print(f"Error de login: {r.text}")
        return None

def limpiar_y_formatear(df):
    """ Paso 2: Convertir los datos raros del DBF a JSON bonito """
    print(f"Limpiando {len(df)} registros...")
    lista_final = []

    for _, row in df.iterrows():
        # Saltamos si no tiene ID de cliente
        if pd.isna(row['CVE_CTE']): continue

        # Armamos el objeto tal cual lo espera tu API
        cliente = {
            "customer_id": int(row['CVE_CTE']),
            "username": str(row.get('NOM_CTE', 'user')).strip()[:20].replace(" ", "_"),
            "email": f"cliente_{row['CVE_CTE']}@farmacruz.com",
            "full_name": str(row.get('NOM_CTE', 'Sin Nombre')).strip(),
            "password": "FarmaCruz2024!", # Password genérica inicial
            "price_list_id": int(float(row['LISTA_PREC'])) if row.get('LISTA_PREC') else 1,
            "address": str(row.get('DIR_CTE', 'N/D')).strip()
        }
        lista_final.append(cliente)
    
    return lista_final

def migrar():
    # 1. Obtener Token
    token = obtener_token()
    if not token: return
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Leer DBF usando Pandas (la forma más fácil)
    print(f"Cargando archivo: {DBF_FILE.name}")
    try:
        tabla = DBF(DBF_FILE, encoding='latin-1')
        df = pd.DataFrame(iter(tabla))
    except Exception as e:
        print(f"No se pudo leer el DBF: {e}")
        return

    # 3. Preparar todos los clientes
    todos_los_clientes = limpiar_y_formatear(df)
    total = len(todos_los_clientes)

    # 4. ENVÍO POR LOTES (Batch) 
    # Usamos un rango que salta de 'BATCH_SIZE' en 'BATCH_SIZE'
    print(f"Iniciando migración de {total} clientes...")
    
    for i in range(0, total, BATCH_SIZE):
        # Cortamos la lista (Slicing) para sacar el bloque actual
        lote = todos_los_clientes[i : i + BATCH_SIZE]
        
        try:
            # Enviamos la LISTA de clientes al endpoint
            # Nota: Tu endpoint debe estar preparado para recibir una lista []
            res = requests.post(f"{API_URL}/customers/batch", json=lote, headers=headers)
            
            if res.status_code in [200, 201]:
                print(f"Bloque enviado: {i + len(lote)} / {total}")
            else:
                print(f"Error en bloque {i}: {res.status_code}")
                
        except Exception as e:
            print(f"Error de conexión: {e}")

    print("\n¡Migración terminada exitosamente!")

if __name__ == "__main__":
    migrar()