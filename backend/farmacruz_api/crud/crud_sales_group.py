"""
CRUD para Grupos de Ventas (SalesGroups)

Gestion completa de grupos de ventas con relaciones N:M:
- Operaciones CRUD basicas de grupos
- Asignacion de marketing managers a grupos (N:M)
- Asignacion de sellers a grupos (N:M)
- Asignacion de customers a grupos (N:1)
- Paginacion y busqueda de miembros
- Funciones para modales de UI

Estructura de un Sales Group:
- Multiples marketing managers pueden administrar un grupo
- Multiples sellers pueden atender un grupo
- Multiples customers pertenecen a un grupo
- Un user/customer puede estar en varios grupos

Esto permite segmentacion de clientes y asignacion de equipos.
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_, and_
from fastapi import HTTPException, status

from db.base import (
    SalesGroup, GroupMarketingManager, GroupSeller,
    User, UserRole, Customer, CustomerInfo
)
from schemas.sales_group import (
    SalesGroupCreate, 
    SalesGroupUpdate,
    SalesGroupWithMembers
)

### FUNCIONES CRUD BASICAS DE GRUPOS ###
""" Crea un nuevo grupo de ventas """
def create_sales_group(db: Session, group: SalesGroupCreate) -> SalesGroup:
    db_group = SalesGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

""" Obtiene un grupo de ventas por ID """
def get_sales_group(db: Session, group_id: int) -> Optional[SalesGroup]:
    return db.query(SalesGroup).filter(
        SalesGroup.sales_group_id == group_id
    ).first()

""" Obtiene lista de grupos de ventas con filtros """
def get_sales_groups(db: Session, skip: int = 0, limit: int = 100, is_active: Optional[bool] = None) -> List[SalesGroup]:
    query = db.query(SalesGroup)
    
    if is_active is not None:
        query = query.filter(SalesGroup.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()

""" Actualiza un grupo de ventas existente """
def update_sales_group(db: Session, group_id: int, group: SalesGroupUpdate) -> Optional[SalesGroup]:
    db_group = get_sales_group(db, group_id)
    if not db_group:
        return None
    
    update_data = group.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group

""" Elimina un grupo de ventas """
def delete_sales_group(db: Session, group_id: int) -> Optional[SalesGroup]:
    db_group = get_sales_group(db, group_id)
    if db_group:
        db.delete(db_group)
        db.commit()
    return db_group

""" Obtiene un grupo con contadores de miembros """
def get_sales_group_with_counts(db: Session, group_id: int) -> Optional[SalesGroupWithMembers]:
    db_group = get_sales_group(db, group_id)
    if not db_group:
        return None
    
    # Contar marketing managers
    marketing_count = db.query(func.count(GroupMarketingManager.group_marketing_id)).filter(
        GroupMarketingManager.sales_group_id == group_id
    ).scalar()
    
    # Contar sellers
    seller_count = db.query(func.count(GroupSeller.group_seller_id)).filter(
        GroupSeller.sales_group_id == group_id
    ).scalar()
    
    # Contar customers
    customer_count = db.query(func.count(CustomerInfo.customer_info_id)).filter(
        CustomerInfo.sales_group_id == group_id
    ).scalar()
    
    return SalesGroupWithMembers(
        **db_group.__dict__,
        marketing_count=marketing_count or 0,
        seller_count=seller_count or 0,
        customer_count=customer_count or 0
    )

### FUNCIONES PARA MARKETING MANAGERS ###
""" Asigna un marketing manager a un grupo (N:M) """
def assign_marketing_to_group(db: Session, group_id: int, marketing_id: int) -> GroupMarketingManager:
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Validar usuario
    user = db.query(User).filter(User.user_id == marketing_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar rol
    if user.role != UserRole.marketing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no es un marketing manager"
        )
    
    # Verificar que no este ya asignado
    existing = db.query(GroupMarketingManager).filter(
        and_(
            GroupMarketingManager.sales_group_id == group_id,
            GroupMarketingManager.marketing_id == marketing_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El marketing manager ya esta asignado a este grupo"
        )
    
    # Crear asignacion
    assignment = GroupMarketingManager(
        sales_group_id=group_id,
        marketing_id=marketing_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

""" Remueve un marketing manager de un grupo """
def remove_marketing_from_group(db: Session, group_id: int, marketing_id: int) -> bool:
    assignment = db.query(GroupMarketingManager).filter(
        and_(
            GroupMarketingManager.sales_group_id == group_id,
            GroupMarketingManager.marketing_id == marketing_id
        )
    ).first()
    
    if assignment:
        db.delete(assignment)
        db.commit()
        return True
    return False

""" Obtiene todos los marketing managers de un grupo """
def get_group_marketing_managers(db: Session, group_id: int) -> List[User]:   
    return db.query(User).join(
        GroupMarketingManager,
        User.user_id == GroupMarketingManager.marketing_id
    ).filter(
        GroupMarketingManager.sales_group_id == group_id
    ).all()

""" Obtiene marketing managers paginados con busqueda """
def get_group_marketing_managers_paginated(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[User]:    
    query = db.query(User).join(
        GroupMarketingManager,
        User.user_id == GroupMarketingManager.marketing_id
    ).filter(
        GroupMarketingManager.sales_group_id == group_id
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

### FUNCIONES PARA SELLERS ###
""" Asigna un vendedor a un grupo (N:M) """
def assign_seller_to_group(db: Session, group_id: int, user_id: int) -> GroupSeller:
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Validar usuario
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Validar rol
    if user.role != UserRole.seller:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario no es un vendedor"
        )
    
    # Verificar duplicado
    existing = db.query(GroupSeller).filter(
        and_(
            GroupSeller.sales_group_id == group_id,
            GroupSeller.seller_id == user_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor ya esta asignado a este grupo"
        )
    
    # Crear asignacion
    assignment = GroupSeller(
        sales_group_id=group_id,
        seller_id=user_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment

""" Remueve un vendedor de un grupo """
def remove_seller_from_group(db: Session, group_id: int, seller_id: int) -> bool:
    assignment = db.query(GroupSeller).filter(
        and_(
            GroupSeller.sales_group_id == group_id,
            GroupSeller.seller_id == seller_id
        )
    ).first()
    
    if assignment:
        db.delete(assignment)
        db.commit()
        return True
    return False

""" Obtiene todos los vendedores de un grupo """
def get_group_sellers(db: Session, group_id: int) -> List[User]:
    return db.query(User).join(
        GroupSeller,
        User.user_id == GroupSeller.seller_id
    ).filter(
        GroupSeller.sales_group_id == group_id
    ).all()

""" Obtiene vendedores paginados con busqueda """
def get_group_sellers_paginated(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[User]:
    query = db.query(User).join(
        GroupSeller,
        User.user_id == GroupSeller.seller_id
    ).filter(
        GroupSeller.sales_group_id == group_id
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

### FUNCIONES PARA CUSTOMERS ###
""" Asigna un cliente a un grupo (N:1) """
def assign_customer_to_sales_group(db: Session, group_id: int, customer_id: int) -> CustomerInfo:
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )

    # Validar customer
    customer = db.query(CustomerInfo).filter(CustomerInfo.customer_id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer no encontrado"
        )

    # Verificar si ya tiene un grupo asignado (N:1)
    if customer.sales_group_id is not None:
        if customer.sales_group_id == group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El cliente ya esta en este grupo"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El cliente ya pertenece a otro grupo (ID: {customer.sales_group_id})"
            )

    # Actualizar asignacion
    customer.sales_group_id = group_id
    db.commit()
    db.refresh(customer)
    return customer

""" Obtiene todos los clientes de un grupo """
def get_group_customers(db: Session, group_id: int) -> List[Customer]:
    return db.query(Customer).join(
        CustomerInfo,
        Customer.customer_id == CustomerInfo.customer_id
    ).filter(
        CustomerInfo.sales_group_id == group_id
    ).all()

""" Obtiene clientes paginados con busqueda """
def get_group_customers_paginated(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[Customer]:    
    query = db.query(Customer).join(
        CustomerInfo,
        Customer.customer_id == CustomerInfo.customer_id
    ).filter(
        CustomerInfo.sales_group_id == group_id
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.username.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

""" Remueve un customer de un grupo """
def remove_customer_from_sales_group(db: Session, group_id: int, customer_id: int) -> bool:
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id,
        CustomerInfo.sales_group_id == group_id
    ).first()
    
    if not customer_info:
        return False
    
    customer_info.sales_group_id = None
    db.commit()
    return True


# FUNCIONES PARA MODALES
""" Obtiene marketing managers NO asignados al grupo """
def get_available_marketing_managers(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[User]:
    # Verificar que el grupo existe
    group = get_sales_group(db, group_id)
    if not group: raise HTTPException( status_code=status.HTTP_404_NOT_FOUND, detail="Grupo de ventas no encontrado")
    # Obtener IDs de marketing ya en el grupo
    current_members = get_group_marketing_managers(db, group_id)
    current_member_ids = [m.user_id for m in current_members]
    # Query de todos los marketing
    query = db.query(User).filter(User.role == UserRole.marketing)
    # Excluir los que ya estan en el grupo
    if current_member_ids:
        query = query.filter(~User.user_id.in_(current_member_ids))
    # Aplicar busqueda
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_pattern)) |
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern))
        )
    # Paginacion
    return query.order_by(User.full_name).offset(skip).limit(limit).all()

""" Obtiene vendedores NO asignados al grupo """
def get_available_sellers(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[User]:
    # Subquery: IDs de sellers YA en el grupo
    assigned_ids = db.query(GroupSeller.seller_id).filter(
        GroupSeller.sales_group_id == group_id
    ).scalar_subquery()
    
    # Query: sellers NO en esa subquery
    query = db.query(User).filter(
        User.role == UserRole.seller,
        User.is_active == True,
        ~User.user_id.in_(assigned_ids)
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    return query.order_by(User.full_name).offset(skip).limit(limit).all()

def get_available_customers(db: Session, group_id: int, skip: int = 0, limit: int = 50, search: Optional[str] = None) -> List[Customer]:
    # Obtener IDs de customers que ya tienen un grupo asignado (CUALQUIER GRUPO)
    # Ya que un cliente es N:1 con grupos, si tiene un sales_group_id, no esta disponible.
    assigned_ids = db.query(CustomerInfo.customer_id).filter(
        CustomerInfo.sales_group_id.isnot(None)
    ).scalar_subquery()
    
    # Query: customers NO en esa subquery (es decir, sin grupo asignado)
    query = db.query(Customer).filter(
        ~Customer.customer_id.in_(assigned_ids)
    )
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(search_term),
                Customer.username.ilike(search_term),
                Customer.email.ilike(search_term)
            )
        )
    return query.order_by(Customer.full_name).offset(skip).limit(limit).all()


# UTILIDADES
""" Obtiene IDs de grupos donde esta asignado un usuario """
def get_user_groups(db: Session, user_id: int) -> List[int]:
    group_ids = []
    
    # Buscar en marketing managers
    marketing_groups = db.query(GroupMarketingManager.sales_group_id).filter(
        GroupMarketingManager.marketing_id == user_id
    ).all()
    group_ids.extend([g[0] for g in marketing_groups])
    
    # Buscar en sellers
    seller_groups = db.query(GroupSeller.sales_group_id).filter(
        GroupSeller.seller_id == user_id
    ).all()
    group_ids.extend([g[0] for g in seller_groups])
    
    # Eliminar duplicados y retornar
    return list(set(group_ids))

""" Verifica si un usuario puede gestionar pedidos de un cliente """
def user_can_manage_order(db: Session, user_id: int, customer_id: int, user_role) -> bool:        
    # Admin puede gestionar todo
    if user_role == UserRole.admin:
        return True
    
    # Obtener grupo del cliente
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.sales_group_id:
        # Cliente sin grupo - solo admin puede gestionar
        return False
    
    # Verificar si el usuario esta en el grupo del cliente
    user_groups = get_user_groups(db, user_id)
    return customer_info.sales_group_id in user_groups

""" Verifica si un usuario pertenece a un grupo especifico """
def user_belongs_to_group(db: Session, user_id: int, group_id: int) -> bool:    
    user_groups = get_user_groups(db, user_id)
    return group_id in user_groups