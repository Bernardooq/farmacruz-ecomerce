"""
Schemas para Grupos de Ventas (SalesGroups)

Los grupos de ventas organizan la estructura comercial:
- Multiples marketing managers pueden administrar un grupo
- Multiples sellers pueden atender un grupo
- Multiples customers pertenecen a un grupo

Esto permite segmentar clientes y asignar equipos especificos.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# SALES GROUPS (Grupos de Ventas)

class SalesGroupBase(BaseModel):
    """Schema base con campos comunes de grupo de ventas"""
    group_name: str = Field(..., max_length=255)  # Nombre del grupo (ej: "Farmacias Zona Norte")
    description: Optional[str] = None  # Descripcion del grupo


class SalesGroupCreate(SalesGroupBase):
    """
    Schema para crear un nuevo grupo de ventas
    
    Por defecto se crea activo.
    """
    is_active: Optional[bool] = True  # Activo por defecto


class SalesGroupUpdate(BaseModel):
    """
    Schema para actualizar un grupo existente
    
    Todos los campos son opcionales.
    """
    group_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    is_active: Optional[bool] = None  # Activar/desactivar grupo


class SalesGroupInDBBase(SalesGroupBase):
    """Schema base de grupo en la base de datos"""
    sales_group_id: int  # ID unico del grupo
    is_active: bool  # Estado del grupo
    created_at: datetime  # Fecha de creacion

    model_config = {"from_attributes": True}


class SalesGroup(SalesGroupInDBBase):
    """Schema completo de grupo para responses"""
    pass


# GROUP MARKETING MANAGERS (N:M Relationship)

class GroupMarketingManagerBase(BaseModel):
    """
    Relacion entre un grupo y un marketing manager
    
    Permite que un manager este en multiples grupos.
    """
    sales_group_id: int  # ID del grupo
    marketing_id: int  # ID del usuario marketing


class GroupMarketingManagerCreate(GroupMarketingManagerBase):
    """Schema para asignar un marketing manager a un grupo"""
    pass


class GroupMarketingManagerInDBBase(GroupMarketingManagerBase):
    """Schema de relacion en base de datos"""
    group_marketing_id: int  # ID unico de la relacion
    assigned_at: datetime  # Cuando se asigno

    model_config = {"from_attributes": True}


class GroupMarketingManager(GroupMarketingManagerInDBBase):
    """Schema completo de la relacion para responses"""
    pass


# GROUP SELLERS (N:M Relationship)

class GroupSellerBase(BaseModel):
    """
    Relacion entre un grupo y un vendedor
    
    Permite que un seller este en multiples grupos.
    """
    sales_group_id: int  # ID del grupo
    seller_id: int  # ID del usuario seller


class GroupSellerCreate(GroupSellerBase):
    """Schema para asignar un seller a un grupo"""
    pass


class GroupSellerInDBBase(GroupSellerBase):
    """Schema de relacion en base de datos"""
    group_seller_id: int  # ID unico de la relacion
    assigned_at: datetime  # Cuando se asigno

    model_config = {"from_attributes": True}


class GroupSeller(GroupSellerInDBBase):
    """Schema completo de la relacion para responses"""
    pass


# SCHEMAS EXTENDIDOS

class SalesGroupWithMembers(SalesGroupInDBBase):
    """
    Grupo con contadores de miembros
    
    util para mostrar estadisticas del grupo sin cargar todos los miembros.
    Muestra cuantos marketing managers, sellers y customers tiene el grupo.
    """
    marketing_count: Optional[int] = 0  # Numero de marketing managers
    seller_count: Optional[int] = 0  # Numero de sellers
    customer_count: Optional[int] = 0  # Numero de customers
