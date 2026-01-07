"""
Modelos SQLAlchemy para FARMACRUZ v2.1

Arquitectura de base de datos:
- Los usuarios internos (admin, marketing, seller) están en la tabla 'users'
- Los clientes están separados en la tabla 'customers'
- Relaciones N:M para grupos de ventas con managers y vendedores
- Listas de precios con markup por producto
- Sistema de pedidos con asignación de vendedores
"""

import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum as SQLAlchemyEnum, 
    ForeignKey, Numeric, TIMESTAMP, func, Text, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship, declarative_base

# Clase base de la que heredan todos los modelos
Base = declarative_base()


# ==========================================
# ENUMS - Tipos enumerados para campos específicos
# ==========================================

class UserRole(str, enum.Enum):
    """
    Roles para usuarios INTERNOS del sistema
    
    - admin: Administrador con acceso completo
    - marketing: Manager de marketing con vista de sus grupos
    - seller: Vendedor que procesa pedidos
    
    NOTA: Los clientes NO usan esta enumeración, están en tabla separada
    """
    admin = "admin"
    marketing = "marketing"
    seller = "seller"


class OrderStatus(str, enum.Enum):
    """
    Estados del ciclo de vida de un pedido
    
    - pending_validation: Pedido creado, esperando asignación a vendedor
    - approved: Vendedor aprobó el pedido
    - shipped: Pedido en tránsito
    - delivered: Entregado al cliente
    - cancelled: Cancelado (por admin o cliente)
    """
    pending_validation = "pending_validation"
    approved = "approved"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"


# ==========================================
# MODELOS - Definición de tablas
# ==========================================

class User(Base):
    """
    Usuarios INTERNOS del sistema (admin, marketing, seller)
    
    Esta tabla NO incluye clientes. Los clientes están en 'customers'.
    Estos usuarios son empleados o personal interno de FARMACRUZ.
    """
    __tablename__ = "users"

    # Campos principales
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # Hash Argon2
    full_name = Column(String(255))
    role = Column(SQLAlchemyEnum(UserRole), nullable=False)  # admin, marketing o seller
    is_active = Column(Boolean, default=True)  # Para desactivar usuarios sin eliminarlos
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relaciones con otras tablas
    # Pedidos donde este usuario es el vendedor asignado
    orders_assigned = relationship("Order", back_populates="assigned_seller", foreign_keys="[Order.assigned_seller_id]")
    # Pedidos donde este usuario hizo la asignación (quién asignó el vendedor)
    orders_assigned_by = relationship("Order", back_populates="assigned_by", foreign_keys="[Order.assigned_by_user_id]")
    # Grupos de ventas donde es marketing manager
    marketing_groups = relationship("GroupMarketingManager", back_populates="marketing_user", cascade="all, delete-orphan")
    # Grupos de ventas donde es vendedor
    seller_groups = relationship("GroupSeller", back_populates="seller_user", cascade="all, delete-orphan")


class Customer(Base):
    """
    Clientes del e-commerce (SEPARADO de Users)
    
    Los clientes son usuarios externos que compran productos.
    Tienen su propia tabla separada de usuarios internos.
    """
    __tablename__ = "customers"

    # Campos principales (similares a User pero en tabla separada)
    customer_id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255), nullable=False)  # Hash Argon2
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relaciones con otras tablas
    # Información adicional del cliente (direcciones, grupo, lista de precios)
    customer_info = relationship("CustomerInfo", back_populates="customer", uselist=False)
    # Pedidos realizados por este cliente
    orders = relationship("Order", back_populates="customer")
    # Carrito de compras temporal
    cart_cache = relationship("CartCache", back_populates="customer", cascade="all, delete")


class SalesGroup(Base):
    """
    Grupos de ventas para organizar clientes, vendedores y managers
    
    Cada grupo puede tener:
    - Múltiples marketing managers (relación N:M)
    - Múltiples vendedores (relación N:M)
    - Múltiples clientes asignados
    """
    __tablename__ = "salesgroups"

    sales_group_id = Column(Integer, primary_key=True)
    group_name = Column(String(255), nullable=False)  # Ej: "Farmacias Zona Norte"
    description = Column(Text)  # Descripción opcional del grupo
    is_active = Column(Boolean, default=True)  # Para desactivar sin eliminar
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relaciones N:M (muchos a muchos)
    # Marketing managers asignados a este grupo
    marketing_managers = relationship("GroupMarketingManager", back_populates="sales_group")
    # Vendedores asignados a este grupo
    sellers = relationship("GroupSeller", back_populates="sales_group")
    # Clientes que pertenecen a este grupo
    customers = relationship("CustomerInfo", back_populates="sales_group")


class GroupMarketingManager(Base):
    """
    Tabla de relación N:M entre SalesGroup y User (marketing managers)
    
    Permite que un marketing manager esté en múltiples grupos
    y que un grupo tenga múltiples marketing managers.
    """
    __tablename__ = "groupmarketingmanagers"

    group_marketing_id = Column(Integer, primary_key=True)
    sales_group_id = Column(Integer, ForeignKey("salesgroups.sales_group_id", ondelete="CASCADE"), nullable=False, index=True)
    marketing_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # Cuándo se asignó

    # Constraint para evitar duplicados (mismo manager en mismo grupo)
    __table_args__ = (
        UniqueConstraint('sales_group_id', 'marketing_id'),
    )

    # Relaciones para navegar de vuelta
    sales_group = relationship("SalesGroup", back_populates="marketing_managers")
    marketing_user = relationship("User", back_populates="marketing_groups")


class GroupSeller(Base):
    """
    Tabla de relación N:M entre SalesGroup y User (sellers)
    
    Permite que un vendedor esté en múltiples grupos
    y que un grupo tenga múltiples vendedores.
    """
    __tablename__ = "groupsellers"

    group_seller_id = Column(Integer, primary_key=True)
    sales_group_id = Column(Integer, ForeignKey("salesgroups.sales_group_id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # Cuándo se asignó

    # Constraint para evitar duplicados (mismo vendedor en mismo grupo)
    __table_args__ = (
        UniqueConstraint('sales_group_id', 'seller_id'),
    )

    # Relaciones para navegar de vuelta
    sales_group = relationship("SalesGroup", back_populates="sellers")
    seller_user = relationship("User", back_populates="seller_groups")


class Category(Base):
    """
    Categorías para organizar productos
    
    Ejemplos: "Analgésicos", "Antibióticos", "Vitaminas", etc.
    """
    __tablename__ = "categories"

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # Nombre de la categoría
    description = Column(Text)  # Descripción opcional
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Productos que pertenecen a esta categoría
    products = relationship("Product", back_populates="category")


class Product(Base):
    """
    Productos del catálogo
    
    El precio final se calcula como:
    precio_final = (base_price + base_price * markup) * (1 + iva_percentage)
    Donde markup viene de la lista de precios del cliente
    """
    __tablename__ = "products"

    product_id = Column(String(50), primary_key=True)  # ID tipo "FAR74" (no numérico)
    codebar = Column(String(100), unique=True, nullable=True, index=True)  # Código de barras (puede ser None)
    name = Column(String(255), nullable=False)  # Nombre del producto
    description = Column(Text)  # Descripción principal (del DBF/sincronización)
    descripcion_2 = Column(Text)  # Descripción adicional (editable por admin, ej: receta médica)
    unidad_medida = Column(String(10))  # Unidad: "piezas", "cajas", "frascos", etc.
    base_price = Column(Numeric(10, 2), nullable=False, default=0.00)  # Precio base sin markup ni IVA
    iva_percentage = Column(Numeric(5, 2), default=0.00)  # % de IVA (ej: 16.00)
    image_url = Column(String(255))  # URL de la imagen del producto (puede ser None)
    stock_count = Column(Integer, default=0)  # Cantidad en inventario
    is_active = Column(Boolean, default=True, index=True)  # Para ocultar productos sin eliminarlos
    category_id = Column(Integer, ForeignKey("categories.category_id"), index=True)
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")  # Items en pedidos
    cart_entries = relationship("CartCache", back_populates="product")  # Items en carritos
    price_list_items = relationship("PriceListItem", back_populates="product")  # Markup por lista


class PriceList(Base):
    """
    Lista de precios (contenedor)
    
    Cada lista agrupa múltiples productos con sus respectivos markups.
    Los clientes se asignan a una lista de precios que determina
    su porcentaje de ganancia sobre el precio base.
    """
    __tablename__ = "pricelists"

    price_list_id = Column(Integer, primary_key=True)
    list_name = Column(String(100), nullable=False)  # Ej: "Farmacias Premium", "Hospitales"
    description = Column(Text)  # Descripción de a quién aplica
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    # Clientes asignados a esta lista
    customers = relationship("CustomerInfo", back_populates="price_list")
    # Items (productos) con su markup específico en esta lista
    price_list_items = relationship("PriceListItem", back_populates="price_list", cascade="all, delete-orphan")


class PriceListItem(Base):
    """
    Markup específico de un producto en una lista de precios
    
    Define el porcentaje de ganancia que se aplica al precio base
    de un producto específico para una lista específica.
    
    Ejemplo: Producto X en "Lista Premium" tiene markup de 25.00%
    """
    __tablename__ = "pricelistitems"

    price_list_item_id = Column(Integer, primary_key=True)
    price_list_id = Column(Integer, ForeignKey("pricelists.price_list_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id", ondelete="CASCADE"), nullable=False, index=True)
    markup_percentage = Column(Numeric(5, 2), nullable=False)  # % de ganancia (ej: 25.00)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraint: un producto solo puede aparecer una vez por lista
    __table_args__ = (
        UniqueConstraint('price_list_id', 'product_id'),
    )

    # Relaciones
    price_list = relationship("PriceList", back_populates="price_list_items")
    product = relationship("Product", back_populates="price_list_items")


class CustomerInfo(Base):
    """
    Información adicional de clientes (1:1 con Customer)
    
    Almacena datos comerciales del cliente:
    - Información fiscal (RFC, razón social)
    - Grupo de ventas al que pertenece
    - Lista de precios asignada
    - Hasta 3 direcciones de envío
    """
    __tablename__ = "customerinfo"

    customer_info_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(255), nullable=False)  # Razón social de la empresa
    rfc = Column(String(13))  # RFC mexicano (12-13 caracteres)
    sales_group_id = Column(Integer, ForeignKey("salesgroups.sales_group_id"), index=True)  # Grupo asignado
    price_list_id = Column(Integer, ForeignKey("pricelists.price_list_id"), index=True)  # Lista de precios
    # Tres direcciones posibles (el cliente elige cuál usar al hacer pedido)
    address_1 = Column(Text)  # Dirección principal
    address_2 = Column(Text)  # Dirección secundaria (opcional)
    address_3 = Column(Text)  # Dirección terciaria (opcional)

    # Relaciones
    customer = relationship("Customer", back_populates="customer_info")  # Usuario cliente
    sales_group = relationship("SalesGroup", back_populates="customers")  # Grupo de ventas
    price_list = relationship("PriceList", back_populates="customers")  # Lista de precios


class Order(Base):
    """
    Pedidos de clientes
    
    Flujo típico:
    1. Cliente crea pedido (status: pending_validation)
    2. Admin/Marketing asigna a vendedor (status: assigned)
    3. Vendedor aprueba (status: approved)
    4. Se envía (status: shipped)
    5. Se entrega (status: delivered)
    """
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id"), nullable=False, index=True)
    assigned_seller_id = Column(Integer, ForeignKey("users.user_id"), index=True)  # Vendedor asignado
    assigned_by_user_id = Column(Integer, ForeignKey("users.user_id"))  # Quién hizo la asignación
    status = Column(SQLAlchemyEnum(OrderStatus), nullable=False, default=OrderStatus.pending_validation, index=True)
    total_amount = Column(Numeric(12, 2), default=0.00)  # Monto total calculado
    shipping_address_number = Column(Integer)  # 1, 2 o 3 (cuál de las 3 direcciones usar)
    assignment_notes = Column(Text)  # Notas del admin al asignar vendedor
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), index=True)
    assigned_at = Column(TIMESTAMP(timezone=True))  # Cuándo se asignó vendedor
    validated_at = Column(TIMESTAMP(timezone=True))  # Cuándo el vendedor lo aprobó

    # Constraint: número de dirección debe ser 1, 2 o 3
    __table_args__ = (
        CheckConstraint('shipping_address_number BETWEEN 1 AND 3', name='check_address_number'),
    )

    # Relaciones
    customer = relationship("Customer", back_populates="orders")  # Cliente que hizo el pedido
    assigned_seller = relationship("User", back_populates="orders_assigned", foreign_keys=[assigned_seller_id])  # Vendedor
    assigned_by = relationship("User", back_populates="orders_assigned_by", foreign_keys=[assigned_by_user_id])  # Quién asignó
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")  # Productos del pedido


class OrderItem(Base):
    """
    Items individuales dentro de un pedido
    
    Cada item representa un producto con su cantidad y precios.
    Los precios se 'congelan' al momento de crear el pedido para
    mantener historial preciso aunque los precios cambien después.
    """
    __tablename__ = "orderitems"

    order_item_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False)  # Cantidad del producto
    # Precios congelados al momento del pedido
    base_price = Column(Numeric(10, 2), nullable=False)  # Precio base snapshot
    markup_percentage = Column(Numeric(5, 2), nullable=False)  # % markup snapshot
    iva_percentage = Column(Numeric(5, 2), nullable=False)  # % IVA snapshot
    final_price = Column(Numeric(10, 2), nullable=False)  # Precio final calculado

    # Constraint: cantidad debe ser positiva
    __table_args__ = (
        CheckConstraint('quantity > 0', name='check_quantity_positive'),
    )

    # Relaciones
    order = relationship("Order", back_populates="items")  # Pedido al que pertenece
    product = relationship("Product", back_populates="order_items")  # Producto ordenado


class CartCache(Base):
    """
    Carrito de compras temporal de clientes
    
    Almacena los productos que el cliente ha agregado al carrito
    pero aún no ha convertido en pedido. Se limpia al crear el pedido.
    """
    __tablename__ = "cartcache"

    cart_cache_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(String(50), ForeignKey("products.product_id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)  # Cantidad a ordenar
    added_at = Column(TIMESTAMP(timezone=True), server_default=func.now())  # Primera vez agregado
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())  # Última modificación

    __table_args__ = (
        # Un producto solo puede aparecer una vez en el carrito de un cliente
        UniqueConstraint('customer_id', 'product_id'),
        # La cantidad debe ser positiva
        CheckConstraint('quantity > 0', name='check_cart_quantity_positive'),
    )

    # Relaciones
    customer = relationship("Customer", back_populates="cart_cache")  # Cliente dueño del carrito
    product = relationship("Product", back_populates="cart_entries")  # Producto en el carrito
