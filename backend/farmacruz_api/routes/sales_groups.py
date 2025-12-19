"""
Routes para Grupos de Ventas (Sales Groups)

Gestión completa de grupos de ventas con relaciones N:M.

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
- Un grupo puede tener múltiples marketing managers
- Un grupo puede tener múltiples sellers
- Un marketing/seller puede estar en múltiples grupos
- Un customer pertenece a UN solo grupo (N:1)
"""


from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user, get_current_seller_user
from schemas.sales_group import (
    SalesGroup,
    SalesGroupCreate,
    SalesGroupUpdate,
    SalesGroupWithMembers,
    GroupMarketingManager,
    GroupSeller
)
from schemas.user import User
from crud.crud_sales_group import (
    create_sales_group,
    get_sales_group,
    get_sales_groups,
    update_sales_group,
    delete_sales_group,
    get_sales_group_with_counts,
    assign_marketing_to_group,
    assign_seller_to_group,
    remove_marketing_from_group,
    remove_seller_from_group,
    get_group_marketing_managers,
    get_group_sellers
)

router = APIRouter()


# ==========================================
# Sales Group CRUD Endpoints
# ==========================================

@router.get("/", response_model=List[SalesGroupWithMembers])
def read_sales_groups(
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene lista de grupos de ventas con paginación, filtros y conteos de miembros.
    Solo administradores.
    """
    groups = get_sales_groups(db, skip=skip, limit=limit, is_active=is_active)
    
    # Add member counts to each group
    groups_with_counts = []
    for group in groups:
        group_with_counts = get_sales_group_with_counts(db, group.sales_group_id)
        if group_with_counts:
            groups_with_counts.append(group_with_counts)
    
    return groups_with_counts


# ==========================================
# My Groups Endpoint (for marketing/sellers)
# ==========================================

@router.get("/my-groups", response_model=List[SalesGroupWithMembers])
def read_my_sales_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_seller_user)
):
    """
    Obtiene los grupos de ventas del usuario actual.
    Marketing ve grupos donde es marketing manager.
    Sellers ven grupos donde son sellers.
    """
    from crud.crud_sales_group import get_user_groups, get_sales_group_with_counts
    
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


@router.get("/{group_id}", response_model=SalesGroupWithMembers)
def read_sales_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene un grupo de ventas con conteos de miembros.
    Solo administradores.
    """
    group = get_sales_group_with_counts(db, group_id=group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    return group


@router.post("/", response_model=SalesGroup, status_code=status.HTTP_201_CREATED)
def create_new_sales_group(
    group: SalesGroupCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Crea un nuevo grupo de ventas.
    Solo administradores.
    """
    return create_sales_group(db=db, group=group)


@router.put("/{group_id}", response_model=SalesGroup)
def update_existing_sales_group(
    group_id: int,
    group: SalesGroupUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Actualiza un grupo de ventas existente.
    Solo administradores.
    """
    db_group = update_sales_group(db, group_id=group_id, group=group)
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    return db_group


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_sales_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Elimina un grupo de ventas (cascade delete de memberships).
    Solo administradores.
    """
    db_group = delete_sales_group(db, group_id=group_id)
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    return None


# ==========================================
# Marketing Manager Membership Endpoints
# ==========================================

class AssignUserRequest(BaseModel):
    user_id: int


@router.post("/{group_id}/marketing", response_model=GroupMarketingManager, status_code=status.HTTP_201_CREATED)
def assign_marketing_manager(
    group_id: int,
    request: AssignUserRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Asigna un marketing manager a un grupo de ventas.
    Solo administradores.
    """
    return assign_marketing_to_group(
        db=db,
        group_id=group_id,
        marketing_id=request.user_id
    )


@router.delete("/{group_id}/marketing/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_marketing_manager(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Remueve un marketing manager de un grupo de ventas.
    Solo administradores.
    """
    success = remove_marketing_from_group(db, group_id=group_id, marketing_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    return None


@router.get("/{group_id}/marketing", response_model=List[User])
def read_group_marketing_managers(
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene marketing managers de un grupo con paginación y búsqueda server-side.
    Solo administradores.
    """
    from crud.crud_sales_group import get_group_marketing_managers_paginated
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    return get_group_marketing_managers_paginated(
        db, 
        group_id=group_id,
        skip=skip,
        limit=limit,
        search=search
    )


@router.get("/{group_id}/available-marketing", response_model=List[User])
def read_available_marketing_managers(
    group_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene marketing managers que NO están en el grupo (disponibles).
    Con paginación y búsqueda server-side.
    """
    from db.base import User as UserModel, UserRole
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Obtener IDs de marketing ya en el grupo
    from crud.crud_sales_group import get_group_marketing_managers
    current_members = get_group_marketing_managers(db, group_id)
    current_member_ids = [m.user_id for m in current_members]
    
    # Query de todos los marketing
    query = db.query(UserModel).filter(UserModel.role == UserRole.marketing)
    
    # Excluir los que ya están en el grupo
    if current_member_ids:
        query = query.filter(~UserModel.user_id.in_(current_member_ids))
    
    # Aplicar búsqueda
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserModel.full_name.ilike(search_pattern)) |
            (UserModel.username.ilike(search_pattern)) |
            (UserModel.email.ilike(search_pattern))
        )
    
    # Paginación
    return query.order_by(UserModel.full_name).offset(skip).limit(limit).all()


# ==========================================
# Seller Membership Endpoints
# ==========================================

@router.post("/{group_id}/sellers", response_model=GroupSeller, status_code=status.HTTP_201_CREATED)
def assign_seller_to_sales_group(
    group_id: int,
    request: AssignUserRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Asigna un vendedor a un grupo de ventas.
    Solo administradores.
    """
    return assign_seller_to_group(
        db=db,
        group_id=group_id,
        seller_id=request.user_id
    )


@router.delete("/{group_id}/sellers/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_seller_from_sales_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Remueve un vendedor de un grupo de ventas.
    Solo administradores.
    """
    success = remove_seller_from_group(db, group_id=group_id, seller_id=user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    return None



@router.get("/{group_id}/sellers", response_model=List[User])
def read_group_sellers(
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_seller_user)
):
    """
    Obtiene vendedores de un grupo con paginación y búsqueda server-side.
    Marketing/Sellers pueden ver vendedores de sus grupos.
    Administradores pueden ver cualquier grupo.
    """
    from db.base import UserRole
    from crud.crud_sales_group import user_belongs_to_group, get_group_sellers_paginated
    
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
    
    return get_group_sellers_paginated(
        db,
        group_id=group_id,
        skip=skip,
        limit=limit,
        search=search
    )


@router.get("/{group_id}/available-sellers", response_model=List[User])
def read_available_sellers(
    group_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene sellers que NO están en el grupo (disponibles).
    Con paginación y búsqueda server-side.
    """
    from db.base import User as UserModel, UserRole
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Obtener IDs de sellers ya en el grupo
    from crud.crud_sales_group import get_group_sellers
    current_members = get_group_sellers(db, group_id)
    current_member_ids = [s.user_id for s in current_members]
    
    # Query de todos los sellers
    query = db.query(UserModel).filter(UserModel.role == UserRole.seller)
    
    # Excluir los que ya están en el grupo
    if current_member_ids:
        query = query.filter(~UserModel.user_id.in_(current_member_ids))
    
    # Aplicar búsqueda
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserModel.full_name.ilike(search_pattern)) |
            (UserModel.username.ilike(search_pattern)) |
            (UserModel.email.ilike(search_pattern))
        )
    
    # Paginación
    return query.order_by(UserModel.full_name).offset(skip).limit(limit).all()



# ==========================================
# Combined Members Endpoint
# ==========================================

class GroupMembers(BaseModel):
    marketing_managers: List[User]
    sellers: List[User]


@router.get("/{group_id}/members", response_model=GroupMembers)
def read_all_group_members(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene todos los miembros de un grupo (marketing managers y sellers).
    Solo administradores.
    """
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    marketing_managers = get_group_marketing_managers(db, group_id=group_id)
    sellers = get_group_sellers(db, group_id=group_id)
    
    return GroupMembers(
        marketing_managers=marketing_managers,
        sellers=sellers
    )


# ==========================================
# Customer Assignment Endpoints
# ==========================================

@router.post("/{group_id}/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def assign_customer_to_group(
    group_id: int,
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Asigna un cliente a un grupo de ventas.
    Solo administradores.
    """
    from db.base import Customer, CustomerInfo
    from sqlalchemy import func as sqlalchemy_func
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Verificar que el customer existe
    customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado"
        )
    
    # Obtener o crear CustomerInfo
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info:
        # Crear CustomerInfo si no existe
        # Auto-generate customer_info_id
        max_id = db.query(sqlalchemy_func.max(CustomerInfo.customer_info_id)).scalar()
        new_customer_info_id = (max_id or 0) + 1
        
        customer_info = CustomerInfo(
            customer_info_id=new_customer_info_id,
            customer_id=customer_id,
            business_name=customer.full_name or customer.username,
            sales_group_id=group_id
        )
        db.add(customer_info)
    else:
        # Actualizar el grupo del cliente
        customer_info.sales_group_id = group_id
    
    db.commit()
    
    return None


@router.delete("/{group_id}/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_customer_from_group(
    group_id: int,
    customer_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Remueve un cliente de un grupo de ventas.
    Solo administradores.
    """
    from db.base import CustomerInfo
    
    # Obtener CustomerInfo
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id,
        CustomerInfo.sales_group_id == group_id
    ).first()
    
    if not customer_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cliente no encontrado en este grupo"
        )
    
    
    # Remover del grupo (establecer a NULL)
    customer_info.sales_group_id = None
    db.commit()
    
    return None




@router.get("/{group_id}/customers")
def read_group_customers(
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    search: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_seller_user)
):
    """
    Obtiene los clientes de un grupo con paginación y búsqueda.
    Marketing/Sellers solo pueden ver clientes de sus grupos.
    Administradores pueden ver cualquier grupo.
    """
    from db.base import CustomerInfo, Customer, UserRole
    from crud.crud_sales_group import user_belongs_to_group
    
    # Verificar permisos
    if current_user.role != UserRole.admin:
        if not user_belongs_to_group(db, current_user.user_id, group_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene permiso para ver los clientes de este grupo"
            )
    
    # Obtener clientes del grupo (de la tabla Customer, NO User)
    query = db.query(Customer).join(
        CustomerInfo,
        Customer.customer_id == CustomerInfo.customer_id
    ).filter(
        CustomerInfo.sales_group_id == group_id
    )
    
    # Aplicar búsqueda si se proporciona
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(search_pattern)) |
            (Customer.username.ilike(search_pattern)) |
            (Customer.email.ilike(search_pattern))
        )
    
    # Aplicar paginación
    customers = query.offset(skip).limit(limit).all()
    
    return customers


@router.get("/{group_id}/available-customers")
def read_available_customers(
    group_id: int,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Obtiene clientes que NO están en este grupo (disponibles).
    Incluye clientes sin grupo y clientes en otros grupos.
    Con paginación y búsqueda server-side.
    """
    from db.base import CustomerInfo, Customer
    
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Query: Clientes que NO tienen este grupo
    # Incluye: sin customer_info, con customer_info.sales_group_id NULL, o con otro grupo
    query = db.query(Customer).outerjoin(
        CustomerInfo,
        Customer.customer_id == CustomerInfo.customer_id
    ).filter(
        # Sin customer_info O con sales_group_id NULL O con otro grupo
        (CustomerInfo.customer_id.is_(None)) |
        (CustomerInfo.sales_group_id.is_(None)) |
        (CustomerInfo.sales_group_id != group_id)
    )
    
    # Aplicar búsqueda
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Customer.full_name.ilike(search_pattern)) |
            (Customer.username.ilike(search_pattern)) |
            (Customer.email.ilike(search_pattern))
        )
    
    # Paginación
    return query.order_by(Customer.full_name).offset(skip).limit(limit).all()
