"""
Schemas para Pedidos (Orders) y OrderItems

Sistema completo de pedidos con:
- Creacion de pedidos por clientes
- Asignacion a vendedores por admin/marketing
- Seguimiento de estados
- Items con precios congelados al momento del pedido

Flujo tipico:
1. Cliente crea pedido (status: pending_validation)
2. Admin/Marketing asigna a vendedor (status: assigned)
3. Vendedor aprueba (status: approved)
4. Se envia (status: shipped)
5. Se entrega (status: delivered)
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from db.base import OrderStatus
from .product import Product


# ORDER USER (Usuario simplificado para pedidos)

class OrderUser(BaseModel):
    """
    Schema simplificado de usuario/cliente para mostrar en pedidos
    
    Puede representar tanto un usuario interno (seller, admin)
    como un cliente (customer). Se distinguen por que ID esta presente.
    """
    user_id: Optional[int] = None  # Para usuarios internos (seller, admin, marketing)
    customer_id: Optional[int] = None  # Para clientes
    username: str  # Nombre de usuario
    email: Optional[str] = None  # Email
    full_name: Optional[str] = None  # Nombre completo

    model_config = {"from_attributes": True}


# ORDER ITEMS (Items del pedido)

class OrderItemBase(BaseModel):
    """Schema base de item de pedido"""
    product_id: str  # ID del producto (tipo texto)
    quantity: int = Field(..., gt=0)  # Cantidad (debe ser > 0)


class OrderItemCreate(OrderItemBase):
    """
    Schema para agregar un producto al pedido
    
    Solo se necesita el ID del producto y la cantidad.
    Los precios se calculan automaticamente en el backend.
    """
    pass


class OrderItem(OrderItemBase):
    """
    Schema completo de item de pedido
    
    Los precios se "congelan" al momento de crear el pedido,
    manteniendo un historial preciso aunque los precios cambien despues.
    """
    order_item_id: UUID  # ID unico del item
    # Precios congelados (snapshot al momento del pedido)
    base_price: Decimal  # Precio base del producto cuando se ordeno
    markup_percentage: Decimal  # % de markup cuando se ordeno
    iva_percentage: Decimal  # % de IVA cuando se ordeno
    final_price: Decimal  # Precio final calculado
    product: Optional[Product] = None  # Informacion del producto (opcional)

    model_config = {"from_attributes": True}


# ORDERS (Pedidos)

class OrderBase(BaseModel):
    """Schema base de pedido"""
    status: OrderStatus = OrderStatus.pending_validation  # Estado inicial


class OrderCreate(OrderBase):
    """
    Schema para crear un nuevo pedido
    
    El cliente solo especifica que direccion usar (1, 2 o 3).
    Los items se agregan despues con OrderItemCreate.
    """
    shipping_address_number: Optional[int] = Field(None, ge=1, le=3)  # Cual direccion usar (1, 2 o 3)
    shipping_cost: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)  # Costo de envío


class OrderUpdate(BaseModel):
    """
    Schema para actualizar un pedido
    
    Usado principalmente para cambiar estado o asignar vendedor.
    """
    status: Optional[OrderStatus] = None  # Cambiar estado
    assigned_seller_id: Optional[int] = None  # Asignar/cambiar vendedor
    shipping_address_number: Optional[int] = Field(None, ge=1, le=3)  # Cambiar direccion
    assignment_notes: Optional[str] = None  # Notas al asignar
    shipping_cost: Optional[Decimal] = Field(None, ge=0)  # Costo de envío


class OrderAssign(BaseModel):
    """
    Schema especifico para asignar un pedido a un vendedor
    
    Usado por admin/marketing para asignar trabajo.
    """
    assigned_seller_id: int  # ID del vendedor a asignar
    assignment_notes: Optional[str] = None  # Notas sobre la asignacion


class OrderItemEdit(BaseModel):
    """
    Schema para editar items de un pedido existente
    
    Si order_item_id es None, es un nuevo producto a agregar.
    Si existe, se actualiza la cantidad de ese item.
    """
    order_item_id: Optional[UUID] = None  # ID del item existente (None para nuevos)
    product_id: str  # ID del producto
    quantity: int = Field(..., gt=0)  # Nueva cantidad


class OrderEditRequest(BaseModel):
    """
    Schema para solicitud de edición de pedido
    
    Permite actualizar los items de un pedido.
    Los precios se recalculan automáticamente en el backend.
    """
    items: List[OrderItemEdit]  # Lista de items actualizados


class Order(OrderBase):
    """
    Schema completo de pedido para responses
    
    Incluye toda la informacion del pedido con relaciones.
    """
    order_id: UUID  # ID unico del pedido
    customer_id: int  # ID del cliente que hizo el pedido (cambio de user_id)
    assigned_seller_id: Optional[int] = None  # ID del vendedor asignado (si hay)
    assigned_by_user_id: Optional[int] = None  # ID de quien hizo la asignacion (si hay)
    total_amount: Decimal  # Monto total del pedido
    shipping_cost: Decimal = Decimal("0.00")  # Costo de envío
    shipping_address_number: Optional[int] = None  # Que direccion se usa (1, 2 o 3)
    assignment_notes: Optional[str] = None  # Notas de asignacion
    
    # Timestamps
    created_at: datetime  # Cuando se creo el pedido
    assigned_at: Optional[datetime] = None  # Cuando se asigno vendedor
    validated_at: Optional[datetime] = None  # Cuando el vendedor lo aprobo
    
    # Relaciones
    items: List[OrderItem] = []  # Lista de productos en el pedido
    customer: Optional[OrderUser] = None  # Informacion del cliente
    assigned_seller: Optional[OrderUser] = None  # Informacion del vendedor asignado
    assigned_by: Optional[OrderUser] = None  # Informacion de quien asigno

    model_config = {"from_attributes": True}


class OrderWithAddress(Order):
    """
    Pedido con la direccion de envio completa
    
    Incluye el texto completo de la direccion seleccionada,
    no solo el numero (1, 2 o 3).
    
    util para mostrar en detalles de pedido o para impresion.
    """
    shipping_address: Optional[str] = None  # Direccion completa basada en shipping_address_number
    customerInfo: Optional[dict] = None  # Informacion completa del cliente (RFC, business_name, telefonos)



