"""
Schemas de Pydantic para FARMACRUZ API

Este modulo exporta todos los schemas de validacion usados en la API.
Los schemas definen la estructura de datos para requests y responses.

Organizacion:
- User: Usuarios internos (admin, marketing, seller)
- Customer: Clientes del e-commerce
- Product & Category: Catalogo de productos
- Order & OrderItem: Sistema de pedidos
- Cart: Carrito de compras temporal
- SalesGroup: Grupos de ventas con managers y vendedores
- PriceList: Listas de precios con markup por producto
- CustomerInfo: Informacion adicional de clientes
"""

# === USUARIOS INTERNOS ===
# Esquemas para usuarios del sistema (admin, marketing, seller)
from .user import User, UserCreate, UserUpdate, UserInDB

# === CLIENTES ===
# Esquemas para clientes del e-commerce (separados de Users)
from .customer import Customer, CustomerCreate, CustomerUpdate, CustomerWithInfo

# === PRODUCTOS Y CATEGORiAS ===
from .product import Product, ProductCreate, ProductUpdate, ProductWithPrice, CatalogProduct
from .category import Category, CategoryCreate, CategoryUpdate

# === INFORMACIoN DE CLIENTES ===
# Informacion comercial: direcciones, grupo de ventas, lista de precios
from .customer_info import CustomerInfo, CustomerInfoCreate, CustomerInfoUpdate, CustomerInfoWithDetails

# === PEDIDOS ===
# Sistema completo de pedidos con items y asignacion de vendedores
from .order import (
    Order, OrderCreate, OrderUpdate, OrderAssign, OrderWithAddress,
    OrderItem, OrderItemCreate, OrderUser
)

# === CARRITO DE COMPRAS ===
from .cart import CartItem

# === GRUPOS DE VENTAS ===
# Organizacion de marketing managers, sellers y customers en grupos
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

# Todos los schemas exportados publicamente
__all__ = [
    # Usuarios internos
    "User", "UserCreate", "UserUpdate", "UserInDB",
    
    # Clientes
    "Customer", "CustomerCreate", "CustomerUpdate", "CustomerWithInfo",
    
    # Productos y categorias
    "Product", "ProductCreate", "ProductUpdate", "ProductWithPrice", "CatalogProduct",
    "Category", "CategoryCreate", "CategoryUpdate",
    
    # Informacion de clientes
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
