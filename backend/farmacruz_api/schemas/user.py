"""
Schemas para Usuarios Internos del Sistema

Define la estructura de datos para usuarios que trabajan en el sistema:
- Admins: Acceso completo
- Marketing: Gestion de grupos y clientes
- Sellers: Procesamiento de pedidos

NOTA: Los clientes estan en schemas/customer.py (tabla separada)
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from db.base import UserRole

class UserBase(BaseModel):
    """Schema base con campos comunes de usuario"""
    username: str = Field(..., min_length=3, max_length=50)  # Nombre de usuario unico
    email: Optional[EmailStr] = None  # Email (opcional)
    full_name: Optional[str] = Field(None, max_length=255)  # Nombre completo

class UserCreate(UserBase):
    """
    Schema para crear un nuevo usuario interno
    
    Requiere contraseña, rol y puede especificar si esta activo.
    """
    password: str = Field(..., min_length=8)  # Contraseña (minimo 8 caracteres)
    role: UserRole  # Rol: admin, marketing o seller
    is_active: Optional[bool] = True  # Usuario activo por defecto

class UserUpdate(BaseModel):
    """
    Schema para actualizar un usuario existente
    
    Todos los campos son opcionales (solo se actualiza lo que se envia).
    """
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)  # Nueva contraseña (opcional)
    role: Optional[UserRole] = None  # Cambiar rol (opcional)
    is_active: Optional[bool] = None  # Activar/desactivar (opcional)

class UserInDBBase(UserBase):
    """
    Schema base para usuarios en la base de datos
    
    Incluye campos generados automaticamente (ID, timestamps, etc.)
    """
    user_id: int  # ID unico del usuario
    role: UserRole  # Rol del usuario
    is_active: bool  # Estado activo/inactivo
    created_at: datetime  # Fecha de creacion

    model_config = {
        "from_attributes": True  # Permite crear desde modelo SQLAlchemy
    }

class User(UserInDBBase):
    """
    Schema completo de usuario para responses de la API
    
    No incluye el password_hash por seguridad.
    """
    pass


class UserInDB(UserInDBBase):
    """
    Schema de usuario con password hash
    
    Solo se usa internamente, NUNCA se envia al frontend.
    """
    password_hash: str
