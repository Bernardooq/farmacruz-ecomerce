"""
CRUD para Productos (Products)

Funciones para manejar productos del catalogo:
- Operaciones CRUD basicas (Create, Read, Update, Delete)
- Busqueda y filtrado por categoria, stock, etc.
- Actualizacion de inventario
- Calculo de precios para clientes
- Productos similares basados en componentes activos
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from utils.price_utils import get_product_final_price, format_price_info

from db.base import Product
from schemas.product import ProductCreate, ProductUpdate
from utils.product_similarity import extract_active_components, calculate_similarity_score


""" Obtiene un producto por ID con su categoria """
def get_product(db: Session, product_id: str) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.category)  
    ).filter(Product.product_id == product_id).first()

""" Obtiene un producto por codigo de barras con su categoria """
def get_product_by_codebar(db: Session, codebar: str) -> Optional[Product]:
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(Product.codebar == codebar).first()

""" Obtiene lista de productos con filtros y ordenamiento """
def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None, is_active: Optional[bool] = None, stock_filter: Optional[str] = None,
    sort_by: Optional[str] = None, sort_order: Optional[str] = "asc", image: Optional[bool] = None  ) -> List[Product]:
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

""" Busca productos por ID, nombre o descripcion """
def search_products(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(
        (Product.product_id.ilike(f"%{search}%")) |  # Buscar por ID
        (Product.name.ilike(f"%{search}%")) | 
        (Product.description.ilike(f"%{search}%"))
    ).offset(skip).limit(limit).all()

""" Crea un nuevo producto en el catalogo """
def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

""" Actualiza un producto existente """
def update_product(db: Session, product_id: str,product: ProductUpdate) -> Optional[Product]:
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

""" Elimina (soft delete) un producto """
def delete_product(db: Session, product_id: str) -> Optional[Product]:
    # Elimina un producto
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
    return db_product

""" Actualiza el stock de un producto """
def update_stock(db: Session, product_id: str, quantity: int) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if db_product:
        if db_product.stock_count + quantity < 0:
            raise ValueError("Stock no puede ser negativo")
        db_product.stock_count += quantity
        db.commit()
        db.refresh(db_product)
    return db_product


""" Encuentra productos similares basados en componentes activos """
def get_similar_products(
    db: Session,
    product_id: str,
    price_list_id: Optional[int] = None,
    limit: int = 5,
    min_similarity: float = 0.3
) -> List[dict]:
    """
    Encuentra productos similares basados en componentes de descripcion_2.
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto objetivo
        price_list_id: ID de lista de precios para calcular precios (opcional)
        limit: Máximo número de productos similares a retornar (default: 5)
        min_similarity: Umbral mínimo de similitud (default: 0.3 = 30%)
    
    Returns:
        Lista de diccionarios con:
        - product: Producto similar
        - similarity_score: Score de similitud (0.0 - 1.0)
        - price_info: Información de precios si price_list_id está presente
    """
    # Obtener producto objetivo
    target_product = get_product(db, product_id)
    if not target_product:
        return []
    
    # Extraer componentes del producto objetivo
    target_components = extract_active_components(target_product.descripcion_2)
    if not target_components:
        return []
    
    # Obtener todos los productos activos (excepto el objetivo)
    all_products = db.query(Product).filter(
        Product.is_active == True,
        Product.product_id != product_id,
        Product.descripcion_2.isnot(None)  # Solo productos con descripcion_2
    ).all()
    
    # Calcular similitud para cada producto
    similarities = []
    for product in all_products:
        product_components = extract_active_components(product.descripcion_2)
        if not product_components:
            continue
        
        score = calculate_similarity_score(target_components, product_components)
        if score >= min_similarity:
            similarities.append((product, score))
    
    # Ordenar por score descendente y tomar top N
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_similar = similarities[:limit]
    
    # Formatear resultados con información de precios
    results = []
    for product, score in top_similar:
        result = {
            "product": product,
            "similarity_score": round(score, 3),
            "price_info": None
        }
        
        # Calcular precios según la lista del cliente
        if price_list_id:
            price_data = get_product_final_price(db, product, price_list_id)
            
            if price_data:
                result["price_info"] = format_price_info(
                    base_price=price_data["base_price"],
                    markup_percentage=price_data["markup_percentage"],
                    final_price=price_data["final_price"]
                )
        
        results.append(result)
    
    return results