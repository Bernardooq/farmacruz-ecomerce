"""
Schemas para Clientes (Customers)

Los clientes están separados de los usuarios internos del sistema.
Son usuarios externos que:
- Compran productos a través del e-commerce
- Tienen información comercial asociada (CustomerInfo)
- Realizan pedidos
- Pertenecen a grupos de ventas

NOTA: Los usuarios internos están en schemas/user.py (tabla separada)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    """Schema base con campos comunes de cliente"""
    username: str = Field(..., min_length=3, max_length=255)  # Nombre de usuario único
    email: Optional[str] = Field(None, max_length=255)  # Email del cliente
    full_name: Optional[str] = Field(None, max_length=255)  # Nombre completo


class CustomerCreate(CustomerBase):
    """
    Schema para crear un nuevo cliente
    
    El admin debe proporcionar el ID (para sincronización con sistema externo).
    """
    customer_id: int  # Admin debe proporcionar este ID
    password: str = Field(..., min_length=8)  # Contraseña (mínimo 8 caracteres)


class CustomerUpdate(BaseModel):
    """
    Schema para actualizar un cliente existente
    
    Todos los campos son opcionales (solo se actualiza lo que se envía).
    """
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)  # Nueva contraseña (opcional)
    is_active: Optional[bool] = None  # Activar/desactivar (opcional)


class CustomerInDBBase(CustomerBase):
    """
    Schema base para clientes en la base de datos
    
    Incluye campos generados automáticamente.
    """
    customer_id: int  # ID único del cliente
    is_active: bool  # Estado activo/inactivo
    created_at: datetime  # Fecha de registro

    model_config = {"from_attributes": True}  # Permite crear desde modelo SQLAlchemy


class Customer(CustomerInDBBase):
    """
    Schema completo de cliente para responses de la API
    
    No incluye el password_hash por seguridad.
    """
    pass


class CustomerWithInfo(Customer):
    """
    Cliente con información comercial completa
    
    Incluye CustomerInfo (direcciones, grupo de ventas, lista de precios).
    Útil para mostrar perfil completo del cliente.
    """
    customer_info: Optional['CustomerInfoSchema'] = None  # Información comercial asociada

    model_config = {"from_attributes": True}


# Import para evitar dependencia circular
from schemas.customer_info import CustomerInfo as CustomerInfoSchema
CustomerWithInfo.model_rebuild()  # Reconstruir modelo después del import
