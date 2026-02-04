"""
Router Principal de la API

Centraliza todos los routers de modulos y los registra
con sus prefijos y tags correspondientes.

Estructura de la API:
/api/v1/
  ├── /auth           - Autenticacion (login, register)
  ├── /users          - Perfil de usuario
  ├── /customers      - CRUD de clientes
  ├── /categories     - CRUD de categorias
  ├── /products       - CRUD de productos
  ├── /catalog        - Catalogo con precios para clientes
  ├── /orders         - Gestion de pedidos y carrito
  ├── /admin          - Administracion de usuarios
  ├── /contact        - Formularios de contacto
  ├── /admindash      - Dashboards y reportes
  ├── /sales-groups   - Grupos de ventas
  └── /price-lists    - Listas de precios
  └── /sync           - Sincronizacion DBF

Tags en Swagger:
- Los tags organizan los endpoints en la documentacion API
- Cada router tiene un tag descriptivo en español
"""

from fastapi import APIRouter
from . import (
    auth,
    products,
    orders,
    admin,
    categories,
    contact,
    users,
    dashboards,
    sales_groups,
    price_lists,
    customers,
    catalog,
    sync_dbf,
    sync_dbf_upload
)

# Router principal que agrupa todos los modulos
api_router = APIRouter()

# === AUTENTICACIoN ===
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticacion"]
)

# === USUARIOS Y PERFIL ===
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["Usuarios"]
)

# === CLIENTES ===
api_router.include_router(
    customers.router,
    prefix="/customers",
    tags=["Clientes"]
)

# === CATaLOGO Y PRODUCTOS ===
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["Categorias"]
)

api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Productos"]
)

api_router.include_router(
    catalog.router,
    prefix="/catalog",
    tags=["Catalogo Cliente"]
)

# === PEDIDOS ===
api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Pedidos"]
)

# === ADMINISTRACIoN ===
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Administracion"]
)

api_router.include_router(
    dashboards.router,
    prefix="/admindash",
    tags=["Dashboards"]
)

# === COMUNICACIoN ===
api_router.include_router(
    contact.router,
    prefix="/contact",
    tags=["Contacto"]
)

# === VENTAS ===
api_router.include_router(
    sales_groups.router,
    prefix="/sales-groups",
    tags=["Grupos de Ventas"]
)

api_router.include_router(
    price_lists.router,
    prefix="/price-lists",
    tags=["Listas de Precios"]
)

# === SINCRONIZACIÓN DBF ===
api_router.include_router(
    sync_dbf.router,
    prefix="/sync",
    tags=["Sincronizacion DBF"]
)

# === SINCRONIZACIÓN DBF UPLOAD (COMPRIMIDO) ===
api_router.include_router(
    sync_dbf_upload.router,
    prefix="/sync-upload",
    tags=["Sincronizacion DBF Upload"]
)
