"""
Schemas para Productos del Catálogo

Define la estructura de datos para productos farmacéuticos.

Sistema de precios:
1. base_price: Precio base sin impuestos ni margen
2. markup_percentage: % de ganancia según lista de precios del cliente
3. iva_percentage: % de IVA (impuesto)
4. final_price = (base_price * (1 + markup)) * (1 + iva)
"""

from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal


class CategoryInProduct(BaseModel):
    """
    Schema simplificado de categoría para incluir en productos
    
    Evita traer toda la información de la categoría cuando no se necesita.
    """
    category_id: int  # ID de la categoría
    name: str  # Nombre de la categoría
    
    model_config = {"from_attributes": True}


class ProductBase(BaseModel):
    """Schema base con todos los campos del producto"""
    product_id: str = Field(..., max_length=50)  # ID tipo texto "FAR74" (no numérico)
    codebar: Optional[str] = Field(None, max_length=100)  # Código de barras (puede ser None)
    name: str = Field(..., max_length=255)  # Nombre del producto
    description: Optional[str] = None  # Descripción principal (del DBF)
    descripcion_2: Optional[str] = None  # Descripción adicional (editada por admin, ej: receta)
    unidad_medida: Optional[str] = Field(None, max_length=50)  # "piezas", "cajas", "frascos"
    base_price: Decimal = Field(..., ge=0)  # Precio base sin markup ni IVA
    iva_percentage: Decimal = Field(0.00, ge=0, le=100)  # % de IVA (ej: 16.00)
    image_url: Optional[str] = Field(None, max_length=255)  # URL de la imagen (puede ser None)
    stock_count: int = Field(0, ge=0)  # Cantidad en inventario
    is_active: bool = True  # Si el producto está visible
    category_id: Optional[int] = None  # ID de la categoría (opcional)


class ProductCreate(BaseModel):
    """
    Schema para crear/actualizar un producto (UPSERT desde DBF)
    
    El product_id es REQUERIDO porque viene del sistema DBF:
    - Si el ID existe en BD: Se ACTUALIZA con los nuevos valores
    - Si el ID NO existe en BD: Se CREA nuevo registro
    
    Esto permite sincronización bidireccional manteniendo los IDs del DBF.
    
    IMPORTANTE sobre descripcion_2:
    - Al sincronizar desde DBF: NO se envía (es None)
    - El CRUD debe preservar el valor existente en BD
    - Solo se actualiza cuando el admin lo edita manualmente
    """
    product_id: str = Field(..., max_length=50)  # REQUERIDO: ID del DBF tipo "FAR74"
    codebar: Optional[str] = Field(None, max_length=100)  # Código de barras (puede ser None)
    name: str = Field(..., max_length=255)  # Nombre del producto
    description: Optional[str] = None  # Descripción principal
    descripcion_2: Optional[str] = None  # Descripción adicional (admin)
    unidad_medida: Optional[str] = Field(None, max_length=50)  # Unidad de medida
    base_price: Decimal = Field(..., ge=0)  # Precio base
    iva_percentage: Decimal = Field(0.00, ge=0, le=100)  # % de IVA
    image_url: Optional[str] = Field(None, max_length=255)  # URL imagen (puede ser None)
    stock_count: int = Field(0, ge=0)  # Cantidad en inventario
    is_active: bool = True  # Si el producto está visible
    category_id: Optional[int] = None  # ID de la categoría


class ProductCreate2(BaseModel):
    """
    Schema para crear/actualizar un producto (UPSERT desde DBF)
    
    El product_id es REQUERIDO porque viene del sistema DBF:
    - Si el ID existe en BD: Se ACTUALIZA con los nuevos valores
    - Si el ID NO existe en BD: Se CREA nuevo registro
    
    Esto permite sincronización bidireccional manteniendo los IDs del DBF.
    
    IMPORTANTE sobre descripcion_2:
    - Al sincronizar desde DBF: NO se envía (es None)
    - El CRUD debe preservar el valor existente en BD
    - Solo se actualiza cuando el admin lo edita manualmente
    """
    product_id: str = Field(..., max_length=50)  # REQUERIDO: ID del DBF tipo "FAR74"
    codebar: Optional[str] = Field(None, max_length=100)  # Código codebar único (puede ser None)
    name: str = Field(..., max_length=255)  # Nombre del producto
    description: Optional[str] = None  # Descripción principal
    descripcion_2: Optional[str] = None  # Descripción adicional (admin)
    unidad_medida: Optional[str] = Field(None, max_length=50)  # Unidad de medida
    base_price: Decimal = Field(..., ge=0)  # Precio base
    iva_percentage: Decimal = Field(0.00, ge=0, le=100)  # % de IVA
    image_url: Optional[str] = Field(None, max_length=255)  # URL imagen (puede ser None)
    stock_count: int = Field(0, ge=0)  # Cantidad en inventario
    is_active: bool = True  # Si el producto está visible
    category_name: Optional[str] = None  # Nombre de la categoría



class ProductUpdate(BaseModel):
    """
    Schema para actualizar un producto existente
    
    Todos los campos son opcionales (solo se actualiza lo que se envía).
    """
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    descripcion_2: Optional[str] = None  # Descripción adicional (admin)
    unidad_medida: Optional[str] = Field(None, max_length=50)  # Unidad de medida
    base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    iva_percentage: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    image_url: Optional[str] = Field(None, max_length=255)
    stock_count: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class Product(ProductBase):
    """
    Schema completo de producto para responses
    
    Incluye información de la categoría si está disponible.
    """
    product_id: str  # ID tipo texto "FAR74"
    category: Optional[CategoryInProduct] = None  # Categoría asociada (opcional)

    model_config = {"from_attributes": True}


class ProductWithPrice(Product):
    """
    Producto con precio final calculado para un cliente específico
    
    Este schema se usa cuando se muestra el catálogo a un cliente,
    aplicando el markup de su lista de precios.
    
    Cálculo:
    - price_with_markup = base_price * (1 + markup_percentage/100)
    - iva_amount = price_with_markup * (iva_percentage/100)
    - final_price = price_with_markup + iva_amount
    """
    markup_percentage: Decimal = Field(0.00, description="% de markup aplicado del cliente")
    price_with_markup: Decimal = Field(..., description="Precio base + markup")
    iva_amount: Decimal = Field(..., description="Monto de IVA calculado")
    final_price: Decimal = Field(..., description="Precio final total (con markup e IVA)")


class CatalogProduct(Product):
    """
    Producto del catálogo con precios calculados para el cliente
    
    Versión simplificada de ProductWithPrice para el catálogo de clientes.
    
    Incluye:
    - Todos los campos del producto base
    - final_price: Precio con markup e IVA aplicados
    - markup_percentage: % de ganancia del cliente
    
    Cálculo:
    - final_price = (base_price * (1 + markup/100)) * (1 + iva/100)
    """
    final_price: Decimal = Field(..., description="Precio final con markup e IVA")
    markup_percentage: Decimal = Field(..., description="% de markup del cliente")
    
    model_config = {"from_attributes": True}