"""
Sincronizacion DBF -> FarmaCruz Backend v2.0
- Soporte para pro_desc (descripciones largas)
- Soporte para existe (stock real)
- Filtro de seguridad CVE_TIAL
- Ignora errores de archivos memo (.fpt/.dbt) faltantes
"""

import pandas as pd
import requests
from dbfread import DBF
from pathlib import Path
import logging
from datetime import datetime 

# ================= CONFIGURACIoN =================
BACKEND_URL = "http://localhost:8000/api/v1"
CREDENTIALS = {"username": "admin", "password": "farmasaenz123"}

CLOUD_FRONT = "farmacruz-ecomerce"

# Directorios
# DBF_DIR = Path("/Users/bernardoorozco/Documents/GitHub/farmacruz-ecomerce/backend/dbfs")
DBF_DIR = Path("C:\\Users\\berna\\Documents\\GitProjects\\farmacruz-ecomerce\\backend\\dbfs")
DBF_PRODUCTOS = DBF_DIR / "producto.dbf"
DBF_PRECIOLIS = DBF_DIR / "PRECIPROD.DBF"
DBF_EXISTE    = DBF_DIR / "existe.dbf"
DBF_PROD_DESC = DBF_DIR / "pro_desc.dbf"

# Configuracion de Lotes (Batches)
BATCH_SIZE = {
    "CAT": 100,
    "PROD": 500,
    "LIST": 100,
    "REL": 1000
}

# Filtros
BLACKLIST_TIAL = {'99999', '99998', '100', '99'}

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ================= UTILIDADES =================
def clean_str(val):
    """Limpia cadenas, eliminando espacios y manejando Nones"""
    if val is None:
        return ""
    return str(val).strip()

def clean_numeric(val, default=0.0):
    """Convierte a float seguro"""
    try:
        if pd.isna(val): return default
        return float(str(val).replace(",", ""))
    except:
        return default

# ================= CARGA DE DATOS AUXILIARES =================
def cargar_mapa_descripciones():
    """
    Carga pro_desc.dbf en memoria.
    Retorna dict: { 'CVE_PROD': 'DESC1' }
    """
    if not DBF_PROD_DESC.exists():
        logger.warning(f"No se encontro {DBF_PROD_DESC}, se omitiran descripciones extra.")
        return {}

    logger.info("Cargando mapa de descripciones (pro_desc)...")
    try:
        # ignore_missing_memofile=True es clave aqui
        dbf = DBF(DBF_PROD_DESC, encoding='latin1', ignore_missing_memofile=True)
        return {r['CVE_PROD'].strip(): r['DESC1'].strip() for r in dbf}
    except Exception as e:
        logger.error(f"Error cargando pro_desc: {e}")
        return {}

def cargar_mapa_existencias():
    """
    Carga existe.dbf en memoria.
    Retorna dict: { 'CVE_PROD': STOCK_FLOAT }
    """
    if not DBF_EXISTE.exists():
        logger.warning(f"No se encontro {DBF_EXISTE}, el stock sera 0.")
        return {}

    logger.info("Cargando mapa de existencias (existe)...")
    try:
        dbf = DBF(DBF_EXISTE, encoding='latin1', ignore_missing_memofile=True)
        # Si hay multiples almacenes, aqui se sobrescribe con el ultimo encontrado.
        # Si necesitas sumar, avisame para cambiar la logica.
        return {r['CVE_PROD'].strip(): clean_numeric(r['EXISTENCIA']) for r in dbf}
    except Exception as e:
        logger.error(f"Error cargando existe: {e}")
        return {}

# ================= API CLIENT =================
def login() -> str:
    logger.info("Autenticando en el backend...")
    try:
        resp = requests.post(f"{BACKEND_URL}/auth/login", data=CREDENTIALS)
        resp.raise_for_status()
        token = resp.json()["access_token"]
        logger.info("Login exitoso.")
        return token
    except Exception as e:
        logger.critical(f"Fallo el login: {e}")
        raise

def send_in_batches(payload_list, batch_size, endpoint, token, entity_name):
    """Envia datos genericos en lotes para no saturar el servidor"""
    if not payload_list:
        logger.info(f"{entity_name} - Nada que sincronizar.")
        return

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    total_created, total_updated, total_errors = 0, 0, 0
    total_items = len(payload_list)

    logger.info(f"{entity_name} - Iniciando sincronizacion de {total_items} registros...")

    for i in range(0, total_items, batch_size):
        batch = payload_list[i:i+batch_size]
        try:
            resp = requests.post(f"{BACKEND_URL}/{endpoint}", json=batch, headers=headers)
            resp.raise_for_status()
            res = resp.json()
            
            c = res.get('creados', 0)
            u = res.get('actualizados', 0)
            e = res.get('errores', 0)
            
            total_created += c
            total_updated += u
            total_errors += e

            logger.info(f"   Lote {i//batch_size + 1}: +{c} creados, ~{u} actualizados, !{e} errores")
            
            if e > 0 and res.get('detalle_errores'):
                logger.warning(f"   Detalle errores: {res.get('detalle_errores')[:2]}...")

        except Exception as err:
            logger.error(f"   FATAL Lote {i}: {err}")
            total_errors += len(batch)

    logger.info(f"Reporte {entity_name}: {total_created} Creados | {total_updated} Actualizados | {total_errors} Errores")

# ================= LoGICA DE SINCRONIZACIoN =================

def sync_categories(df_productos, token, fecha_inicio):
    # Extraer categorias unicas
    cats = df_productos['CSE_PROD'].dropna().apply(clean_str).unique()
    # Filtrar basura
    cats = [c for c in cats if c and c.upper() != 'GASTOS' and c != '99999']

    payload = [{"name": c, "description": None, "updated_at": fecha_inicio} for c in cats]
    send_in_batches(payload, BATCH_SIZE["CAT"], "sync/categories", token, "Categorias")

def sync_products(df_productos, map_desc, map_stock, token, fecha_inicio):
    logger.info("Procesando productos para envio...")
    payload = []

    for _, row in df_productos.iterrows():
        # 1. Filtro de Categoria (existente)
        cat = clean_str(row.get('CSE_PROD'))
        if cat.upper() == 'GASTOS' or cat == '99999':
            continue

        # 2. NUEVO FILTRO: CVE_TIAL (Lista Negra)
        cve_tial = clean_str(row.get('CVE_TIAL'))
        if cve_tial in BLACKLIST_TIAL:
            continue

        cve_prod = clean_str(row.get('CVE_PROD'))

        # Construccion de descripcion tecnica (base)
        desc_base = " | ".join(filter(None, [
            f"Costo Público: {clean_str(row.get('FACT_PESO'))}" if row.get('FACT_PESO') else None,
            f"Unidad: {clean_str(row.get('DATO_4'))}" if row.get('DATO_4') else None
        ])) or None

        # Obtener datos de los mapas auxiliares
        stock_real = map_stock.get(cve_prod, 0.0)      # Viene de 'existe.dbf'
        desc_extra = map_desc.get(cve_prod, None)      # Viene de 'pro_desc.dbf'

        # Limpiar Codebar
        codebar = clean_str(row.get('CODBAR'))
        if not codebar: codebar = None

        producto = {
            "product_id": cve_prod,
            "codebar": codebar,
            "name": clean_str(row.get('DESC_PROD'))[:255] or "Sin Nombre",
            "description": desc_base,           # Descripcion tecnica
            "descripcion_2": desc_extra,        # Descripcion larga (pro_desc)
            "stock_count": int(stock_real),     # Stock real (existe)
            "base_price": clean_numeric(row.get('CTO_ENT')),
            "iva_percentage": clean_numeric(row.get('PORCENIVA'), 16.0),
            "category_name": cat or None,
            "is_active": True,
            "unidad_medida": clean_str(row.get('DATO_4')) or None,
            "updated_at": fecha_inicio,
            "image_url": f"{CLOUD_FRONT}/{cve_prod}.webp"  # Asumiendo extension webp
        }
        payload.append(producto)

    send_in_batches(payload, BATCH_SIZE["PROD"], "sync/products", token, "Productos")

# ===== SINCRONIZAR LISTAS DE PRECIOS =====

def sync_price_lists(df_preciprod, token, fecha_inicio):
    """Sincroniza solo las listas de precios (sin items)"""
    logger.info("Procesando listas de precios para envio...")
    # Extraer listas de precios unicas
    listas = df_preciprod['NLISPRE'].dropna().apply(clean_str).unique()

    listas_array = []
    for lista in listas:
        listas_array.append({
            "price_list_id": int(lista),
            "list_name": f"Lista {lista}",
            "description": None,
            "is_active": True,
            "updated_at": fecha_inicio
        })

    # Enviar listas de precios
    send_in_batches(listas_array, BATCH_SIZE['LIST'], "sync/price-lists", token, "Listas de Precios")
    return listas

def sync_price_list_items(df_preciprod, listas, token, fecha_inicio):
    """Sincroniza los items de cada lista de precios con sus markups"""
    logger.info("Procesando items de todas las listas de precios...")
    
    # Preparar TODOS los items de TODAS las listas de una sola vez
    all_items_payload = []
    
    for lista in listas:
        df_lista = df_preciprod[df_preciprod['NLISPRE'].apply(clean_str) == lista]
        price_list_id = int(lista)

        for _, row in df_lista.iterrows():
            cve_prod = clean_str(row.get('CVE_PROD'))
            markup_percentage = clean_numeric(row.get('LMARGEN'))
            final_price = clean_numeric(row.get('LPRECPROD'))

            all_items_payload.append({
                "price_list_id": price_list_id,
                "product_id": cve_prod,
                "markup_percentage": markup_percentage,
                "final_price": final_price,
                "updated_at": fecha_inicio
            })

    # Enviar TODOS los items en lotes
    send_in_batches(
        all_items_payload,
        BATCH_SIZE['REL'],
        "sync/price-list-items",
        token,
        "Items de Listas de Precios"
    )

# ===== ENVIAR FECHA DE LIMPIEZA =====
def date_rm_sync(datetimep, token):
    """Manda la fecha de ultima sincronizacion al backend, los items que no fueron actualizados desde esa fecha seran desactivados o eliminados."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"last_sync": datetimep}
    try:
        resp = requests.post(f"{BACKEND_URL}/sync/cleanup", json=payload, headers=headers)
        resp.raise_for_status()
        logger.info("Fecha de limpieza enviada correctamente.")
    except Exception as e:
        logger.error(f"Error enviando fecha de limpieza: {e}")

# ================= MAIN =================
def main():
    print("INICIANDO SINCRONIZACIoN FARMACRUZ")
    fecha_inicio = datetime.now().isoformat()
    logger.info(f"Fecha de inicio: {fecha_inicio}")
    # 1. Login
    try:
        token = login()
    except:
        return # Salir si no hay login

    # 2. Cargar Mapas Auxiliares (Memoria)
    map_desc = cargar_mapa_descripciones()
    map_stock = cargar_mapa_existencias()

    # 3. Cargar DBF Productos y Precios
    logger.info(f"Leyendo DBF Principal: {DBF_PRODUCTOS}...")
    # ignore_missing_memofile=True evita crasheos si faltan .fpt
    df_prods = pd.DataFrame(iter(DBF(DBF_PRODUCTOS, encoding='latin1', ignore_missing_memofile=True)))
    
    logger.info(f"Leyendo DBF Precios: {DBF_PRECIOLIS}...")
    df_preci = pd.DataFrame(iter(DBF(DBF_PRECIOLIS, encoding='latin1', ignore_missing_memofile=True)))

    # Limpieza inicial de DataFrames (Strings vacios en lugar de NaN)
    df_prods = df_prods.map(lambda x: clean_str(x) if isinstance(x, str) else x)

    # 4. Ejecutar Sincronizacion
    sync_categories(df_prods, token, fecha_inicio)
    sync_products(df_prods, map_desc, map_stock, token, fecha_inicio)
    
    # 5. Sincronizar listas de precios y sus items
    listas = sync_price_lists(df_preci, token, fecha_inicio)
    sync_price_list_items(df_preci, listas, token, fecha_inicio)
    date_rm_sync(fecha_inicio, token)

    print("SINCRONIZACIoN COMPLETADA EXITOSAMENTE")

if __name__ == "__main__":
    main()