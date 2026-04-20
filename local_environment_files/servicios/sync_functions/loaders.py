"""
Loaders - Funciones para cargar datos auxiliares desde DBFs.
"""

import pandas as pd
from dbfread import DBF
from .data_cleaning import limpiar_numero


def cargar_descripciones_extra(dbf_path):
    """
    Lee pro_desc.dbf y retorna mapa de descripciones largas.
    
    Returns:
        dict: {producto_id: descripcion_larga}
    """
    if not dbf_path.exists():
        print(f"Warning: {dbf_path.name} not found, skipping extra descriptions")
        return {}
    
    try:
        print("Loading extra descriptions...")
        dbf = DBF(dbf_path, encoding='latin1', ignore_missing_memofile=True)
        return {r['CVE_PROD'].strip(): r['DESC1'].strip() for r in dbf if r.get('CVE_PROD') and r.get('DESC1')}
    except Exception as e:
        print(f"Error reading descriptions: {e}")
        return {}


def cargar_existencias(dbf_path):
    """
    Lee existe.dbf y retorna mapa de stock.
    
    Returns:
        dict: {producto_id: cantidad_en_stock}
    """
    if not dbf_path.exists():
        print(f"Warning: {dbf_path.name} not found, stock will default to 0")
        return {}
    
    try:
        print("Loading stock data...")
        dbf = DBF(dbf_path, encoding='latin1', ignore_missing_memofile=True)
        
        stock_map = {}
        for r in dbf:
            pid = r.get('CVE_PROD')
            if not pid:
                continue
            
            pid = pid.strip()
            
            # Obtener el valor de EXISTENCIA previniendo None
            val = r.get('EXISTENCIA')
            if val is None: val = r.get('EXISTE')
            if val is None: val = r.get('STOCK')
            if val is None: val = 0
            
            try:
                # Convertir a float antes de int por casos como "316.0"
                cantidad_int = int(float(limpiar_numero(val) or 0))
            except (ValueError, TypeError):
                cantidad_int = 0
                
            stock_map[pid] = stock_map.get(pid, 0) + cantidad_int
            
        return stock_map
    except Exception as e:
        print(f"Error reading stock: {e}")
        return {}


def dbf_to_dataframe(dbf_path):
    """Convierte DBF a DataFrame de pandas."""
    print(f"Reading {dbf_path.name}...")
    dbf = DBF(dbf_path, encoding='latin1', ignore_missing_memofile=True)
    return pd.DataFrame(iter(dbf))
