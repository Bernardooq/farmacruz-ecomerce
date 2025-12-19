"""
CRUD para Productos (Products)

Funciones para manejar productos del catálogo:
- Operaciones CRUD básicas (Create, Read, Update, Delete)
- Búsqueda y filtrado por categoría, stock, etc.
- Actualización de inventario
- Cálculo de precios para clientes
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from db.base import Product
from schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Obtiene un producto por ID con su categoría
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto
        
    Returns:
        Producto encontrado con categoría precargada, o None si no existe
    """
    return db.query(Product).options(
        joinedload(Product.category)  # Eager load para evitar N+1 queries
    ).filter(Product.product_id == product_id).first()


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """
    Obtiene un producto por su SKU (código único)
    
    Args:
        db: Sesión de base de datos
        sku: Código SKU del producto
        
    Returns:
        Producto encontrado con categoría precargada, o None si no existe
    """
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(Product.sku == sku).first()


def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    sort_by: Optional[str] = None,
    sort_order: Optional[str] = "asc"
) -> List[Product]:
    """
    Obtiene lista de productos con filtros y ordenamiento
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Máximo de registros a devolver
        category_id: Filtrar por categoría (opcional)
        is_active: Filtrar por estado activo/inactivo (opcional)
        sort_by: Campo para ordenar ("price", "name", o None para default)
        sort_order: Orden ascendente ("asc") o descendente ("desc")
        
    Returns:
        Lista de productos con categorías precargadas
    """
    query = db.query(Product).options(joinedload(Product.category))
    
    # === APLICAR FILTROS ===
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    # === APLICAR ORDENAMIENTO ===
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
        # Orden por defecto: más recientes primero
        query = query.order_by(Product.product_id.desc())
    
    return query.offset(skip).limit(limit).all()


def search_products(
    db: Session,
    search: str,
    skip: int = 0,
    limit: int = 100
) -> List[Product]:
    """
    Busca productos por nombre o descripción
    
    La búsqueda es insensible a mayúsculas/minúsculas.
    
    Args:
        db: Sesión de base de datos
        search: Término de búsqueda
        skip: Número de registros a saltar
        limit: Máximo de registros a devolver
        
    Returns:
        Lista de productos que coinciden con la búsqueda
    """
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(
        (Product.name.ilike(f"%{search}%")) | 
        (Product.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    """
    Crea un nuevo producto en el catálogo
    
    Args:
        db: Sesión de base de datos
        product: Schema con datos del producto a crear
        
    Returns:
        Producto creado con ID generado
    """
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(
    db: Session,
    product_id: int,
    product: ProductUpdate
) -> Optional[Product]:
    """
    Actualiza un producto existente
    
    Solo actualiza los campos proporcionados (exclude_unset=True).
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto a actualizar
        product: Schema con campos a actualizar
        
    Returns:
        Producto actualizado o None si no existe
    """
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


def delete_product(db: Session, product_id: int) -> Optional[Product]:
    """
    Elimina un producto (soft delete)
    
    No elimina el registro de la base de datos, solo lo marca
    como inactivo. Esto preserva:
    - Historial de pedidos con este producto
    - Integridad referencial
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto a eliminar
        
    Returns:
        Producto marcado como inactivo, o None si no existe
    """
    db_product = get_product(db, product_id)
    if db_product:
        db_product.is_active = False
        db.commit()
        db.refresh(db_product)
    return db_product


def update_stock(
    db: Session,
    product_id: int,
    quantity: int
) -> Optional[Product]:
    """
    Actualiza el stock de un producto
    
    Puede incrementar (quantity positivo) o decrementar (quantity negativo).
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto
        quantity: Cantidad a sumar/restar (puede ser negativo)
        
    Returns:
        Producto con stock actualizado, o None si no existe
        
    Example:
        update_stock(db, 1, +100)  # Agregar 100 unidades
        update_stock(db, 1, -5)    # Reducir 5 unidades (venta)
    """
    db_product = get_product(db, product_id)
    if db_product:
        db_product.stock_count += quantity
        db.commit()
        db.refresh(db_product)
    return db_product


def get_products_with_prices_for_customer(
    db: Session,
    customer_id: int,  # CORREGIDO: era user_id
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = None
) -> List:
    """
    Obtiene productos con precios calculados para un cliente específico
    
    Aplica el markup de la lista de precios del cliente y calcula
    el precio final con IVA. Útil para mostrar el catálogo personalizado.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente (CORREGIDO: era user_id)
        skip: Número de registros a saltar
        limit: Máximo de registros a devolver
        category_id: Filtrar por categoría (opcional)
        is_active: Filtrar por estado (opcional, default: True)
        
    Returns:
        Lista de ProductWithPrice con todos los precios calculados
    """
    from crud.price_calculator import calculate_product_price_for_customer
    
    # Obtener productos base
    products = get_products(
        db=db,
        skip=skip,
        limit=limit,
        category_id=category_id,
        is_active=is_active if is_active is not None else True
    )
    
    # Calcular precios para cada producto
    products_with_prices = []
    for product in products:
        product_with_price = calculate_product_price_for_customer(
            db=db,
            product_id=product.product_id,
            customer_id=customer_id  # CORREGIDO: era user_id
        )
        if product_with_price:
            products_with_prices.append(product_with_price)
    
    return products_with_prices
