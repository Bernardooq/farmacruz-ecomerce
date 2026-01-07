"""
Routes para Administración de Productos

Endpoints CRUD para gestión de productos del catálogo:
- GET / - Lista de productos con filtros
- GET /{id} - Detalle de producto
- GET /codebar/{codebar} - Buscar por codebar
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
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from schemas.product import ProductCreate, ProductUpdate, Product
from crud.crud_product import (
    get_products, 
    get_product, 
    get_product_by_codebar,
    create_product,
    update_product,
    delete_product,
    search_products,
    update_stock
)

router = APIRouter()


class StockUpdate(BaseModel):
    """
    Schema para ajustar inventario
    
    quantity puede ser:
    - Positivo: Agregar stock (recepción)
    - Negativo: Reducir stock (ajuste)
    """
    quantity: int


@router.get("/", response_model=List[Product])
def read_products(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(100, ge=1, le=200, description="Máximo de registros"),
    category_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    is_active: Optional[bool] = Query(True, description="Filtrar por estado"),
    search: Optional[str] = Query(None, description="Buscar por nombre/descripción"),
    stock_filter: Optional[str] = Query(None, description="Filtrar por stock: in_stock, out_of_stock, low_stock"),
    sort_by: Optional[str] = Query(None, description="Ordenar por: price, name"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    db: Session = Depends(get_db)
):
    """
    Lista de productos con filtros y ordenamiento
    
    Si search está presente, ignora otros filtros.
    
    Returns:
        Lista de productos con categorías precargadas
    """
    if search:
        products = search_products(db, search=search, skip=skip, limit=limit)
    else:
        products = get_products(
            db, 
            skip=skip, 
            limit=limit, 
            category_id=category_id,
            is_active=is_active,
            stock_filter=stock_filter,
            sort_by=sort_by,
            sort_order=sort_order
        )
    return products


@router.get("/{product_id}", response_model=Product)
def read_product(product_id: str, db: Session = Depends(get_db)):
    """
    Detalle de un producto específico
    
    Incluye categoría precargada.
    
    Raises:
        404: Si el producto no existe
    """
    product = get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product


@router.get("/codebar/{codebar}", response_model=Product)
def read_product_by_codebar(codebar: str, db: Session = Depends(get_db)):
    """
    Buscar producto por codebar (código único)
    
    Útil para validaciones y búsquedas por código de barras.
    
    Raises:
        404: Si el codebar no existe
    """
    product = get_product_by_codebar(db, codebar=codebar)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_new_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Crea un nuevo producto
    
    Validaciones:
    - base_price > 0
    - iva_percentage entre 0 y 100
    - stock_count >= 0
    - codebar único
    
    Permisos: Solo administradores
    
    Raises:
        400: Validaciones fallidas o codebar duplicado
    """
    # === VALIDAR PRECIO BASE ===
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
    
    # === VERIFICAR codebar ÚNICO ===
    db_product = get_product_by_codebar(db, codebar=product.codebar)
    if db_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El codebar '{product.codebar}' ya está registrado"
        )
    
    return create_product(db=db, product=product)


@router.put("/{product_id}", response_model=Product)
def update_existing_product(
    product_id: str,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Actualiza un producto existente
    
    Solo actualiza campos proporcionados (partial update).
    
    Validaciones (si el campo se proporciona):
    - base_price > 0
    - iva_percentage entre 0 y 100
    
    Permisos: Solo administradores
    
    Raises:
        400: Validaciones fallidas
        404: Producto no encontrado
    """
    # === VALIDAR PRECIO BASE ===
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
    
    # === VALIDAR IVA ===
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


@router.delete("/{product_id}", response_model=Product)
def delete_existing_product(
    product_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Elimina un producto (soft delete)
    
    Marca el producto como inactivo (is_active = False).
    No elimina el registro de la BD (preserva historial).
    
    Permisos: Solo administradores
    
    Raises:
        404: Producto no encontrado
    """
    db_product = delete_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return db_product


@router.patch("/{product_id}/stock", response_model=Product)
def adjust_product_stock(
    product_id: str,
    stock_update: StockUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Ajusta el inventario de un producto
    
    quantity puede ser positivo (agregar) o negativo (reducir).
    
    Valida que el stock resultante no sea negativo.
    
    Ejemplos:
        - Recibir 100 unidades: quantity = 100
        - Ajuste por merma de 5: quantity = -5
    
    Permisos: Solo administradores
    
    Raises:
        400: Stock resultante sería negativo
        404: Producto no encontrado
    """
    # === OBTENER PRODUCTO ACTUAL ===
    current_product = get_product(db, product_id=product_id)
    if not current_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # === CALCULAR Y VALIDAR NUEVO STOCK ===
    new_stock = current_product.stock_count + stock_update.quantity
    
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede restar {abs(stock_update.quantity)} unidades. Stock actual: {current_product.stock_count}"
        )
    
    db_product = update_stock(db, product_id=product_id, quantity=stock_update.quantity)
    
    return db_product