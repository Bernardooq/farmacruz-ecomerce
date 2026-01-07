"""
Schemas para Categorías de Productos

Las categorías organizan productos en grupos lógicos.
Ejemplos: "Analgésicos", "Antibióticos", "Vitaminas"
"""

from pydantic import BaseModel, Field
from typing import Optional


class CategoryBase(BaseModel):
    """Schema base con campos comunes de categoría"""
    name: str = Field(..., max_length=100)  # Nombre de la categoría
    description: Optional[str] = None  # Descripción opcional


class CategoryCreate(CategoryBase):
    """Schema para crear una nueva categoría"""
    pass


class CategoryUpdate(CategoryBase):
    """Schema para actualizar una categoría existente"""
    pass


class CategorySync(CategoryBase):
    """Schema para sincronizar categorías desde DBF"""
    pass


class Category(CategoryBase):
    """
    Schema completo de categoría para responses
    
    Incluye el ID generado por la base de datos.
    """
    category_id: int  # ID único de la categoría

    model_config = {
        "from_attributes": True  # Permite crear desde modelo SQLAlchemy
    }