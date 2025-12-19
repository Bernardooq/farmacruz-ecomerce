"""
Clase Base CRUD para Operaciones Genéricas de Base de Datos

Proporciona operaciones CRUD estándar (Create, Read, Update, Delete)
que pueden ser heredadas por clases CRUD específicas.

Basado en el patrón Repository para encapsular lógica de acceso a datos.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db.base import Base

# Type variables para tipado genérico
ModelType = TypeVar("ModelType", bound=Base)  # Modelo SQLAlchemy
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)  # Schema de creación
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)  # Schema de actualización


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    Clase base genérica para operaciones CRUD
    
    Proporciona implementaciones por defecto de:
    - get: Obtener un registro por ID
    - get_multi: Obtener múltiples registros con paginación
    - create: Crear un nuevo registro
    - update: Actualizar un registro existente
    - delete: Eliminar un registro
    
    Uso:
        class CRUDProduct(CRUDBase[Product, ProductCreate, ProductUpdate]):
            pass
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Inicializa el CRUD base con un modelo SQLAlchemy
        
        Args:
            model: Clase del modelo SQLAlchemy a manejar
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        Obtiene un registro por su ID
        
        Args:
            db: Sesión de base de datos
            id: ID del registro a obtener
            
        Returns:
            Registro encontrado o None si no existe
        """
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        Obtiene múltiples registros con paginación
        
        Args:
            db: Sesión de base de datos
            skip: Número de registros a saltar (offset)
            limit: Número máximo de registros a devolver
            
        Returns:
            Lista de registros
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """
        Crea un nuevo registro en la base de datos
        
        Args:
            db: Sesión de base de datos
            obj_in: Schema Pydantic con los datos a crear
            
        Returns:
            Registro creado con ID generado
        """
        obj_in_data = jsonable_encoder(obj_in)  # Convierte a dict JSON-compatible
        db_obj = self.model(**obj_in_data)  # Crea instancia del modelo
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)  # Obtiene datos generados (ID, timestamps, etc.)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        Actualiza un registro existente
        
        Args:
            db: Sesión de base de datos
            db_obj: Registro existente a actualizar
            obj_in: Schema Pydantic o dict con los campos a actualizar
            
        Returns:
            Registro actualizado
            
        Note:
            Solo actualiza los campos proporcionados (exclude_unset=True)
        """
        obj_data = jsonable_encoder(db_obj)
        
        # Convertir schema a dict si es necesario
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        # Actualizar solo los campos proporcionados
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: int) -> ModelType:
        """
        Elimina un registro de la base de datos
        
        Args:
            db: Sesión de base de datos
            id: ID del registro a eliminar
            
        Returns:
            Registro eliminado
            
        Warning:
            Esto es un hard delete. Para soft delete, usar update con is_active=False
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj