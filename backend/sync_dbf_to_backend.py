"""
Sincronizador de Productos DBF → PostgreSQL
============================================

Lee los archivos DBF del sistema viejo y sincroniza:
- Categorías
- Productos (con stock desde existe.dbf)
- Listas de precios
- Items de listas (markups por producto)

Corre cada X horas via Task Scheduler o como Windows Service.

Autor: Farmacruz Team
"""

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
IMAGES_FOLDER = Path("/Users/bernardoorozco/Downloads/CompressedImg")

# Archivos DBF
PRODUCTOS_DBF = DBF_FOLDER / "producto.dbf"
PRECIOS_DBF = DBF_FOLDER / "PRECIPROD.DBF"
EXISTENCIAS_DBF = DBF_FOLDER / "existe.dbf"
DESCRIPCIONES_DBF = DBF_FOLDER / "pro_desc.dbf"

# Cuantos registros enviar por llamada
BATCH_SIZE = {
    "categorias": 100,
    "productos": 500,
    "listas": 100,
    "items": 1000
}

# Productos a ignorar (filtro de seguridad)
PRODUCTOS_BLOQUEADOS = {'99999', '99998', '100', '99'}
CATEGORIA_BLOQUEADA = 'GASTOS'

# CDN para imagenes (CloudFront)
CDN_URL = "https://digheqbxnmxr3.cloudfront.net/images"

# Credenciales de admin
USERNAME = "admin"
PASSWORD = "farmasaenz123"


# ============================================================================
# HELPERS - Funciones auxiliares
# ============================================================================

def limpiar_texto(valor):
    """Limpia strings eliminando espacios"""
    if valor is None:
        return ""
    return str(valor).strip()


def verificar_imagen_existe(producto_id):
    """
    Verifica si existe la imagen del producto en la carpeta local
    Retorna la URL del CDN si existe, None si no existe
    """
    imagen_path = IMAGES_FOLDER / f"{producto_id}.webp"
    if imagen_path.exists():
        return f"{CDN_URL}/{producto_id}.webp"
    return None


def limpiar_numero(valor, default=0.0):
    """Convierte a numero float de forma segura"""
    try:
        if pd.isna(valor):
            return default
        return float(str(valor).replace(",", ""))
    except:
        return default


def cargar_descripciones_extra():
    """
    Lee pro_desc.dbf y retorna mapa de descripciones largas
    Retorna: {producto_id: descripcion_larga}
    """
    if not DESCRIPCIONES_DBF.exists():
        print(f"⚠️  Archivo {DESCRIPCIONES_DBF.name} no encontrado, se omitiran descripciones extra")
        return {}
    
    print(f"📄 Cargando descripciones extra...")
    try:
        dbf = DBF(DESCRIPCIONES_DBF, encoding='latin1', ignore_missing_memofile=True)
        return {r['CVE_PROD'].strip(): r['DESC1'].strip() for r in dbf}
    except Exception as e:
        print(f"❌ Error leyendo descripciones: {e}")
        return {}


def cargar_existencias():
    """
    Lee existe.dbf y retorna mapa de stock
    Retorna: {producto_id: cantidad_en_stock}
    """
    if not EXISTENCIAS_DBF.exists():
        print(f"⚠️  Archivo {EXISTENCIAS_DBF.name} no encontrado, stock sera 0")
        return {}
    
    print(f"📦 Cargando existencias...")
    try:
        dbf = DBF(EXISTENCIAS_DBF, encoding='latin1', ignore_missing_memofile=True)
        return {r['CVE_PROD'].strip(): limpiar_numero(r['EXISTENCIA']) for r in dbf}
    except Exception as e:
        print(f"❌ Error leyendo existencias: {e}")
        return {}


# ============================================================================
# API - Comunicacion con el backend
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


def enviar_batch(datos, endpoint, token, nombre):
    """Envia un lote de datos al backend"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/{endpoint}",
            json=datos,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error en {nombre}: {e}")
        return {"creados": 0, "actualizados": 0, "errores": len(datos)}


def enviar_en_lotes(datos, batch_size, endpoint, token, nombre):
    """Divide datos en lotes y los envia al backend"""
    if not datos:
        print(f"⚠️  {nombre}: No hay datos para sincronizar")
        return
    
    total = len(datos)
    creados = 0
    actualizados = 0
    errores = 0
    
    print(f"📤 {nombre}: Enviando {total} registros...")
    
    for i in range(0, total, batch_size):
        lote = datos[i:i + batch_size]
        resultado = enviar_batch(lote, endpoint, token, nombre)
        
        creados += resultado.get('creados', 0)
        actualizados += resultado.get('actualizados', 0)
        errores += resultado.get('errores', 0)
    
    print(f"   ✅ {creados} creados, {actualizados} actualizados, {errores} errores")


def enviar_fecha_limpieza(fecha, token):
    """
    Envia la fecha de sync al backend.
    Los registros no actualizados desde esa fecha seran desactivados/eliminados.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/sync/cleanup",
            json={"last_sync": fecha},
            headers=headers
        )
        response.raise_for_status()
        print("🧹 Limpieza de registros antiguos completada")
    except Exception as e:
        print(f"⚠️  Error en limpieza: {e}")


# ============================================================================
# PROCESADORES - Lectura y preparacion de datos
# ============================================================================

def procesar_categorias(df_productos, fecha_sync):
    """Extrae categorias unicas de los productos"""
    # Obtener categorias unicas
    categorias = df_productos['CSE_PROD'].dropna().apply(limpiar_texto).unique()
    
    # Filtrar categorias invalidas
    categorias = [
        c for c in categorias 
        if c and c.upper() != CATEGORIA_BLOQUEADA and c not in PRODUCTOS_BLOQUEADOS
    ]
    
    # Convertir a formato API
    return [
        {
            "name": cat,
            "description": None,
            "updated_at": fecha_sync
        }
        for cat in categorias
    ]


def procesar_productos(df_productos, descripciones_extra, stock_map, fecha_sync):
    """Lee productos del DBF y los prepara para el backend"""
    print("📦 Procesando productos...")
    productos = []
    
    for _, row in df_productos.iterrows():
        # Filtro 1: Categoria bloqueada
        categoria = limpiar_texto(row.get('CSE_PROD'))
        if categoria.upper() == CATEGORIA_BLOQUEADA or categoria in PRODUCTOS_BLOQUEADOS:
            continue
        
        # Filtro 2: Producto bloqueado por CVE_TIAL
        cve_tial = limpiar_texto(row.get('CVE_TIAL'))
        if cve_tial in PRODUCTOS_BLOQUEADOS:
            continue
        
        # ID del producto
        producto_id = limpiar_texto(row.get('CVE_PROD'))
        
        # Descripcion tecnica (info adicional)
        desc_tecnica_parts = []
        if row.get('FACT_PESO'):
            desc_tecnica_parts.append(f"Costo Público: {limpiar_texto(row.get('FACT_PESO'))}")
        if row.get('DATO_4'):
            desc_tecnica_parts.append(f"Unidad: {limpiar_texto(row.get('DATO_4'))}")
        desc_tecnica = " | ".join(desc_tecnica_parts) or None
        
        # Descripcion larga (de pro_desc.dbf)
        desc_larga = descripciones_extra.get(producto_id)
        
        # Stock (de existe.dbf)
        stock = int(stock_map.get(producto_id, 0))
        
        # Codigo de barras
        codebar = limpiar_texto(row.get('CODBAR')) or None
        
        # Construir producto
        producto = {
            "product_id": producto_id,
            "codebar": codebar,
            "name": limpiar_texto(row.get('DESC_PROD'))[:255] or "Sin Nombre",
            "description": desc_tecnica,
            "descripcion_2": desc_larga,
            "stock_count": stock,
            "base_price": limpiar_numero(row.get('CTO_ENT')),
            "iva_percentage": limpiar_numero(row.get('PORCENIVA'), 16.0),
            "category_name": categoria or None,
            "is_active": True,
            "unidad_medida": limpiar_texto(row.get('DATO_4')) or None,
            "image_url": verificar_imagen_existe(producto_id),
            "updated_at": fecha_sync
        }
        productos.append(producto)
    
    return productos


def procesar_listas_precios(df_precios, fecha_sync):
    """Extrae listas de precios unicas"""
    # Obtener IDs de listas unicas
    listas_ids = df_precios['NLISPRE'].dropna().apply(limpiar_texto).unique()
    
    # Convertir a formato API
    listas = [
        {
            "price_list_id": int(lista_id),
            "list_name": f"Lista {lista_id}",
            "description": None,
            "is_active": True,
            "updated_at": fecha_sync
        }
        for lista_id in listas_ids
    ]
    
    return listas, listas_ids


def procesar_items_listas(df_precios, listas_ids, fecha_sync):
    """Procesa los items (productos) de cada lista de precios con sus markups"""
    print("💰 Procesando items de listas de precios...")
    items = []
    
    for lista_id in listas_ids:
        # Filtrar items de esta lista
        df_lista = df_precios[df_precios['NLISPRE'].apply(limpiar_texto) == lista_id]
        
        for _, row in df_lista.iterrows():
            item = {
                "price_list_id": int(lista_id),
                "product_id": limpiar_texto(row.get('CVE_PROD')),
                "markup_percentage": limpiar_numero(row.get('LMARGEN')),
                "final_price": limpiar_numero(row.get('LPRECPROD')),
                "updated_at": fecha_sync
            }
            items.append(item)
    
    return items


# ============================================================================
# MAIN - Ejecucion principal
# ============================================================================

def main():
    """Funcion principal de sincronizacion"""
    inicio = datetime.now(timezone.utc)
    fecha_sync = inicio.isoformat()
    
    print(f"\n{'='*60}")
    print(f"🔄 Sync Productos DBF → PostgreSQL")
    print(f"⏰ {inicio.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 1. Login
    token = login()
    if not token:
        print("❌ No se pudo hacer login. Abortando.\n")
        return
    
    # 2. Cargar datos auxiliares (descripciones y stock)
    descripciones_extra = cargar_descripciones_extra()
    stock_map = cargar_existencias()
    
    # 3. Leer archivos DBF principales
    print(f"📖 Leyendo {PRODUCTOS_DBF.name}...")
    df_productos = pd.DataFrame(iter(DBF(PRODUCTOS_DBF, encoding='latin1', ignore_missing_memofile=True)))
    
    print(f"📖 Leyendo {PRECIOS_DBF.name}...")
    df_precios = pd.DataFrame(iter(DBF(PRECIOS_DBF, encoding='latin1', ignore_missing_memofile=True)))
    
    # Limpiar strings en DataFrames
    df_productos = df_productos.map(lambda x: limpiar_texto(x) if isinstance(x, str) else x)
    
    # 4. Procesar y enviar datos
    print()
    
    # Categorias
    categorias = procesar_categorias(df_productos, fecha_sync)
    enviar_en_lotes(categorias, BATCH_SIZE["categorias"], "sync/categories", token, "Categorías")
    
    # Productos
    productos = procesar_productos(df_productos, descripciones_extra, stock_map, fecha_sync)
    enviar_en_lotes(productos, BATCH_SIZE["productos"], "sync/products", token, "Productos")
    
    # Listas de precios
    listas, listas_ids = procesar_listas_precios(df_precios, fecha_sync)
    enviar_en_lotes(listas, BATCH_SIZE["listas"], "sync/price-lists", token, "Listas de Precios")
    
    # Items de listas (markups por producto)
    items = procesar_items_listas(df_precios, listas_ids, fecha_sync)
    enviar_en_lotes(items, BATCH_SIZE["items"], "sync/price-list-items", token, "Items de Listas")
    
    # 5. Limpieza de registros antiguos
    print()
    enviar_fecha_limpieza(fecha_sync, token)
    
    # 6. Resumen final
    fin = datetime.now(timezone.utc)
    duracion = (fin - inicio).total_seconds()
    
    print(f"\n{'='*60}")
    print(f"✅ Sync completado en {duracion:.1f}s")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()