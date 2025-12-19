"""
CRUD Module - Operaciones de Base de Datos para FARMACRUZ

Este módulo centraliza todas las operaciones CRUD (Create, Read, Update, Delete)
para las tablas de la base de datos.

Organización:
- Base: Clase genérica CRUDBase
- Auxiliares: dashboard, cart, price_calculator
- Básicos: user, customer, product, category
- Complejos: order, sales_group, price_list

Uso:
    from crud import crud_user, crud_product, price_calculator
"""

# === CLASE BASE ===
from .base import CRUDBase

# === AUXILIARES ===
from . import crud_dashboard
from . import crud_cart
from . import price_calculator

# === USUARIOS Y CLIENTES ===
from . import crud_user
from . import crud_customer

# === PRODUCTOS Y CATEGORÍAS ===
from . import crud_product
from . import crud_category

# === PEDIDOS ===
from . import crud_order

# === GRUPOS DE VENTAS ===
from . import crud_sales_group

# === LISTAS DE PRECIOS ===
from . import crud_price_list

__all__ = [
    # Base
    "CRUDBase",
    
    # Auxiliares
    "crud_dashboard",
    "crud_cart",
    "price_calculator",
    
    # Usuarios y clientes
    "crud_user",
    "crud_customer",
    
    # Productos
    "crud_product",
    "crud_category",
    
    # Pedidos
    "crud_order",
    
    # Grupos y precios
    "crud_sales_group",
    "crud_price_list",
]
