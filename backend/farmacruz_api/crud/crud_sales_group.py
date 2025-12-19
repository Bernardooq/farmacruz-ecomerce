"""
CRUD para Grupos de Ventas (SalesGroups)

Gestión completa de grupos de ventas con relaciones N:M:
- Operaciones CRUD básicas de grupos
- Asignación de marketing managers a grupos (N:M)
- Asignación de sellers a grupos (N:M)
- Asignación de customers a grupos (N:1)
- Paginación y búsqueda de miembros
- Funciones para modales de UI

Estructura de un Sales Group:
- Múltiples marketing managers pueden administrar un grupo
- Múltiples sellers pueden atender un grupo
- Múltiples customers pertenecen a un grupo
- Un user/customer puede estar en varios grupos

Esto permite segmentación de clientes y asignación de equipos.
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
    SalesGroupWithMembers,
    GroupMarketingManagerCreate,
    GroupSellerCreate
)


# ==========================================
# SALES GROUP (Operaciones básicas)
# ==========================================

def create_sales_group(db: Session, group: SalesGroupCreate) -> SalesGroup:
    """
    Crea un nuevo grupo de ventas
    
    Args:
        db: Sesión de base de datos
        group: Datos del grupo a crear
    
    Returns:
        Grupo de ventas creado con ID generado
    """
    db_group = SalesGroup(**group.dict())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group


def get_sales_group(db: Session, group_id: int) -> Optional[SalesGroup]:
    """
    Obtiene un grupo de ventas por ID
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
    
    Returns:
        Grupo encontrado o None si no existe
    """
    return db.query(SalesGroup).filter(
        SalesGroup.sales_group_id == group_id
    ).first()


def get_sales_groups(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    is_active: Optional[bool] = None
) -> List[SalesGroup]:
    """
    Obtiene lista de grupos de ventas con filtros
    
    Args:
        db: Sesión de base de datos
        skip: Registros a saltar (paginación)
        limit: Máximo de registros
        is_active: Filtrar por estado activo (opcional)
    
    Returns:
        Lista de grupos de ventas
    """
    query = db.query(SalesGroup)
    
    if is_active is not None:
        query = query.filter(SalesGroup.is_active == is_active)
    
    return query.offset(skip).limit(limit).all()


def update_sales_group(
    db: Session, 
    group_id: int, 
    group: SalesGroupUpdate
) -> Optional[SalesGroup]:
    """
    Actualiza un grupo de ventas existente
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo a actualizar
        group: Datos actualizados
    
    Returns:
        Grupo actualizado o None si no existe
    """
    db_group = get_sales_group(db, group_id)
    if not db_group:
        return None
    
    update_data = group.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_group, field, value)
    
    db.commit()
    db.refresh(db_group)
    return db_group


def delete_sales_group(db: Session, group_id: int) -> Optional[SalesGroup]:
    """
    Elimina un grupo de ventas
    
    Warning:
        Elimina en CASCADE todas las membresías (managers, sellers).
        Los customers del grupo quedarán sin grupo (sales_group_id = NULL).
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo a eliminar
    
    Returns:
        Grupo eliminado o None si no existía
    """
    db_group = get_sales_group(db, group_id)
    if db_group:
        db.delete(db_group)
        db.commit()
    return db_group


def get_sales_group_with_counts(
    db: Session, 
    group_id: int
) -> Optional[SalesGroupWithMembers]:
    """
    Obtiene un grupo con contadores de miembros
    
    Calcula cuántos marketing managers, sellers y customers
    tiene el grupo sin cargar todos los miembros.
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
    
    Returns:
        SalesGroupWithMembers con contadores o None si no existe
    """
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


# ==========================================
# MARKETING MANAGERS (Asignación N:M)
# ==========================================

def assign_marketing_to_group(
    db: Session, 
    group_id: int, 
    marketing_id: int
) -> GroupMarketingManager:
    """
    Asigna un marketing manager a un grupo
    
    Validaciones:
    - El grupo debe existir y estar activo
    - El usuario debe existir y estar activo
    - El usuario debe tener rol marketing
    - No debe estar ya asignado (evita duplicados)
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        marketing_id: ID del usuario marketing
    
    Returns:
        Relación creada (GroupMarketingManager)
    
    Raises:
        HTTPException 404: Grupo o usuario no encontrado
        HTTPException 400: Usuario no es marketing o ya asignado
    """
    # Validar grupo
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
    
    # Verificar que no esté ya asignado
    existing = db.query(GroupMarketingManager).filter(
        and_(
            GroupMarketingManager.sales_group_id == group_id,
            GroupMarketingManager.marketing_id == marketing_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El marketing manager ya está asignado a este grupo"
        )
    
    # Crear asignación
    assignment = GroupMarketingManager(
        sales_group_id=group_id,
        marketing_id=marketing_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def remove_marketing_from_group(
    db: Session, 
    group_id: int, 
    marketing_id: int
) -> bool:
    """
    Remueve un marketing manager de un grupo
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        marketing_id: ID del usuario marketing
    
    Returns:
        True si se removió, False si no estaba asignado
    """
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


def get_group_marketing_managers(db: Session, group_id: int) -> List[User]:
    """
    Obtiene todos los marketing managers de un grupo
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
    
    Returns:
        Lista de usuarios con rol marketing asignados al grupo
    """
    return db.query(User).join(
        GroupMarketingManager,
        User.user_id == GroupMarketingManager.marketing_id
    ).filter(
        GroupMarketingManager.sales_group_id == group_id
    ).all()


def get_group_marketing_managers_paginated(
    db: Session, 
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[User]:
    """
    Obtiene marketing managers paginados con búsqueda
    
    Útil para modales de UI con muchos miembros.
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o username (opcional)
    
    Returns:
        Lista paginada de marketing managers
    """
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


# ==========================================
# SELLERS (Asignación N:M)
# ==========================================

def assign_seller_to_group(
    db: Session, 
    group_id: int, 
    seller_id: int
) -> GroupSeller:
    """
    Asigna un vendedor a un grupo
    
    Validaciones similares a marketing managers.
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        seller_id: ID del usuario seller
    
    Returns:
        Relación creada (GroupSeller)
    
    Raises:
        HTTPException: Ver assign_marketing_to_group
    """
    # Validar grupo
    group = get_sales_group(db, group_id)
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grupo de ventas no encontrado"
        )
    
    # Validar usuario
    user = db.query(User).filter(User.user_id == seller_id).first()
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
            GroupSeller.seller_id == seller_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El vendedor ya está asignado a este grupo"
        )
    
    # Crear asignación
    assignment = GroupSeller(
        sales_group_id=group_id,
        seller_id=seller_id
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def remove_seller_from_group(
    db: Session, 
    group_id: int, 
    seller_id: int
) -> bool:
    """
    Remueve un vendedor de un grupo
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        seller_id: ID del usuario seller
    
    Returns:
        True si se removió, False si no estaba asignado
    """
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


def get_group_sellers(db: Session, group_id: int) -> List[User]:
    """
    Obtiene todos los vendedores de un grupo
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
    
    Returns:
        Lista de usuarios con rol seller asignados al grupo
    """
    return db.query(User).join(
        GroupSeller,
        User.user_id == GroupSeller.seller_id
    ).filter(
        GroupSeller.sales_group_id == group_id
    ).all()


def get_group_sellers_paginated(
    db: Session, 
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[User]:
    """
    Obtiene vendedores paginados con búsqueda
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o username (opcional)
    
    Returns:
        Lista paginada de vendedores
    """
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


# ==========================================
# CUSTOMERS (Asignación N:1 vía CustomerInfo)
# ==========================================

def get_group_customers(db: Session, group_id: int) -> List[Customer]:
    """
    Obtiene todos los clientes de un grupo
    
    Los customers se asignan a grupos vía CustomerInfo.sales_group_id
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
    
    Returns:
        Lista de clientes en el grupo
    """
    return db.query(Customer).join(
        CustomerInfo,
        Customer.customer_id == CustomerInfo.customer_id
    ).filter(
        CustomerInfo.sales_group_id == group_id
    ).all()


def get_group_customers_paginated(
    db: Session, 
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[Customer]:
    """
    Obtiene clientes paginados con búsqueda
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre, username o email (opcional)
    
    Returns:
        Lista paginada de clientes
    """
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


# ==========================================
# FUNCIONES PARA MODALES (Disponibles)
# ==========================================

def get_available_marketing_managers(
    db: Session,
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[User]:
    """
    Obtiene marketing managers NO asignados al grupo
    
    Útil para modal "Agregar Marketing Manager" mostrando
    solo los que se pueden agregar.
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o username (opcional)
    
    Returns:
        Lista de marketing managers disponibles para agregar
    """
    # Subquery: IDs de marketing YA en el grupo
    assigned_ids = db.query(GroupMarketingManager.marketing_id).filter(
        GroupMarketingManager.sales_group_id == group_id
    ).subquery()
    
    # Query: marketing managers NO en esa subquery
    query = db.query(User).filter(
        User.role == UserRole.marketing,
        User.is_active == True,
        ~User.user_id.in_(assigned_ids)
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


def get_available_sellers(
    db: Session,
    group_id: int,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None
) -> List[User]:
    """
    Obtiene vendedores NO asignados al grupo
    
    Args:
        db: Sesión de base de datos
        group_id: ID del grupo
        skip: Registros a saltar
        limit: Máximo de registros
        search: Buscar por nombre o username (opcional)
    
    Returns:
        Lista de vendedores disponibles para agregar
    """
    # Subquery: IDs de sellers YA en el grupo
    assigned_ids = db.query(GroupSeller.seller_id).filter(
        GroupSeller.sales_group_id == group_id
    ).subquery()
    
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
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()


# ==========================================
# UTILIDADES
# ==========================================

def get_user_groups(db: Session, user_id: int) -> List[int]:
    """
    Obtiene IDs de grupos donde está asignado un usuario
    
    Busca en marketing managers y sellers.
    Útil para verificar permisos.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario interno
    
    Returns:
        Lista de IDs de grupos donde está el usuario
    """
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


def user_can_manage_order(db: Session, user_id: int, customer_id: int, user_role) -> bool:
    """
    Verifica si un usuario puede gestionar pedidos de un cliente
    
    Lógica de permisos:
    - Admin: Puede gestionar todos los pedidos
    - Marketing/Seller: Solo puede gestionar pedidos de clientes en sus grupos
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario interno
        customer_id: ID del cliente del pedido
        user_role: Role del usuario (UserRole enum)
    
    Returns:
        True si el usuario puede gestionar, False caso contrario
    """
    from db.base import UserRole, CustomerInfo
    
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
    
    # Verificar si el usuario está en el grupo del cliente
    user_groups = get_user_groups(db, user_id)
    return customer_info.sales_group_id in user_groups


def user_belongs_to_group(db: Session, user_id: int, group_id: int) -> bool:
    """
    Verifica si un usuario pertenece a un grupo específico
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario interno
        group_id: ID del grupo
    
    Returns:
        True si el usuario está en el grupo, False caso contrario
    """
    user_groups = get_user_groups(db, user_id)
    return group_id in user_groups

