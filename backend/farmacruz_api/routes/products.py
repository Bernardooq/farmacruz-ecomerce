from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user, get_current_user
from schemas.product import ProductCreate, ProductUpdate, Product
from crud.crud_product import (
    get_products, 
    get_product, 
    get_product_by_sku,
    create_product,
    update_product,
    delete_product,
    search_products,
    update_stock
)

router = APIRouter()

class StockUpdate(BaseModel):
    quantity: int

@router.get("/", response_model=List[Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    is_active: Optional[bool] = True,
    search: Optional[str] = None,
    sort_by: Optional[str] = Query(None, description="Campo para ordenar: price"),
    sort_order: Optional[str] = Query("asc", description="Orden: asc o desc"),
    db: Session = Depends(get_db)
):
    """
    Obtiene lista de productos con filtros opcionales y ordenamiento
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
            sort_by=sort_by,
            sort_order=sort_order
        )
    return products

@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """
    Obtiene un producto específico por su ID
    """
    product = get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

@router.get("/sku/{sku}", response_model=Product)
def read_product_by_sku(sku: str, db: Session = Depends(get_db)):
    """
    Obtiene un producto por su SKU
    """
    product = get_product_by_sku(db, sku=sku)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    return product

@router.post("/", response_model=Product)
def create_new_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Crea un nuevo producto (solo administradores)
    """
    # Validar precio
    if product.price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio no puede ser negativo"
        )
    
    if product.price == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El precio debe ser mayor a 0"
        )
    
    # Validar stock
    if product.stock_count < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El stock no puede ser negativo"
        )
    
    # Verificar que el SKU no exista
    db_product = get_product_by_sku(db, sku=product.sku)
    if db_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El SKU ya está registrado"
        )
    
    return create_product(db=db, product=product)

@router.put("/{product_id}", response_model=Product)
def update_existing_product(
    product_id: int,
    product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Actualiza un producto existente (solo administradores)
    """
    # Validar precio si se está actualizando
    if product.price is not None:
        if product.price < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio no puede ser negativo"
            )
        if product.price == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El precio debe ser mayor a 0"
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
    product_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Elimina un producto (soft delete - solo administradores)
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
    product_id: int,
    stock_update: StockUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Ajusta el stock de un producto (solo administradores)
    """
    # Obtener el producto actual para validar
    current_product = get_product(db, product_id=product_id)
    if not current_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Producto no encontrado"
        )
    
    # Calcular el nuevo stock
    new_stock = current_product.stock_count + stock_update.quantity
    
    # Validar que el stock resultante no sea negativo
    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede restar {abs(stock_update.quantity)} unidades. Stock actual: {current_product.stock_count}"
        )
    
    db_product = update_stock(db, product_id=product_id, quantity=stock_update.quantity)
    
    return db_product