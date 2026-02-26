"""
Routes para Administracion de Productos

Endpoints CRUD para gestion de productos del catalogo:
- GET / - Lista de productos con filtros
- GET /{id} - Detalle de producto
- GET /codebar/{codebar} - Buscar por codebar
- GET /{id}/similar - Productos similares basados en componentes
- POST / - Crear producto
- PUT /{id} - Actualizar producto
- DELETE /{id} - Eliminar producto (soft delete)
- PATCH /{id}/stock - Ajustar inventario

Permisos:
- GET: Todos los usuarios
- POST/PUT/DELETE/PATCH: Solo administradores

Nota: Los precios finales para clientes se calculan en /catalog
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user, get_current_user
from schemas.product import ProductCreate, ProductUpdate, Product
from crud.crud_product import (
    get_products, 
    get_product, 
    get_product_by_codebar,
    create_product,
    update_product,
    delete_product,
    search_products,
    update_stock,
    get_similar_products
)

router = APIRouter()


class StockUpdate(BaseModel):
    # Schema para ajustar inventario
    quantity: int

""" GET / - Lista de productos con filtros """
@router.get("/", response_model=List[Product])
def read_products(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Maximo de registros"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoria"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado: True=activos, False=inactivos, None=todos"),
    search: Optional[str] = Query(None, description="Buscar por nombre/descripcion"),
    stock_filter: Optional[str] = Query(None, description="Filtrar por stock: in_stock, out_of_stock, low_stock"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: price, name"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    image: Optional[bool] = Query(None, description="Filtrar por imagen"),
    db: Session = Depends(get_db)
):
    # Lista de productos con filtros y ordenamiento
    if search:
        products = search_products(db, search=search, skip=skip, limit=limit)
    else:
        products = get_products(db, skip=skip, limit=limit, category_id=category_id, is_active=is_active, stock_filter=stock_filter,
            sort_by=sort_by, sort_order=sort_order, image=image)
    return products

""" GET /{id} - Detalle de producto especifico """
@router.get("/{product_id}", response_model=Product)
def read_product(product_id: str, db: Session = Depends(get_db)):
    # Detalle de un producto especifico
    product = get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

""" GET /codebar/{codebar} - Buscar producto por codebar (codigo unico) """
@router.get("/codebar/{codebar}", response_model=Product)
def read_product_by_codebar(codebar: str, db: Session = Depends(get_db)):
    # Buscar producto por codebar (codigo unico) 
    product = get_product_by_codebar(db, codebar=codebar)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

""" POST / - Crear un nuevo producto """
@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_new_product(product: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Crea un nuevo producto
    if product.base_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio base no puede ser negativo"
        )
    
    if product.base_price == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio base debe ser mayor a 0"
        )
    
    # === VALIDAR IVA ===
    if product.iva_percentage < 0 or product.iva_percentage > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El porcentaje de IVA debe estar entre 0 y 100"
        )
    
    # === VALIDAR STOCK ===
    if product.stock_count < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock no puede ser negativo"
        )
    
    # === VERIFICAR codebar uNICO ===
    db_product = get_product_by_codebar(db, codebar=product.codebar)
    if db_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El codebar '{product.codebar}' ya esta registrado"
        )
    
    return create_product(db=db, product=product)

""" PUT /{product_id} - Actualizar un producto existente """
@router.put("/{product_id}", response_model=Product)
def update_existing_product(product_id: str, product: ProductUpdate,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Actualiza un producto existente
    if product.base_price is not None:
        if product.base_price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio base no puede ser negativo"
            )
        if product.base_price == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio base debe ser mayor a 0"
            )
    
    # validar IVA
    if product.iva_percentage is not None:
        if product.iva_percentage < 0 or product.iva_percentage > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El porcentaje de IVA debe estar entre 0 y 100"
            )
    
    db_product = update_product(db, product_id=product_id, product=product)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return db_product

""" DELETE /{product_id} - Eliminar un producto (soft delete) """
@router.delete("/{product_id}", response_model=Product)
def delete_existing_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    # Elimina un producto (soft delete)
    try:
        db_product = delete_product(db, product_id=product_id)
        if not db_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        return db_product
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el producto porque ya forma parte de uno o más pedidos."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error inesperado al eliminar: {str(e)}"
        )

""" PATCH /{product_id}/stock - Ajustar inventario de un producto """
@router.patch("/{product_id}/stock", response_model=Product)
def adjust_product_stock(
    product_id: str,
    stock_update: StockUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    # Ajusta el inventario de un producto (positivo o negativo)
    current_product = get_product(db, product_id=product_id)
    if not current_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    new_stock = current_product.stock_count + stock_update.quantity
    
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede restar {abs(stock_update.quantity)} unidades. Stock actual: {current_product.stock_count}"
        )
    
    db_product = update_stock(db, product_id=product_id, quantity=stock_update.quantity)
    
    return db_product


""" GET /{product_id}/similar - Obtiene productos similares basados en componentes activos """
@router.get("/{product_id}/similar")
def read_similar_products(
    product_id: str,
    limit: int = Query(5, ge=1, le=10, description="Cantidad maxima de productos similares (max 10)"),
    min_similarity: float = Query(0.3, ge=0.1, le=1.0, description="Umbral minimo de similitud (0.1-1.0)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Encuentra productos similares basados en componentes activos en descripcion_2.
    
    Algoritmo:
    - Extrae componentes de descripcion_2 (ej: AMANTADINA, CLORFENAMINA, PARACETAMOL)
    - Calcula similitud con otros productos usando Jaccard similarity
    - Retorna top N productos con mayor similitud
    - Si el usuario está autenticado, usa su lista de precios para calcular precios
    
    Returns:
        {
            "target_product": {...},
            "similar_products": [
                {
                    "product": {...},
                    "similarity_score": 0.85,
                    "price_info": {...}
                }
            ]
        }
    """
    # Verificar que el producto existe
    target_product = get_product(db, product_id=product_id)
    if not target_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Obtener price_list_id del cliente autenticado
    price_list_id = None
    if current_user and hasattr(current_user, 'customer_info') and current_user.customer_info:
        price_list_id = current_user.customer_info.price_list_id
    
    # Obtener productos similares
    similar_products = get_similar_products(
        db=db,
        product_id=product_id,
        price_list_id=price_list_id,
        limit=limit,
        min_similarity=min_similarity
    )
    
    return {
        "target_product": target_product,
        "similar_products": similar_products
    }