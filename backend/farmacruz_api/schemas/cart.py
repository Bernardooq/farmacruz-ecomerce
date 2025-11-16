from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class CartItemBase(BaseModel):
    product_id: int
    quantity: int
    price_at_addition: Decimal

class CartItem(CartItemBase):
    cart_cache_id: int
    user_id: int
    added_at: datetime
    updated_at: datetime
    
    # Información del producto (opcional, para mostrar en el frontend)
    product_name: str | None = None
    product_sku: str | None = None
    product_image_url: str | None = None
    stock_count: int | None = None
    
    model_config = {
        "from_attributes": True
    }
