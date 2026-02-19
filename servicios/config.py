"""
Configuración centralizada para scripts de sincronización.

Define rutas y credenciales comunes utilizadas por todos los
scripts de sync (sync_zip y sync_multithread).
"""

from pathlib import Path

# ============================================================================
# BACKEND API CONFIGURATION
# ============================================================================

BACKEND_URL = "https://api.farmacruz.com.mx/api/v1"
# BACKEND_URL = "http://localhost:8000/api/v1"
ADMIN_USERNAME = "syncadminssuser2026"
ADMIN_PASSWORD = "ahc4gjnw40blssrtvhjfl4563"

# ============================================================================
# FILE PATHS
# ============================================================================

# Directorio donde están los archivos DBF
DBF_DIR = Path("C:\\Users\\berna\\Documents\\GitProjects\\farmacruz-ecomerce\\backend\\dbfs")

# Directorio donde están las imágenes de productos
IMAGES_FOLDER = Path("C:\\Users\\berna\\Downloads\\\CompressedImg")

# URL del CDN para imágenes
CDN_URL = "https://imgs.farmacruz.com.mx"

# ============================================================================
# DBF FILES
# ============================================================================

# Archivos DBF específicos (rutas completas)
CLIENTES_DBF = DBF_DIR / "clientes.dbf"
AGENTES_DBF = DBF_DIR / "agentes.dbf"
PRODUCTO_DBF = DBF_DIR / "producto.dbf"
PRO_DESC_DBF = DBF_DIR / "pro_desc.dbf"
EXISTE_DBF = DBF_DIR / "existe.dbf"
PRECIPROD_DBF = DBF_DIR / "PRECIPROD.DBF"

# ============================================================================
# FILTERS
# ============================================================================

# Productos bloqueados (IDs que no se sincronizan)
PRODUCTOS_BLOQUEADOS = {'99999', '99998', '100', '99'}

# Categoría bloqueada
CATEGORIA_BLOQUEADA = 'GASTOS'

# Cuantos registros enviar por llamada
BATCH_SIZE = {
    "categorias": 100,
    "productos": 500,
    "listas": 100,
    "items": 2000,
    "users": 200
}
