"""
CRUD para Productos (Products)

Funciones para manejar productos del catalogo:
- Operaciones CRUD basicas (Create, Read, Update, Delete)
- Busqueda y filtrado por categoria, stock, etc.
- Actualizacion de inventario
- Calculo de precios para clientes
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from db.base import Product
from schemas.product import ProductCreate, ProductUpdate
from crud.price_calculator import calculate_product_price_for_customer



def get_product(db: Session, product_id: str) -> Optional[Product]:
    # Obtiene un producto por ID con su categoria
    return db.query(Product).options(
        joinedload(Product.category)  # Eager load para evitar N+1 queries
    ).filter(Product.product_id == product_id).first()


def get_product_by_codebar(db: Session, codebar: str) -> Optional[Product]:
    # Obtiene un producto por su codebar (codigo unico)
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(Product.codebar == codebar).first()


def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None, is_active: Optional[bool] = None, stock_filter: Optional[str] = None,
    sort_by: Optional[str] = None, sort_order: Optional[str] = "asc", image: Optional[bool] = None  ) -> List[Product]:
    # Obtiene lista de productos con filtros y ordenamiento
    LOW_STOCK_THRESHOLD = 10  # Umbral para considerar bajo stock
    
    query = db.query(Product).options(joinedload(Product.category))
    
    # Filtros
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    if image is not None:
        if image:
            query = query.filter(Product.image_url.isnot(None))
        else:
            query = query.filter(Product.image_url.is_(None))
    
    # Filtrar por nivel de stock
    if stock_filter:
        if stock_filter == "out_of_stock":
            query = query.filter(Product.stock_count == 0)
        elif stock_filter == "low_stock":
            query = query.filter(
                Product.stock_count > 0,
                Product.stock_count < LOW_STOCK_THRESHOLD
            )
        elif stock_filter == "in_stock":
            query = query.filter(Product.stock_count >= LOW_STOCK_THRESHOLD)
    
    # Ordenamiento
    if sort_by == "price":
        # Ordenar por precio base
        if sort_order == "desc":
            query = query.order_by(Product.base_price.desc())
        else:
            query = query.order_by(Product.base_price.asc())
    elif sort_by == "name":
        # Ordenar por nombre
        if sort_order == "desc":
            query = query.order_by(Product.name.desc())
        else:
            query = query.order_by(Product.name.asc())
    else:
        # Orden por defecto: mas recientes primero
        query = query.order_by(Product.product_id.desc())
    
    return query.offset(skip).limit(limit).all()


def search_products(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Product]:
    # Busca productos por ID, nombre o descripcion
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(
        (Product.product_id.ilike(f"%{search}%")) |  # Buscar por ID
        (Product.name.ilike(f"%{search}%")) | 
        (Product.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    # Crea un nuevo producto en el catalogo
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: str,product: ProductUpdate) -> Optional[Product]:
    # Actualiza un producto existente
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    # Actualizar solo campos proporcionados
    update_data = product.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_product, field, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: str) -> Optional[Product]:
    # Elimina un producto (soft delete)
    db_product = get_product(db, product_id)
    if db_product:
        db_product.is_active = False
        db.commit()
        db.refresh(db_product)
    return db_product


def update_stock(db: Session, product_id: str, quantity: int) -> Optional[Product]:
    # Actualiza el stock de un producto
    db_product = get_product(db, product_id)
    if db_product:
        db_product.stock_count += quantity
        db.commit()
        db.refresh(db_product)
    return db_product