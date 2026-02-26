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

from db.base import Product, ProductRecommendation
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
            # Tiene imagen: image_url no es NULL ni string vacío
            query = query.filter(
                Product.image_url.isnot(None),
                Product.image_url != ""
            )
        else:
            # Sin imagen: image_url es NULL o string vacío
            query = query.filter(
                (Product.image_url.is_(None)) | (Product.image_url == "")
            )
    
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
        (Product.description.ilike(f"%{search}%")) |
        (Product.descripcion_2.ilike(f"%{search}%"))  # Buscar por descripcion adicional
    ).offset(skip).limit(limit).all()

""" Crea un nuevo producto en el catalogo """
def create_product(db: Session, product: ProductCreate) -> Product:
    product_data = product.model_dump()
    # Normalizar image_url: guardar NULL en vez de string vacío
    if not product_data.get("image_url"):
        product_data["image_url"] = None
    db_product = Product(**product_data)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

""" Actualiza un producto existente """
def update_product(db: Session, product_id: str, product: ProductUpdate) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if not db_product:
        return None
    
    # Actualizar solo campos proporcionados
    update_data = product.dict(exclude_unset=True)
    # Normalizar image_url: guardar NULL en vez de string vacío
    if "image_url" in update_data and not update_data["image_url"]:
        update_data["image_url"] = None
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



def get_similar_products(
    db: Session,
    product_id: str,
    price_list_id: Optional[int] = None,
    limit: int = 5,
    min_similarity: float = 0.3
) -> List[dict]:
    """
    Versión Optimizada v2.1: 
    Usa la tabla pre-calculada 'product_recommendations' para encontrar similitudes.
    Retorna productos en formato seguro (sin base_price) igual que el catálogo.
    """
    
    recommendations = (
        db.query(ProductRecommendation)
        .filter(
            ProductRecommendation.product_id == product_id,
            ProductRecommendation.score >= min_similarity
        )
        .options(joinedload(ProductRecommendation.recommended_product))
        .order_by(ProductRecommendation.score.desc())
        .limit(limit)
        .all()
    )

    if not recommendations:
        return []

    results = []
    
    for rec in recommendations:
        product = rec.recommended_product  # Usar recommended_product, no target_product 
        
        if not product.is_active:
            continue

        # Obtener precio si el cliente tiene price_list
        final_price = None
        markup_percentage = 0.0
        
        if price_list_id:
            price_data = get_product_final_price(db, product, price_list_id)
            if price_data:
                final_price = price_data["final_price"]
                markup_percentage = price_data["markup_percentage"]
        
        # Construir dict del producto SIN base_price (igual que catálogo)
        product_dict = {
            'product_id': product.product_id,
            'codebar': product.codebar,
            'name': product.name,
            'description': product.description,
            'descripcion_2': product.descripcion_2,
            'unidad_medida': product.unidad_medida,
            # base_price: EXCLUIDO - información sensible
            # iva_percentage: EXCLUIDO - ya incluido en final_price
            'image_url': product.image_url,
            'stock_count': product.stock_count,
            'is_active': product.is_active,
            'category_id': product.category_id,
            'category': product.category,
            'final_price': float(final_price) if final_price else None,
            'markup_percentage': float(markup_percentage)
        }
        
        result = {
            "product": product_dict,  # ← Ahora es dict seguro, no ORM object
            "similarity_score": round(float(rec.score), 3)
        }
        
        results.append(result)

    return results