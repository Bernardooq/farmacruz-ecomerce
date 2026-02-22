"""
Schema para crear pedido directamente (sin carrito)

Usado por admin/marketing para crear pedidos en nombre de clientes.
"""

from pydantic import BaseModel, Field
from typing import List

class DirectOrderItemCreate(BaseModel):
    """Item para pedido directo"""
    product_id: str
    quantity: int = Field(..., gt=0)

class DirectOrderCreate(BaseModel):
    """Request para crear pedido directamente"""
    customer_id: int
    items: List[DirectOrderItemCreate]
    shipping_address_number: int = Field(1, ge=1, le=3)
    shipping_cost: float = Field(0.00, ge=0, description="Costo de envío")
