"""
Routes para Grupos de Ventas (Sales Groups)

Gestion completa de grupos de ventas con relaciones N:M.

GRUPOS (CRUD):
- GET / - Lista de grupos con conteos
- GET /my-groups - Mis grupos (marketing/seller)
- GET /{id} - Detalle con conteos
- POST / - Crear grupo
- PUT /{id} - Actualizar grupo
- DELETE /{id} - Eliminar grupo (cascade)

MARKETING MANAGERS (N:M):
- POST /{id}/marketing - Asignar marketing manager
- DELETE /{id}/marketing/{user_id} - Remover marketing manager
- GET /{id}/marketing - Ver marketing managers (paginado)
- GET /{id}/available-marketing - Ver disponibles para agregar

SELLERS (N:M):
- POST /{id}/sellers - Asignar seller
- DELETE /{id}/sellers/{user_id} - Remover seller
- GET /{id}/sellers - Ver sellers (paginado)
- GET /{id}/available-sellers - Ver disponibles para agregar

CUSTOMERS (N:1):
- POST /{id}/customers/{customer_id} - Asignar customer
- DELETE /{id}/customers/{customer_id} - Remover customer
- GET /{id}/customers - Ver customers (paginado)
- GET /{id}/available-customers - Ver disponibles para agregar

UTILIDADES:
- GET /{id}/members - Ver todos los miembros (marketing + sellers)

Sistema de Permisos:
- Admin: Full access a todos los endpoints
- Marketing: Solo puede ver sus grupos asignados
- Seller: Solo puede ver sus grupos asignados

Relaciones N:M:
- Un grupo puede tener multiples marketing managers
- Un grupo puede tener multiples sellers
- Un marketing/seller puede estar en multiples grupos
- Un customer pertenece a UN solo grupo (N:1)
"""


from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel
from db.base import User as UserModel, UserRole


from dependencies import get_db, get_current_admin_user, get_current_seller_user
from schemas.sales_group import ( SalesGroup, SalesGroupCreate,
SalesGroupUpdate, SalesGroupWithMembers, GroupMarketingManager, GroupSeller, UserAssignment)

from schemas.user import User
from crud.crud_sales_group import ( get_available_customers, create_sales_group, get_available_marketing_managers, get_available_sellers, 
    get_group_customers_paginated, get_group_sellers_paginated, get_sales_group, get_sales_groups, get_user_groups, remove_customer_from_sales_group, 
    update_sales_group, delete_sales_group, get_sales_group_with_counts, assign_marketing_to_group, assign_seller_to_group, remove_marketing_from_group, 
    remove_seller_from_group, get_group_marketing_managers, get_group_sellers, get_group_marketing_managers_paginated, user_belongs_to_group
)

router = APIRouter()

### Sales Group Endpoints ###

""" GET / - Obtener todos los grupos de ventas con conteos de miembros """
@router.get("/", response_model=List[SalesGroupWithMembers])
def read_sales_groups(skip: int = 0, limit: int = 100, is_active: Optional[bool] = None,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Obtiene todos los grupos de ventas con conteos de miembros.
    groups = get_sales_groups(db, skip=skip, limit=limit, is_active=is_active)
    
    # Add member counts to each group
    groups_with_counts = []
    for group in groups:
        group_with_counts = get_sales_group_with_counts(db, group.sales_group_id)
        if group_with_counts:
            groups_with_counts.append(group_with_counts)
    
    return groups_with_counts


""" GET /my-groups - Obtener los grupos de ventas asignados al usuario actual (marketing/seller) """
@router.get("/my-groups", response_model=List[SalesGroupWithMembers])
def read_my_sales_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_seller_user)):
    # Obtiene los grupos de ventas asignados al usuario actual (marketing/seller).
    # Obtener IDs de grupos del usuario
    group_ids = get_user_groups(db, current_user.user_id)
    
    if not group_ids:
        return []
    # Obtener detalles de cada grupo con conteos
    groups = []
    for group_id in group_ids:
        group = get_sales_group_with_counts(db, group_id)
        if group:
            groups.append(group)
    
    return groups

""" GET /{group_id} - Obtener un grupo de ventas por ID con conteos de miembros """
@router.get("/{group_id}", response_model=SalesGroupWithMembers)
def read_sales_group(group_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Obtiene un grupo de ventas por ID con conteos de miembros
    group = get_sales_group_with_counts(db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    return group

""" POST / - Crear un nuevo grupo de ventas """
@router.post("/", response_model=SalesGroup, status_code=status.HTTP_201_CREATED)
def create_new_sales_group(group: SalesGroupCreate, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Crea un nuevo grupo de ventas
    return create_sales_group(db=db, group=group)

""" PUT /{group_id} - Actualizar un grupo de ventas existente """
@router.put("/{group_id}", response_model=SalesGroup)
def update_existing_sales_group(group_id: int, group: SalesGroupUpdate,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Actualiza un grupo de ventas existente
    db_group = update_sales_group(db, group_id=group_id, group=group)
    if not db_group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo de ventas no encontrado")
    return db_group

""" DELETE /{group_id} - Eliminar un grupo de ventas """
@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_sales_group(group_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Elimina un grupo de ventas
    db_group = delete_sales_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    return None


### Marketing Manager Membership Endpoints ###
""" POST /{group_id}/marketing - Asignar marketing manager a un grupo de ventas """
@router.post("/{group_id}/marketing", response_model=GroupMarketingManager, status_code=status.HTTP_201_CREATED)
def assign_marketing_manager(group_id: int, assignment: UserAssignment,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Asigna un marketing manager a un grupo de ventas.
    return assign_marketing_to_group(db=db, group_id=group_id, marketing_id=assignment.user_id)

""" DELETE /{group_id}/marketing/{user_id} - Remover marketing manager de un grupo de ventas """
@router.delete("/{group_id}/marketing/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_marketing_manager(group_id: int, user_id: int,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Remueve un marketing manager de un grupo de ventas.
    success = remove_marketing_from_group(db, group_id=group_id, marketing_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asignacion no encontrada")
    return None

""" GET /{group_id}/marketing - Obtener marketing managers de un grupo con paginacion y busqueda server-side """
@router.get("/{group_id}/marketing", response_model=List[User])
def read_group_marketing_managers(group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo de ventas no encontrado")
    
    return get_group_marketing_managers_paginated(db, group_id=group_id, skip=skip, limit=limit, search=search)

""" GET /{group_id}/available-marketing - Obtener marketing managers que NO estan en el grupo (disponibles) """
@router.get("/{group_id}/available-marketing", response_model=List[User])
def read_available_marketing_managers(group_id: int, skip: int = 0, limit: int = 20, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):    
    # Obtiene marketing managers que NO estan en el grupo (disponibles)
    return get_available_marketing_managers(db, group_id=group_id, skip=skip, limit=limit, search=search )


### Seller Membership Endpoints ###
""" POST /{group_id}/sellers - Asignar seller a un grupo de ventas """
@router.post("/{group_id}/sellers", response_model=GroupSeller, status_code=status.HTTP_201_CREATED)
def assign_seller_to_sales_group(group_id: int, assignment: UserAssignment,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Asigna un seller a un grupo de ventas.
    return assign_seller_to_group(db=db, group_id=group_id, user_id=assignment.user_id)


""" DELETE /{group_id}/sellers/{user_id} - Remover seller de un grupo de ventas """
@router.delete("/{group_id}/sellers/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_seller_from_sales_group(group_id: int, user_id: int,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Remueve un vendedor de un grupo de ventas.
    success = remove_seller_from_group(db, group_id=group_id, user_id=user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Asignacion no encontrada")
    return None


""" GET /{group_id}/sellers - Obtener sellers de un grupo con paginacion y busqueda server-side """
@router.get("/{group_id}/sellers", response_model=List[User])
def read_group_sellers(group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None, 
    db: Session = Depends(get_db), current_user = Depends(get_current_seller_user)):    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Verificar permisos
    if current_user.role != UserRole.admin:
        if not user_belongs_to_group(db, current_user.user_id, group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver los vendedores de este grupo"
            )

    return get_group_sellers_paginated(db, group_id=group_id, skip=skip, limit=limit, search=search)


""" GET /{group_id}/available-sellers - Obtener sellers que NO estan en el grupo (disponibles) """
@router.get("/{group_id}/available-sellers", response_model=List[User])
def read_available_sellers(group_id: int, skip: int = 0, limit: int = 20, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Obtiene sellers que NO estan en el grupo (disponibles)
    return get_available_sellers(db, group_id=group_id, skip=skip, limit=limit, search=search )


#### Combined Members Endpoint ###
class GroupMembers(BaseModel):
    marketing_managers: List[User]
    sellers: List[User]

""" GET /{group_id}/members - Obtener todos los miembros (marketing + sellers) de un grupo de ventas """
@router.get("/{group_id}/members", response_model=GroupMembers)
def read_all_group_members(group_id: int,db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)):
    # Obtiene todos los miembros (marketing + sellers) de un grupo de ventas.
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grupo de ventas no encontrado")
    
    marketing_managers = get_group_marketing_managers(db, group_id=group_id)
    sellers = get_group_sellers(db, group_id=group_id)

    return GroupMembers(marketing_managers=marketing_managers, sellers=sellers)

### Customer Assignment Endpoints ###
""" POST /{group_id}/customers/{customer_id} - Asignar un customer a un grupo de ventas """
@router.post("/{group_id}/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_customer_to_group(group_id: int, customer_id: int,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Asigna un customer a un grupo de ventas
    try:
        assign_customer_to_sales_group(db, group_id=group_id, customer_id=customer_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

""" DELETE /{group_id}/customers/{customer_id} - Remover un customer de un grupo de ventas """
@router.delete("/{group_id}/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_customer_from_group(group_id: int, customer_id: int, db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)):
    success = remove_customer_from_sales_group(db, group_id=group_id, customer_id=customer_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignacion no encontrada"
        )
    return None


""" GET /{group_id}/customers - Obtener customers de un grupo con paginacion y busqueda server-side """
@router.get("/{group_id}/customers")
def read_group_customers(group_id: int, skip: int = 0,limit: int = 100, search: str = None, 
    db: Session = Depends(get_db), current_user = Depends(get_current_seller_user)):
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    # Verificar permisos
    if current_user.role != UserRole.admin and current_user.role != UserRole.marketing:
        if not user_belongs_to_group(db, current_user.user_id, group_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permiso para ver los clientes de este grupo")
    return get_group_customers_paginated(db, group_id=group_id, skip=skip, limit=limit, search=search)

""" GET /{group_id}/available-customers - Obtener customers que NO estan en el grupo (disponibles) """
@router.get("/{group_id}/available-customers")
def read_available_customers(group_id: int, skip: int = 0, limit: int = 20, search: Optional[str] = None,
    db: Session = Depends(get_db), current_user = Depends(get_current_admin_user)):
    # Obtiene customers que NO estan en el grupo (disponibles)
    return get_available_customers(db, group_id=group_id, skip=skip, limit=limit, search=search )
