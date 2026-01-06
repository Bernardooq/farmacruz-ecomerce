"""
Schemas de Pydantic para FARMACRUZ API

Este módulo exporta todos los schemas de validación usados en la API.
Los schemas definen la estructura de datos para requests y responses.

Organización:
- User: Usuarios internos (admin, marketing, seller)
- Customer: Clientes del e-commerce
- Product & Category: Catálogo de productos
- Order & OrderItem: Sistema de pedidos
- Cart: Carrito de compras temporal
- SalesGroup: Grupos de ventas con managers y vendedores
- PriceList: Listas de precios con markup por producto
- CustomerInfo: Información adicional de clientes
"""

# === USUARIOS INTERNOS ===
# Esquemas para usuarios del sistema (admin, marketing, seller)
from .user import User, UserCreate, UserUpdate, UserInDB

# === CLIENTES ===
# Esquemas para clientes del e-commerce (separados de Users)
from .customer import Customer, CustomerCreate, CustomerUpdate, CustomerWithInfo

# === PRODUCTOS Y CATEGORÍAS ===
from .product import Product, ProductCreate, ProductUpdate, ProductWithPrice, CatalogProduct
from .category import Category, CategoryCreate, CategoryUpdate

# === INFORMACIÓN DE CLIENTES ===
# Información comercial: direcciones, grupo de ventas, lista de precios
from .customer_info import CustomerInfo, CustomerInfoCreate, CustomerInfoUpdate, CustomerInfoWithDetails

# === PEDIDOS ===
# Sistema completo de pedidos con items y asignación de vendedores
from .order import (
    Order, OrderCreate, OrderUpdate, OrderAssign, OrderWithAddress,
    OrderItem, OrderItemCreate, OrderUser
)

# === CARRITO DE COMPRAS ===
from .cart import CartItem

# === GRUPOS DE VENTAS ===
# Organización de marketing managers, sellers y customers en grupos
from .sales_group import (
    SalesGroup, SalesGroupCreate, SalesGroupUpdate, SalesGroupWithMembers,
    GroupMarketingManager, GroupMarketingManagerCreate,
    GroupSeller, GroupSellerCreate
)

# === LISTAS DE PRECIOS ===
# Sistema de markup por producto para diferentes tipos de clientes
from .price_list import PriceList, PriceListCreate, PriceListUpdate, PriceCalculation

# === DASHBOARDS Y REPORTES ===
from .dashboards import DashboardStats, SalesReport, SalesReportItem

# Todos los schemas exportados públicamente
__all__ = [
    # Usuarios internos
    "User", "UserCreate", "UserUpdate", "UserInDB",
    
    # Clientes
    "Customer", "CustomerCreate", "CustomerUpdate", "CustomerWithInfo",
    
    # Productos y categorías
    "Product", "ProductCreate", "ProductUpdate", "ProductWithPrice", "CatalogProduct",
    "Category", "CategoryCreate", "CategoryUpdate",
    
    # Información de clientes
    "CustomerInfo", "CustomerInfoCreate", "CustomerInfoUpdate", "CustomerInfoWithDetails",
    
    # Pedidos
    "Order", "OrderCreate", "OrderUpdate", "OrderAssign", "OrderWithAddress",
    "OrderItem", "OrderItemCreate", "OrderUser",
    
    # Carrito
    "CartItem",
    
    # Grupos de ventas
    "SalesGroup", "SalesGroupCreate", "SalesGroupUpdate", "SalesGroupWithMembers",
    "GroupMarketingManager", "GroupMarketingManagerCreate",
    "GroupSeller", "GroupSellerCreate",
    
    # Listas de precios
    "PriceList", "PriceListCreate", "PriceListUpdate", "PriceCalculation",
    
    # Dashboards
    "DashboardStats", "SalesReport", "SalesReportItem",
]
