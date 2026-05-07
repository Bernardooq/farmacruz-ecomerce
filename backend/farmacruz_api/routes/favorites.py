from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from dependencies import get_db, get_current_user
from db.base import Customer
from schemas.favorite import FavoriteList, FavoriteListCreate, FavoriteListUpdate, FavoriteListItem, FavoriteListItemCreate
from crud import crud_favorite

router = APIRouter(tags=["favorites"])

def get_customer_id(current_user):
    if isinstance(current_user, Customer):
        return current_user.customer_id
    customer_id = getattr(current_user, 'user_id', None)
    if not customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo identificar el cliente")
    return customer_id

@router.get("/", response_model=List[FavoriteList])
def list_favorites(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    return crud_favorite.get_favorite_lists(db, customer_id)

@router.post("/", response_model=FavoriteList)
def create_favorite(obj_in: FavoriteListCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    try:
        return crud_favorite.create_favorite_list(db, customer_id, obj_in)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{list_id}", response_model=FavoriteList)
def get_favorite(list_id: UUID, skip: int = 0, limit: int = 15, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    db_obj = crud_favorite.get_favorite_list_details(db, list_id, customer_id, skip=skip, limit=limit)
    if not db_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada")
    return db_obj


@router.put("/{list_id}", response_model=FavoriteList)
def update_favorite(list_id: UUID, obj_in: FavoriteListUpdate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    try:
        db_obj = crud_favorite.update_favorite_list(db, list_id, customer_id, obj_in)
        if not db_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada")
        return db_obj
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{list_id}")
def delete_favorite(list_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    if not crud_favorite.delete_favorite_list(db, list_id, customer_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lista no encontrada")
    return {"message": "Lista eliminada correctamente"}

# --- Items en la lista ---

@router.post("/{list_id}/items", response_model=FavoriteListItem)
def add_item(list_id: UUID, item_in: FavoriteListItemCreate, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    try:
        return crud_favorite.add_item_to_favorite_list(db, list_id, customer_id, item_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{list_id}/items/{product_id}")
def remove_item(list_id: UUID, product_id: str, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    if not crud_favorite.remove_item_from_favorite_list(db, list_id, customer_id, product_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item no encontrado")
    return {"message": "Item eliminado de la lista"}

@router.post("/{list_id}/load-to-cart")
def load_to_cart(list_id: UUID, current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    customer_id = get_customer_id(current_user)
    try:
        return crud_favorite.load_favorite_list_to_cart(db, list_id, customer_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
