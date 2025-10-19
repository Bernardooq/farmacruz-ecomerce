from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from farmacruz_api.db.base import OrderStatus
from .product import Product

# Order Item Schemas 
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0) 

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    order_item_id: int
    price_at_purchase: Decimal


    class Config:
        orm_mode = True

# --- Order Schemas ---
class OrderBase(BaseModel):
    status: OrderStatus = OrderStatus.cart

class OrderCreate(OrderBase):
    pass 

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    seller_id: Optional[int] = None 

# Properties to return via API
class Order(OrderBase):
    order_id: int
    user_id: int
    seller_id: Optional[int] = None
    total_amount: Decimal
    created_at: datetime
    validated_at: Optional[datetime] = None
    items: List[OrderItem] = [] 

    class Config:
        orm_mode = True