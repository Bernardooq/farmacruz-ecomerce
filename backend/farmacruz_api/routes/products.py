from fastapi import APIRouter, Depends
from typing import List
from schemas.product import ProductCreate, ProductUpdate, Product

# Importa tus dependencias, schemas y crud aquí
# from ....dependencies import get_current_user
# from ....schemas.product import Product
# from ....crud.crud_product import get_products

router = APIRouter()

@router.get("/", response_model=List[Product]) # Lista de productos
def read_products():

    # return get_products(db)
    return 

@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int):
    """
    Obtiene un producto específico por su ID.
    """
    # return get_product(db, product_id)
    return 

@router.post("/", response_model=Product)
def insert_product(product: ProductCreate):
    """
    Insertar producto en db
    """
    # return insert_product(db, product)
    return # product_insertion

@router.put("/{product_id}", response_model=Product)
def read_product(product_id: int, product: ProductUpdate):
    """
    Edita producto conociendo su ID 
    """
    # return update_product(db, product_id, product)
    return {"product_id": product_id, "name": f"Producto {product_id}"}

@router.delete("/{product_id}", response_model=Product)
def read_product(product_id: int):
    """
    Dropea producto conociendo su ID 
    """
    # return delete_product(db, product_id)
    return {"product_id": product_id, "name": f"Producto {product_id}"}