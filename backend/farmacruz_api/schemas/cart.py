"""
Schemas para Carrito de Compras (CartCache)

El carrito es temporal y almacena lo que el cliente quiere comprar
antes de convertirlo en un pedido formal.
"""

from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from typing import Optional


class CartItemBase(BaseModel):
    """Schema base para items del carrito"""
    product_id: str  # ID del producto a comprar (tipo texto)
    quantity: int  # Cantidad deseada
    price_at_addition: Decimal  # Precio cuando se agrego (snapshot)


class CartItem(CartItemBase):
    """
    Item completo del carrito con informacion adicional
    
    Incluye datos del producto para mostrar en el frontend
    sin necesidad de hacer queries adicionales.
    """
    cart_cache_id: int  # ID unico del item en el carrito
    customer_id: int  # ID del cliente dueño del carrito (CORREGIDO: era user_id)
    added_at: datetime  # Primera vez que se agrego
    updated_at: datetime  # ultima modificacion de cantidad
    
    # Informacion del producto (opcional, para mostrar en el frontend)
    product_name: Optional[str] = None  # Nombre del producto
    product_codebar: Optional[str] = None  # Codigo codebar
    product_image_url: Optional[str] = None  # URL de la imagen
    stock_count: Optional[int] = None # Stock disponible
    
    model_config = {
        "from_attributes": True
    }
