"""
Schemas para Pedidos (Orders) y OrderItems

Sistema completo de pedidos con:
- Creación de pedidos por clientes
- Asignación a vendedores por admin/marketing
- Seguimiento de estados
- Items con precios congelados al momento del pedido

Flujo típico:
1. Cliente crea pedido (status: pending_validation)
2. Admin/Marketing asigna a vendedor (status: assigned)
3. Vendedor aprueba (status: approved)
4. Se envía (status: shipped)
5. Se entrega (status: delivered)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from db.base import OrderStatus
from .product import Product


# ==========================================
# ORDER USER (Usuario simplificado para pedidos)
# ==========================================

class OrderUser(BaseModel):
    """
    Schema simplificado de usuario/cliente para mostrar en pedidos
    
    Puede representar tanto un usuario interno (seller, admin)
    como un cliente (customer). Se distinguen por qué ID está presente.
    """
    user_id: Optional[int] = None  # Para usuarios internos (seller, admin, marketing)
    customer_id: Optional[int] = None  # Para clientes
    username: str  # Nombre de usuario
    email: Optional[str] = None  # Email
    full_name: Optional[str] = None  # Nombre completo

    model_config = {"from_attributes": True}


# ==========================================
# ORDER ITEMS (Items del pedido)
# ==========================================

class OrderItemBase(BaseModel):
    """Schema base de item de pedido"""
    product_id: str  # ID del producto (tipo texto)
    quantity: int = Field(..., gt=0)  # Cantidad (debe ser > 0)


class OrderItemCreate(OrderItemBase):
    """
    Schema para agregar un producto al pedido
    
    Solo se necesita el ID del producto y la cantidad.
    Los precios se calculan automáticamente en el backend.
    """
    pass


class OrderItem(OrderItemBase):
    """
    Schema completo de item de pedido
    
    Los precios se "congelan" al momento de crear el pedido,
    manteniendo un historial preciso aunque los precios cambien después.
    """
    order_item_id: int  # ID único del item
    # Precios congelados (snapshot al momento del pedido)
    base_price: Decimal  # Precio base del producto cuando se ordenó
    markup_percentage: Decimal  # % de markup cuando se ordenó
    iva_percentage: Decimal  # % de IVA cuando se ordenó
    final_price: Decimal  # Precio final calculado
    product: Optional[Product] = None  # Información del producto (opcional)

    model_config = {"from_attributes": True}


# ==========================================
# ORDERS (Pedidos)
# ==========================================

class OrderBase(BaseModel):
    """Schema base de pedido"""
    status: OrderStatus = OrderStatus.pending_validation  # Estado inicial


class OrderCreate(OrderBase):
    """
    Schema para crear un nuevo pedido
    
    El cliente solo especifica qué dirección usar (1, 2 o 3).
    Los items se agregan después con OrderItemCreate.
    """
    shipping_address_number: Optional[int] = Field(None, ge=1, le=3)  # Cuál dirección usar (1, 2 o 3)


class OrderUpdate(BaseModel):
    """
    Schema para actualizar un pedido
    
    Usado principalmente para cambiar estado o asignar vendedor.
    """
    status: Optional[OrderStatus] = None  # Cambiar estado
    assigned_seller_id: Optional[int] = None  # Asignar/cambiar vendedor
    shipping_address_number: Optional[int] = Field(None, ge=1, le=3)  # Cambiar dirección
    assignment_notes: Optional[str] = None  # Notas al asignar


class OrderAssign(BaseModel):
    """
    Schema específico para asignar un pedido a un vendedor
    
    Usado por admin/marketing para asignar trabajo.
    """
    assigned_seller_id: int  # ID del vendedor a asignar
    assignment_notes: Optional[str] = None  # Notas sobre la asignación


class Order(OrderBase):
    """
    Schema completo de pedido para responses
    
    Incluye toda la información del pedido con relaciones.
    """
    order_id: int  # ID único del pedido
    customer_id: int  # ID del cliente que hizo el pedido (cambió de user_id)
    assigned_seller_id: Optional[int] = None  # ID del vendedor asignado (si hay)
    assigned_by_user_id: Optional[int] = None  # ID de quién hizo la asignación (si hay)
    total_amount: Decimal  # Monto total del pedido
    shipping_address_number: Optional[int] = None  # Qué dirección se usa (1, 2 o 3)
    assignment_notes: Optional[str] = None  # Notas de asignación
    
    # Timestamps
    created_at: datetime  # Cuándo se creó el pedido
    assigned_at: Optional[datetime] = None  # Cuándo se asignó vendedor
    validated_at: Optional[datetime] = None  # Cuándo el vendedor lo aprobó
    
    # Relaciones
    items: List[OrderItem] = []  # Lista de productos en el pedido
    customer: Optional[OrderUser] = None  # Información del cliente
    assigned_seller: Optional[OrderUser] = None  # Información del vendedor asignado
    assigned_by: Optional[OrderUser] = None  # Información de quién asignó

    model_config = {"from_attributes": True}


class OrderWithAddress(Order):
    """
    Pedido con la dirección de envío completa
    
    Incluye el texto completo de la dirección seleccionada,
    no solo el número (1, 2 o 3).
    
    Útil para mostrar en detalles de pedido o para impresión.
    """
    shipping_address: Optional[str] = None  # Dirección completa basada en shipping_address_number
