"""
Schemas para Categorias de Productos

Las categorias organizan productos en grupos logicos.
Ejemplos: "Analgesicos", "Antibioticos", "Vitaminas"
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    """Schema base con campos comunes de categoria"""
    name: str = Field(..., max_length=100)  # Nombre de la categoria
    description: Optional[str] = None  # Descripcion opcional
    updated_at: Optional[datetime] = None  # Fecha de ultima actualizacion en formato datetime


class CategoryCreate(CategoryBase):
    """Schema para crear una nueva categoria"""
    pass


class CategoryUpdate(CategoryBase):
    """Schema para actualizar una categoria existente"""
    pass


class CategorySync(CategoryBase):
    """Schema para sincronizar categorias desde DBF"""
    pass


class Category(CategoryBase):
    """
    Schema completo de categoria para responses
    
    Incluye el ID generado por la base de datos.
    """
    category_id: int  # ID unico de la categoria

    model_config = {
        "from_attributes": True  # Permite crear desde modelo SQLAlchemy
    }