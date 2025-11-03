from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from db.base import UserRole

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

class UserInDBBase(UserBase):
    user_id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
        }
class User(UserInDBBase):
    pass 

class UserInDB(UserInDBBase):
    password_hash: str