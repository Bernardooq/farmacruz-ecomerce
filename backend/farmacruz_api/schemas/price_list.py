"""
Schemas para Listas de Precios (PriceLists) y PriceListItems

Sistema de precios con markup por producto:
- Cada PriceList es un contenedor (ej: "Farmacias Premium", "Hospitales")
- Cada PriceListItem define el markup de un producto específico en esa lista
- Los clientes se asignan a una lista, que determina sus precios

Ejemplo:
  PriceList: "Farmacias Premium"
    - Producto A: markup 25%
    - Producto B: markup 30%
  
  PriceList: "Distribuidoras"
    - Producto A: markup 10%
    - Producto B: markup 15%
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ==========================================
# PRICE LIST (Contenedor de listas de precios)
# ==========================================

class PriceListBase(BaseModel):
    """Schema base de lista de precios"""
    list_name: str = Field(..., max_length=100)  # Nombre de la lista (ej: "Premium")
    description: Optional[str] = None  # Descripción de a quién aplica


class PriceListCreate(PriceListBase):
    """
    Schema para crear una nueva lista de precios
    
    El ID es opcional (admin puede proporcionarlo o se auto-genera).
    """
    price_list_id: Optional[int] = None  # Opcional: admin puede proveer o se auto-genera
    is_active: Optional[bool] = True  # Activa por defecto


class PriceListUpdate(BaseModel):
    """
    Schema para actualizar una lista existente
    
    Todos los campos son opcionales.
    """
    list_name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None  # Activar/desactivar


class PriceListInDBBase(PriceListBase):
    """Schema de lista en base de datos"""
    price_list_id: int  # ID único de la lista
    is_active: bool  # Estado de la lista
    created_at: datetime  # Fecha de creación

    model_config = {"from_attributes": True}


class PriceList(PriceListInDBBase):
    """Schema completo de lista para responses"""
    pass


# ==========================================
# PRICE LIST ITEMS (Markup por producto)
# ==========================================

class PriceListItemBase(BaseModel):
    """
    Schema base de item de lista de precios
    
    Define el markup de UN producto en UNA lista.
    """
    product_id: int  # ID del producto
    markup_percentage: Decimal = Field(..., ge=0, decimal_places=2)  # % de ganancia (ej: 25.00)

    @field_validator('markup_percentage')
    @classmethod
    def validate_markup(cls, v):
        """Valida que el markup no sea negativo"""
        if v < 0:
            raise ValueError('El porcentaje de markup debe ser mayor o igual a 0')
        return v


class PriceListItemCreate(PriceListItemBase):
    """Schema para crear un item de lista"""
    pass


class PriceListItemUpdate(BaseModel):
    """
    Schema para actualizar el markup de un producto
    
    Solo se puede cambiar el porcentaje de markup.
    """
    markup_percentage: Decimal = Field(..., ge=0, decimal_places=2)

    @field_validator('markup_percentage')
    @classmethod
    def validate_markup(cls, v):
        """Valida que el markup no sea negativo"""
        if v < 0:
            raise ValueError('El porcentaje de markup debe ser mayor o igual a 0')
        return v


class PriceListItemInDB(PriceListItemBase):
    """Schema de item en base de datos"""
    price_list_item_id: int  # ID único del item
    price_list_id: int  # ID de la lista a la que pertenece
    created_at: datetime  # Cuándo se agregó
    updated_at: datetime  # Última actualización del markup

    model_config = {"from_attributes": True}


class PriceListItem(PriceListItemInDB):
    """Schema completo de item para responses"""
    pass


# ==========================================
# SCHEMAS EXTENDIDOS
# ==========================================

class PriceListWithItems(PriceList):
    """
    Lista de precios con todos sus items
    
    Útil para mostrar la lista completa con todos los markups.
    """
    items: List[PriceListItem] = []  # Lista de productos con sus markups


class PriceListItemsBulkUpdate(BaseModel):
    """
    Schema para actualizar múltiples productos a la vez
    
    Permite establecer el markup de varios productos en una sola operación.
    """
    items: List[PriceListItemCreate]  # Lista de items a actualizar


# ==========================================
# PRECIO CALCULATION (Cálculo de precio final)
# ==========================================

class PriceCalculation(BaseModel):
    """
    Resultado del cálculo de precio final para un producto
    
    Muestra el desglose completo:
    1. Precio base del producto
    2. Markup aplicado según lista del cliente
    3. IVA aplicado
    4. Precio final total
    
    Fórmula:
    - price_with_markup = base_price * (1 + markup_percentage/100)
    - iva_amount = price_with_markup * (iva_percentage/100)
    - final_price = price_with_markup + iva_amount
    """
    base_price: Decimal  # Precio base del producto
    markup_percentage: Decimal  # % de markup del cliente
    iva_percentage: Decimal  # % de IVA del producto
    price_with_markup: Decimal  # Precio con markup aplicado
    iva_amount: Decimal  # Monto del IVA
    final_price: Decimal  # Precio final total
