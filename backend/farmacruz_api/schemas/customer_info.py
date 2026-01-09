"""
Schemas para Informacion Comercial de Clientes (CustomerInfo)

Define la estructura de datos para informacion adicional de clientes:
- Datos fiscales (RFC, razon social)
- Grupo de ventas asignado
- Lista de precios asignada
- Hasta 3 direcciones de envio

Relacion 1:1 con Customer (cada cliente tiene una CustomerInfo).
"""

from pydantic import BaseModel, Field
from typing import Optional


class CustomerInfoBase(BaseModel):
    """Schema base con informacion comercial del cliente"""
    business_name: str = Field(..., max_length=255)  # Razon social de la empresa
    rfc: Optional[str] = Field(None, max_length=13)  # RFC mexicano (12-13 caracteres)
    sales_group_id: Optional[int] = None  # Grupo de ventas al que pertenece
    price_list_id: Optional[int] = None  # Lista de precios asignada
    # Tres direcciones posibles para envio
    address_1: Optional[str] = None  # Direccion principal
    address_2: Optional[str] = None  # Direccion secundaria (opcional)
    address_3: Optional[str] = None  # Direccion terciaria (opcional)


class CustomerInfoCreate(CustomerInfoBase):
    """
    Schema para crear informacion comercial de un cliente
    
    El admin debe proporcionar los IDs (para sincronizacion).
    """
    customer_info_id: int  # Admin debe proporcionar este ID
    customer_id: int  # ID del cliente asociado (cambio de user_id)


class CustomerInfoUpdate(BaseModel):
    """
    Schema para actualizar informacion comercial
    
    Todos los campos son opcionales (solo se actualiza lo que se envia).
    """
    business_name: Optional[str] = Field(None, max_length=255)
    rfc: Optional[str] = Field(None, max_length=13)
    sales_group_id: Optional[int] = None  # Cambiar de grupo
    price_list_id: Optional[int] = None  # Cambiar lista de precios
    address_1: Optional[str] = None  # Actualizar direccion 1
    address_2: Optional[str] = None  # Actualizar direccion 2
    address_3: Optional[str] = None  # Actualizar direccion 3


class CustomerInfo(CustomerInfoBase):
    """
    Schema completo de informacion comercial para responses
    
    Incluye los IDs generados automaticamente.
    """
    customer_info_id: int  # ID unico de este registro
    customer_id: int  # ID del cliente asociado (cambio de user_id)

    model_config = {"from_attributes": True}


class CustomerInfoWithDetails(CustomerInfo):
    """
    CustomerInfo con detalles del grupo y lista de precios
    
    util para mostrar informacion completa sin hacer queries adicionales.
    Incluye nombres en lugar de solo IDs.
    """
    sales_group_name: Optional[str] = None  # Nombre del grupo de ventas
    price_list_name: Optional[str] = None  # Nombre de la lista de precios
    markup_percentage: Optional[float] = None  # % de markup de la lista