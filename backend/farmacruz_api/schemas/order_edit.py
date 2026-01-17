"""
Schemas para Edicion de Pedidos

Define la estructura de datos para editar pedidos existentes:
- OrderItemEdit: Para modificar items individuales
- OrderEditRequest: Para la solicitud completa de edicion

Solo marketing y admin pueden usar estas operaciones.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


class OrderItemEdit(BaseModel):
    """
    Schema para editar un item de pedido
    
    - Si order_item_id es None, se crea un nuevo item
    - Si order_item_id existe, se actualiza ese item
    - Los items no incluidos en la lista se eliminan
    """
    order_item_id: Optional[UUID] = None  # None para nuevos items
    product_id: str = Field(..., description="ID del producto")
    quantity: int = Field(..., gt=0, description="Cantidad del producto")


class OrderEditRequest(BaseModel):
    """
    Schema para solicitud de edicion de pedido completo
    
    Incluye la lista de items que deberia tener el pedido.
    Marketing/Admin puede:
    - Agregar nuevos productos
    - Eliminar productos existentes
    - Cambiar cantidades
    
    Los precios se recalculan automaticamente segun la lista del cliente.
    """
    items: List[OrderItemEdit] = Field(..., description="Lista de items del pedido")

    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [
                    {"order_item_id": None, "product_id": "PROD123", "quantity": 5},
                    {"order_item_id": "550e8400-e29b-41d4-a716-446655440000", "product_id": "PROD456", "quantity": 3}
                ]
            }
        }
    }
