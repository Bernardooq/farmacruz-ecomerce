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
from utils.price_utils import get_product_final_price, format_price_info, apply_iva

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
def get_products(db: Session, skip: int = 0, limit: int = 100, category_id: Optional[int] = None, 
                 is_active: Optional[bool] = None, stock_filter: Optional[str] = None,
                 sort_by: Optional[str] = None, sort_order: Optional[str] = "asc", 
                 image: Optional[bool] = None, search: Optional[str] = None) -> List[Product]:
    LOW_STOCK_THRESHOLD = 10  # Umbral para considerar bajo stock
    query = db.query(Product).options(joinedload(Product.category))
    
    # Filtros base
    if category_id is not None:
        query = query.filter(Product.category_id == category_id)
    
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    if image is not None:
        if image:
            query = query.filter(Product.image_url.isnot(None), Product.image_url != "")
        else:
            query = query.filter((Product.image_url.is_(None)) | (Product.image_url == ""))
    
    # Filtro de Búsqueda (Multi-palabra)
    if search:
        search_terms = search.strip().split()
        if search_terms:
            word_filters = []
            for term in search_terms:
                pattern = f"%{term}%"
                word_filters.append(
                    (Product.product_id.ilike(pattern)) |
                    (Product.name.ilike(pattern)) |
                    (Product.description.ilike(pattern)) |
                    (Product.descripcion_2.ilike(pattern)) |
                    (Product.codebar.ilike(pattern))
                )
            query = query.filter(and_(*word_filters))
    
    # Filtrar por nivel de stock
    if stock_filter:
        if stock_filter == "out_of_stock":
            query = query.filter(Product.stock_count == 0)
        elif stock_filter == "low_stock":
            query = query.filter(Product.stock_count > 0, Product.stock_count < LOW_STOCK_THRESHOLD)
        elif stock_filter == "in_stock":
            query = query.filter(Product.stock_count >= LOW_STOCK_THRESHOLD)
    
    # Ordenamiento
    if sort_by == "price":
        query = query.order_by(Product.base_price.desc()) if sort_order == "desc" else query.order_by(Product.base_price.asc())
    elif sort_by == "name":
        query = query.order_by(Product.name.desc()) if sort_order == "desc" else query.order_by(Product.name.asc())
    else:
        # Orden por defecto: mas recientes primero
        query = query.order_by(Product.product_id.desc())
    
    return query.offset(skip).limit(limit).all()

""" Busca productos por ID, nombre o descripcion (Soporta múltiples palabras) """
def search_products(db: Session, search: str, skip: int = 0, limit: int = 100) -> List[Product]:
    search_terms = search.strip().split()
    if not search_terms:
        return db.query(Product).offset(skip).limit(limit).all()
    
    # Cada palabra debe estar presente en al menos uno de los campos
    word_filters = []
    for term in search_terms:
        pattern = f"%{term}%"
        word_filters.append(
            (Product.product_id.ilike(pattern)) |
            (Product.name.ilike(pattern)) |
            (Product.description.ilike(pattern)) |
            (Product.descripcion_2.ilike(pattern))
        )
    
    return db.query(Product).options(
        joinedload(Product.category)
    ).filter(and_(*word_filters)).offset(skip).limit(limit).all()

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

""" Incrementa la version de la imagen para forzar refresco de cache """
def increment_image_version(db: Session, product_id: str) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if db_product:
        db_product.image_version = (db_product.image_version or 0) + 1
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
        iva_pct = 0.0
        
        if price_list_id:
            price_data = get_product_final_price(db, product, price_list_id)
            if price_data:
                price_without_iva = price_data["final_price"]  # Precio con markup, SIN IVA
                markup_percentage = price_data["markup_percentage"]
                iva_pct = float(product.iva_percentage or 0)
                # Aplicar IVA para obtener precio final
                from decimal import Decimal
                final_price = float(apply_iva(Decimal(str(price_without_iva)), Decimal(str(iva_pct))))
        
        # Construir dict del producto SIN base_price (igual que catálogo)
        product_dict = {
            'product_id': product.product_id,
            'codebar': product.codebar,
            'name': product.name,
            'description': product.description,
            'descripcion_2': product.descripcion_2,
            'unidad_medida': product.unidad_medida,
            # base_price: EXCLUIDO - información sensible
            # markup_percentage: EXCLUIDO - información sensible
            'iva_percentage': iva_pct,
            'image_url': product.image_url,
            'stock_count': product.stock_count,
            'is_active': product.is_active,
            'category_id': product.category_id,
            'category': product.category,
            'final_price': final_price,  # CON IVA
            'image_version': product.image_version,
        }
        
        result = {
            "product": product_dict,  # ← Ahora es dict seguro, no ORM object
            "similarity_score": round(float(rec.score), 3)
        }
        
        results.append(result)

    return results