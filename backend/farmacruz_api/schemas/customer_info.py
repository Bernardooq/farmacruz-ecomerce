from pydantic import BaseModel, Field
from typing import Optional

class CustomerInfoBase(BaseModel):
    business_name: str = Field(..., max_length=255)
    address: Optional[str] = None
    rfc: Optional[str] = Field(None, max_length=13)

class CustomerInfoCreate(CustomerInfoBase):
    user_id: int 
class CustomerInfoUpdate(CustomerInfoBase):
    pass 

class CustomerInfo(CustomerInfoBase):
    customer_info_id: int
    user_id: int

    class Config:
        orm_mode = True