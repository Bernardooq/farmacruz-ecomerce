"""
Builders - Funciones para construir diccionarios de entidades.
"""

from .data_cleaning import (
    limpiar_texto, limpiar_numero, construir_telefono, crear_username
)

# ============================================================================
# PRODUCTO
# ============================================================================

def build_producto_dict(row, descripciones_map, stock_map, verificar_imagen_fn, sync_time):
    """
    Construye diccionario de producto desde una fila del DBF.
    
    Args:
        row: Fila del DataFrame (producto.dbf)
        descripciones_map: Dict {producto_id: descripcion_larga}
        stock_map: Dict {producto_id: stock}
        verificar_imagen_fn: Función para verificar imagen
        sync_time: Timestamp de sincronización
    
    Returns:
        dict: Producto formateado para el API
    """
    producto_id = limpiar_texto(row.get('CVE_PROD'))
    
    # Descripcion tecnica formateada
    desc_tecnica_parts = []
    if row.get('FACT_PESO'):
        desc_tecnica_parts.append(f"Costo Público: {limpiar_texto(row.get('FACT_PESO'))}")
    if row.get('DATO_4'):
        desc_tecnica_parts.append(f"Caja: {limpiar_texto(row.get('DATO_4'))}")
    desc_tecnica = " | ".join(desc_tecnica_parts) or None
    
    return {
        "product_id": producto_id,
        "codebar": limpiar_texto(row.get('CODBAR')) or None,
        "name": limpiar_texto(row.get('DESC_PROD'))[:255] or "Sin Nombre",
        "description": desc_tecnica,
        "descripcion_2": descripciones_map.get(producto_id),
        "stock_count": int(stock_map.get(producto_id, 0)),
        "base_price": limpiar_numero(row.get('CTO_ENT')),
        "iva_percentage": limpiar_numero(row.get('PORCENIVA'), 16.0),
        "category_name": limpiar_texto(row.get('CSE_PROD')) or None,
        "is_active": True,
        "unidad_medida": limpiar_texto(row.get('UNI_MED')) or None,
        "image_url": verificar_imagen_fn(producto_id),
        "updated_at": sync_time
    }


# ============================================================================
# CATEGORIA
# ============================================================================

def build_categoria_dict(nombre, sync_time):
    """Construye diccionario de categoría."""
    return {
        "name": nombre,
        "description": None,
        "updated_at": sync_time
    }


# ============================================================================
# VENDEDOR (SELLER)
# ============================================================================

def build_vendedor_dict(row, sync_time=None):
    """
    Construye diccionario de vendedor desde una fila del DBF.
    
    Args:
        row: Fila del DataFrame (agentes.dbf)
        sync_time: Timestamp de sincronización (opcional)
    
    Returns:
        dict: Vendedor formateado para el API
    """
    primer_nombre = row['NOM_AGE'].split()[0].lower()
    
    vendedor = {
        "user_id": int(row['CVE_AGE']),
        "username": f"{primer_nombre}_S{row['CVE_AGE']}",
        "email": row.get('EMAIL_AGE') or f"seller{row['CVE_AGE']}@farmacruz.com",
        "full_name": str(row.get('NOM_AGE', '')).strip(),
        "password": "vendedor2026",
        "is_active": True
    }
    
    if sync_time:
        vendedor["updated_at"] = sync_time
    
    return vendedor


# ============================================================================
# CLIENTE (CUSTOMER)
# ============================================================================

def build_cliente_dict(row, sync_time=None):
    """
    Construye diccionario de cliente desde una fila del DBF.
    
    Args:
        row: Fila del DataFrame (clientes.dbf)
        sync_time: Timestamp de sincronización (opcional)
    
    Returns:
        dict: Cliente formateado para el API
    """
    cid = int(row['CVE_CTE'])
    
    # Dirección completa
    direccion = (
        f"{row.get('DIR_CTE', '')} "
        f"{row.get('COL_CTE', '')} "
        f"{row.get('CD_CTE', '')}"
    ).strip() or None
    
    cliente = {
        "customer_id": cid,
        "username": crear_username(row.get('NOM_CTE', 'CLIENTE'), cid),
        "email": row.get('EMAIL_CTE') or f"client{cid}@farmacruz.com",
        "full_name": str(row.get('NOM_CTE', '')).strip(),
        "password": "farmacruz2026",
        "agent_id": str(row['CVE_AGE']) if row.get('CVE_AGE') else None,
        "business_name": str(row.get('NOM_FAC', row.get('NOM_CTE', ''))).strip(),
        "rfc": str(row.get('RFC_CTE', ''))[:13] or None,
        "price_list_id": int(float(row['LISTA_PREC'])) if row.get('LISTA_PREC') else None,
        "address_1": direccion,
        "telefono_1": construir_telefono(row.get('LADA_CTE'), row.get('TEL1_CTE')),
        "telefono_2": construir_telefono(row.get('LADA_CTE'), row.get('TEL2_CTE'))
    }
    
    if sync_time:
        cliente["updated_at"] = sync_time
    
    return cliente


# ============================================================================
# LISTA DE PRECIOS
# ============================================================================

def build_lista_precios_dict(lista_id, sync_time):
    """Construye diccionario de lista de precios."""
    return {
        "price_list_id": int(lista_id),
        "list_name": f"Lista {int(lista_id)}",
        "description": None,
        "is_active": True,
        "updated_at": sync_time
    }


# ============================================================================
# ITEM DE LISTA
# ============================================================================

def build_item_lista_dict(row, sync_time):
    """Construye diccionario de item de lista de precios."""
    return {
        "price_list_id": int(limpiar_texto(row.get('NLISPRE'))),
        "product_id": limpiar_texto(row.get('CVE_PROD')),
        "markup_percentage": limpiar_numero(row.get('LMARGEN')),
        "final_price": limpiar_numero(row.get('LPRECPROD')),
        "updated_at": sync_time
    }
