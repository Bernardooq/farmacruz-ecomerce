from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID

class FavoriteListItemBase(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)

class FavoriteListItemCreate(FavoriteListItemBase):
    pass

class FavoriteListItemUpdate(BaseModel):
    quantity: int = Field(..., gt=0)

class FavoriteListItem(FavoriteListItemBase):
    list_item_id: UUID
    list_id: UUID
    added_at: datetime
    # Info para el frontend
    product_name: Optional[str] = None
    product_image_url: Optional[str] = None
    product_stock: Optional[int] = None
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True

class FavoriteListBase(BaseModel):
    name: str

class FavoriteListCreate(FavoriteListBase):
    pass

class FavoriteListUpdate(FavoriteListBase):
    pass

class FavoriteList(FavoriteListBase):
    list_id: UUID
    customer_id: int
    created_at: datetime
    updated_at: datetime
    items: List[FavoriteListItem] = []

    class Config:
        from_attributes = True
