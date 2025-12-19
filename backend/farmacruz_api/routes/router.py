"""
Router Principal de la API

Centraliza todos los routers de módulos y los registra
con sus prefijos y tags correspondientes.

Estructura de la API:
/api/v1/
  ├── /auth           - Autenticación (login, register)
  ├── /users          - Perfil de usuario
  ├── /customers      - CRUD de clientes
  ├── /categories     - CRUD de categorías
  ├── /products       - CRUD de productos
  ├── /catalog        - Catálogo con precios para clientes
  ├── /orders         - Gestión de pedidos y carrito
  ├── /admin          - Administración de usuarios
  ├── /contact        - Formularios de contacto
  ├── /admindash      - Dashboards y reportes
  ├── /sales-groups   - Grupos de ventas
  └── /price-lists    - Listas de precios

Tags en Swagger:
- Los tags organizan los endpoints en la documentación API
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
    catalog
)

# Router principal que agrupa todos los módulos
api_router = APIRouter()

# === AUTENTICACIÓN ===
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["Autenticación"]
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
    tags=["Clientes"]
)

# === CATÁLOGO Y PRODUCTOS ===
api_router.include_router(
    categories.router,
    prefix="/categories",
    tags=["Categorías"]
)

api_router.include_router(
    products.router,
    prefix="/products",
    tags=["Productos"]
)

api_router.include_router(
    catalog.router,
    prefix="/catalog",
    tags=["Catálogo Cliente"]
)

# === PEDIDOS ===
api_router.include_router(
    orders.router,
    prefix="/orders",
    tags=["Pedidos"]
)

# === ADMINISTRACIÓN ===
api_router.include_router(
    admin.router,
    prefix="/admin",
    tags=["Administración"]
)

api_router.include_router(
    dashboards.router,
    prefix="/admindash",
    tags=["Dashboards"]
)

# === COMUNICACIÓN ===
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
    tags=["Listas de Precios"]
)