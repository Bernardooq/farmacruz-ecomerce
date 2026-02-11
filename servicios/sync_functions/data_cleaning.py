"""
Data Cleaning - Funciones de limpieza de datos para scripts de sincronización.
"""

import re
import unicodedata
import pandas as pd

# ============================================================================
# LIMPIEZA DE TEXTO
# ============================================================================

def limpiar_texto(valor):
    """Limpia strings eliminando espacios"""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return None
    return str(valor).strip()


def normalizar_texto(texto):
    """Quita acentos y convierte a mayusculas"""
    if not texto:
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
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


# ============================================================================
# LIMPIEZA DE NÚMEROS
# ============================================================================

def limpiar_numero(valor, default=0.0):
    """Convierte a numero float de forma segura"""
    if pd.isna(valor) or valor == '':
        return default
    try:
        return float(str(valor).replace(",", ""))
    except:
        return default


# ============================================================================
# TELÉFONOS
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


# ============================================================================
# USERNAMES
# ============================================================================

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
            pass
    
    base = base.replace(" ", "_")
    base = base[:50].rstrip("_")
    
    if not base:
        base = "CLIENTE"
    
    return f"{base}_{id_cliente}"
