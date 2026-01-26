"""
Sincronizador de Usuarios DBF -> PostgreSQL
===========================================

Este script lee los archivos DBF del sistema viejo y los sube al backend nuevo.
Corre cada X horas via Task Scheduler o como Windows Service.

Autor: Farmacruz Team
"""

import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
from dbfread import DBF


# ============================================================================
# CONFIGURACION
# ============================================================================

BACKEND_URL = "http://localhost:8000/api/v1"
DBF_FOLDER = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")

# Archivos DBF
CLIENTES_DBF = DBF_FOLDER / "clientes.dbf"
AGENTES_DBF = DBF_FOLDER / "agentes.dbf"

# Cuantos registros enviar por llamada (no cambiar)
BATCH_SIZE = 200

# Credenciales de admin
USERNAME = "admin"
PASSWORD = "farmasaenz123"


# ============================================================================
# HELPERS - Funciones auxiliares para limpiar datos
# ============================================================================

def limpiar_digitos(valor):
    """Quita todo excepto numeros"""
    if not valor or str(valor).lower() == 'nan':
        return ""
    return re.sub(r"\D", "", str(valor))


def limpiar_lada(lada):
    """Limpia codigo de area (lada) mexicana"""
    lada = limpiar_digitos(lada)
    
    # Quitar prefijos comunes
    if lada.startswith(("044", "045")):
        lada = lada[3:]
    elif lada.startswith("01"):
        lada = lada[2:]
    
    # Lada valida: 2 o 3 digitos
    if lada.isdigit() and len(lada) in (2, 3):
        return lada
    return ""


def construir_telefono(lada, numero):
    """Construye telefono en formato internacional +52XXXXXXXXXX"""
    numero = limpiar_digitos(numero)
    lada = limpiar_lada(lada)
    
    # Celular o telefono moderno (10 digitos)
    if len(numero) == 10:
        return f"+52{numero}"
    
    # Telefono fijo antiguo (8 digitos + lada)
    if len(numero) == 8 and lada:
        return f"+52{lada}{numero}"
    
    return None


def normalizar_texto(texto):
    """Quita acentos y convierte a mayusculas"""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    return texto.upper()


def limpiar_nombre(nombre):
    """Limpia un nombre para username"""
    nombre = normalizar_texto(nombre)
    # Quitar contenido entre parentesis
    nombre = re.sub(r"\(.*?\)", "", nombre)
    # Quitar simbolos raros
    nombre = re.sub(r"[^\w\s]", " ", nombre)
    # Colapsar espacios multiples
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre


def crear_username(nombre, id_cliente):
    """Crea un username unico y valido"""
    PALABRAS_LEGALES = [
        "S DE RL DE CV","S DE RL", "S DE R L", "S DE R.L",
        "SA DE CV", "S A DE C V", "S.A. DE C.V.",
        "SA", "S.A.", "DE CV", "SOCIEDAD"
    ]
    
    base = limpiar_nombre(nombre).lower()
    
    # Si es empresa, quitar sufijos legales SOLO al final del nombre
    # Esto previene que nombres como "SALVADOR" se corten incorrectamente
    for palabra in PALABRAS_LEGALES:
        # Buscar con espacio antes: " SA" no coincide con "SALVADOR"
        palabra_con_espacio = " " + palabra.lower()
        if base.endswith(palabra_con_espacio):
            base = base[:-len(palabra_con_espacio)].strip()
            break
        # Si el nombre ES exactamente la palabra legal, mantenerlo
        elif base == palabra:
            # Nombres como "SA" solos son muy raros, pero manejarlos
            pass
    
    # Reemplazar espacios con guion bajo
    base = base.replace(" ", "_")
    
    # Limitar largo (para no tener usernames gigantes)
    base = base[:50].rstrip("_")
    
    # Si después de limpiar quedó vacío, usar placeholder
    if not base:
        base = "CLIENTE"
    
    return f"{base}_{id_cliente}"


# ============================================================================
# API - Funciones para comunicarse con el backend
# ============================================================================

def login():
    """Hace login y retorna el token"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/auth/login",
            data={"username": USERNAME, "password": PASSWORD}
        )
        response.raise_for_status()
        return response.json()["access_token"]
    except Exception as e:
        print(f"❌ Error de login: {e}")
        return None


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
        print(f"❌ Error syncing sellers: {e}")
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
        print(f"\n      ❌ HTTP Error: {error_detail}")
        return {"creados": 0, "actualizados": 0, "errores": len(clientes)}
    except Exception as e:
        print(f"\n      ❌ Error: {e}")
        return {"creados": 0, "actualizados": 0, "errores": len(clientes)}


# ============================================================================
# PROCESADORES - Leen DBF y preparan datos
# ============================================================================

def procesar_vendedores():
    """Lee AGENTES.DBF y retorna lista de vendedores"""
    if not AGENTES_DBF.exists():
        print(f"⚠️  Archivo no encontrado: {AGENTES_DBF}")
        return []
    
    try:
        # Leer DBF
        df = pd.DataFrame(iter(DBF(AGENTES_DBF, encoding='latin-1', ignore_missing_memofile=True)))
        df = df[df['CVE_AGE'].notna()].copy()
        
        print(f"📊 {len(df)} vendedores en DBF")
        
        # Convertir a formato API
        vendedores = []
        for _, row in df.iterrows():
            # Username = primer nombre + id (ej: bernardo_123)
            primer_nombre = row['NOM_AGE'].split()[0].lower()
            
            vendedor = {
                "user_id": int(row['CVE_AGE']),
                "username": f"{primer_nombre}_{row['CVE_AGE']}",
                "email": row.get("EMAIL_AGE") or f"vendedor{row['CVE_AGE']}@farmacruz.com",
                "full_name": row['NOM_AGE'],
                "password": "vendedor2026",
                "is_active": True,
                "updated_at": datetime.now(timezone.utc).isoformat()    
            }
            vendedores.append(vendedor)
        
        return vendedores
        
    except Exception as e:
        print(f"❌ Error leyendo vendedores: {e}")
        return []


def procesar_clientes():
    """Lee CLIENTES.DBF y retorna lista de clientes"""
    if not CLIENTES_DBF.exists():
        print(f"⚠️  Archivo no encontrado: {CLIENTES_DBF}")
        return []
    
    try:
        # Leer DBF
        df = pd.DataFrame(iter(DBF(CLIENTES_DBF, encoding='latin-1', ignore_missing_memofile=True)))
        df = df[df['CVE_CTE'].notna()].copy()
        
        print(f"📊 {len(df)} clientes en DBF")
        
        # Convertir a formato API
        clientes = []
        for _, row in df.iterrows():
            try:
                # Crear direccion completa
                direccion = (
                    f"{row.get('DIR_CTE', '')} "
                    f"{row.get('COL_CTE', '')} "
                    f"{row.get('CD_CTE', '')} "
                    f"{row.get('EDO_CTE', '')} "
                    f"{row.get('CP_CTE', '')}"
                ).strip()
                
                # Telefonos
                lada = row.get("LADA_CTE", "")
                tel1 = construir_telefono(lada, row.get("TEL1_CTE", ""))
                tel2 = construir_telefono(lada, row.get("TEL2_CTE", ""))
                
                cliente = {
                    "customer_id": int(row['CVE_CTE']),
                    "username": crear_username(row.get('NOM_CTE', 'CLIENTE'), row['CVE_CTE']),
                    "email": row.get("EMAIL_CTE") or f"cliente{row['CVE_CTE']}@farmacruz.com",
                    "full_name": str(row.get('NOM_CTE', 'N/A')).strip(),
                    "password": "farmacruz2026",
                    "agent_id": str(row.get('CVE_AGE')) if row.get('CVE_AGE') else None,
                    "business_name": str(row.get('NOM_FAC', row.get('NOM_CTE', ''))).strip(),
                    "rfc": str(row.get('RFC_CTE', ''))[:13] or None,
                    "price_list_id": int(float(row['LISTA_PREC'])) if row.get('LISTA_PREC') else None,
                    "address_1": direccion or None,
                    "address_2": None,
                    "address_3": None,
                    "telefono_1": tel1,
                    "telefono_2": tel2,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                clientes.append(cliente)
                
            except Exception as e:
                print(f"⚠️  Cliente {row.get('CVE_CTE')} falló: {e}")
                continue
        
        return clientes
        
    except Exception as e:
        print(f"❌ Error leyendo clientes: {e}")
        return []


# ============================================================================
# MAIN - Ejecucion principal
# ============================================================================

def main():
    """Funcion principal de sincronizacion"""
    inicio = datetime.now(timezone.utc)
    print(f"\n{'='*60}")
    print(f"🔄 Sync DBF → PostgreSQL")
    print(f"⏰ {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Login
    token = login()
    if not token:
        print("❌ No se pudo hacer login. Abortando.\n")
        return
    
    # 2. Procesar vendedores
    print("👤 Sincronizando vendedores...")
    vendedores = procesar_vendedores()
    if vendedores:
        resultado = sync_vendedores(token, vendedores)
        print(f"   ✅ {resultado.get('creados', 0)} creados, {resultado.get('actualizados', 0)} actualizados\n")
    
    # 3. Procesar clientes
    print("👥 Sincronizando clientes...")
    clientes = procesar_clientes()
    
    if not clientes:
        print("   ⚠️  No hay clientes para sincronizar\n")
    else:
        total_creados = 0
        total_actualizados = 0
        total_errores = 0
        
        # Calcular número de batches
        num_batches = (len(clientes) + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"   📦 Enviando en {num_batches} batches de {BATCH_SIZE}...")
        
        # Enviar en batches
        for i in range(0, len(clientes), BATCH_SIZE):
            batch_num = (i // BATCH_SIZE) + 1
            batch = clientes[i:i + BATCH_SIZE]
            print(f"   📤 Batch {batch_num}/{num_batches}: {len(batch)} clientes...", end=" ")
            
            resultado = sync_clientes(token, batch)
            
            total_creados += resultado.get('creados', 0)
            total_actualizados += resultado.get('actualizados', 0)
            total_errores += resultado.get('errores', 0)
            
            # Mostrar detalles de errores si existen
            errores_detalle = resultado.get('detalle_errores', [])
            if errores_detalle:
                print(f"✗")
                for error in errores_detalle[:3]:  # Solo mostrar primeros 3 errores
                    print(f"      → {error}")
                if len(errores_detalle) > 3:
                    print(f"      ... y {len(errores_detalle) - 3} errores más")
            else:
                print(f"✓ ({resultado.get('creados', 0)} creados, {resultado.get('actualizados', 0)} actualizados, {resultado.get('errores', 0)} errores)")
        
        print(f"\n   ✅ TOTAL: {total_creados} creados, {total_actualizados} actualizados")
        if total_errores > 0:
            print(f"   ⚠️  {total_errores} errores")
        print()
    
    # 4. Resumen final
    fin = datetime.now(timezone.utc)
    duracion = (fin - inicio).total_seconds()
    
    print(f"{'='*60}")
    print(f"✅ Sync completado en {duracion:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
