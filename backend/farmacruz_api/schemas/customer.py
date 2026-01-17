"""
Schemas para Clientes (Customers)

Los clientes son usuarios externos que compran productos.
Tienen informacion adicional en CustomerInfo (direccion, RFC, etc.)
"""

from typing import Optional
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """Campos base compartidos por todos los schemas de Customer"""
    username: str = Field(..., min_length=3, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)


class CustomerCreate(CustomerBase):
    """Schema para crear un nuevo cliente"""
    customer_id: int = Field(..., description="ID del cliente (para sincronizacion)")
    password: str = Field(..., min_length=8)
    agent_id: Optional[int] = Field(None, description="ID del agente/seller asignado")


class CustomerUpdate(BaseModel):
    """Schema para actualizar un cliente existente"""
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    agent_id: Optional[int] = Field(None, description="ID del agente/seller asignado")


class Customer(CustomerBase):
    """Schema de respuesta con datos del cliente"""
    customer_id: int
    is_active: bool
    agent_id: Optional[int] = None

    class Config:
        from_attributes = True


class CustomerWithInfo(Customer):
    """
    Schema de respuesta que incluye informacion adicional del cliente
    (direccion, RFC, lista de precios, etc.)
    """
    business_name: Optional[str] = None
    rfc: Optional[str] = None
    price_list_id: Optional[int] = None
    sales_group_id: Optional[int] = None
    address_1: Optional[str] = None
    address_2: Optional[str] = None
    address_3: Optional[str] = None

    class Config:
        from_attributes = True


# ===== SCHEMA PARA SINCRONIZACIoN =====

class CustomerSync(BaseModel):
    """
    Schema unificado para sincronizar clientes desde DBF
    
    Combina campos de Customer y CustomerInfo en un solo schema
    para simplificar la sincronizacion masiva.
    """
    # === CUSTOMER (obligatorios) ===
    customer_id: int = Field(..., description="ID del cliente (del DBF)")
    username: str = Field(..., min_length=3, max_length=255, description="Nombre de usuario")
    password: str = Field(..., min_length=8, description="Contraseña inicial")
    
    # === CUSTOMER (opcionales) ===
    email: Optional[str] = Field(None, max_length=255, description="Email del cliente")
    full_name: Optional[str] = Field(None, max_length=255, description="Nombre completo")
    
    # === CUSTOMER INFO (opcionales) ===
    business_name: Optional[str] = Field(None, max_length=255, description="Nombre comercial/fiscal")
    rfc: Optional[str] = Field(None, max_length=13, description="RFC fiscal")
    price_list_id: Optional[int] = Field(None, description="ID de lista de precios asignada")
    sales_group_id: Optional[int] = Field(None, description="ID del grupo de ventas")
    address_1: Optional[str] = Field(None, description="Direccion principal")
    address_2: Optional[str] = Field(None, description="Direccion de entrega")
    address_3: Optional[str] = Field(None, description="Direccion de facturacion")
