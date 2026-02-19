"""
CRUD para Usuarios Internos del Sistema (Users)

Funciones para manejar usuarios internos (admin, marketing, seller):
- Operaciones CRUD basicas
- Autenticacion
- Busqueda y filtrado por rol

NOTA: Los clientes estan en crud_customer.py (tabla separada).

RANGOS DE IDs:
- Sellers (agentes DBF): 1-9000
- Admin/Marketing: 9001+
"""

from typing import List, Optional
from .crud_sales_group import get_user_groups, create_sales_group, assign_seller_to_group
from utils.sales_group_utils import auto_crear_grupo_seller
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from schemas.sales_group import SalesGroupCreate        
from core.security import get_password_hash, verify_password
from db.base import GroupSeller, User, UserRole, SalesGroup
from schemas.user import UserCreate, UserUpdate

""" Obtener un usuario interno por ID """
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()

""" Obtener un usuario interno por username """
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

""" Obtener un usuario interno por email """
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

""" Obtener lista de usuarios internos con filtros opcionales """
def get_users(db: Session, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None, search: Optional[str] = None) -> List[User]:
    query = db.query(User)
    
    # Fltrar por rol
    if role:
        query = query.filter(User.role == role)
    
    # Por nombre o username
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term),
                User.email.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()



""" Crear un nuevo usuario interno """
def create_user(db: Session, user: UserCreate) -> User:
    """
    Crea un nuevo usuario interno
    
    Sistema de rangos de IDs:
    - Sellers (agentes DBF): IDs 1-9000
    - Admin/Marketing: IDs 9001+
    
    Si user_id es proporcionado, valida que no exista y que este en el rango correcto.
    Si no, genera el siguiente ID disponible en el rango del rol.
    """
    # Definir rangos segun rol
    SELLER_ID_MIN = 1
    SELLER_ID_MAX = 9000
    ADMIN_MARKETING_ID_MIN = 9001
    ADMIN_MARKETING_ID_MAX = 99999  # Limite razonable
    
    # Hashear contraseña
    hashed_password = get_password_hash(user.password)
    
    # Determinar el ID a usar
    if user.user_id is not None:
        # ID manual proporcionado - validar que no exista
        existing_user = db.query(User).filter(User.user_id == user.user_id).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya existe un usuario con el ID {user.user_id}"
            )
        
        # Validar que el ID este en el rango correcto segun el rol
        if user.role == UserRole.seller:
            if not (SELLER_ID_MIN <= user.user_id <= SELLER_ID_MAX):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Los sellers deben tener IDs entre {SELLER_ID_MIN} y {SELLER_ID_MAX}. ID proporcionado: {user.user_id}"
                )
        else:  # admin o marketing
            if not (ADMIN_MARKETING_ID_MIN <= user.user_id <= ADMIN_MARKETING_ID_MAX):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Admin/Marketing deben tener IDs desde {ADMIN_MARKETING_ID_MIN} en adelante. ID proporcionado: {user.user_id}"
                )
        
        user_id_to_use = user.user_id
    else:
        # Auto-generar el siguiente ID disponible DENTRO DEL RANGO del rol
        if user.role == UserRole.seller:
            # Buscar max ID en rango de sellers (1-9000)
            max_id = db.query(func.max(User.user_id)).filter(
                and_(
                    User.user_id >= SELLER_ID_MIN,
                    User.user_id <= SELLER_ID_MAX
                )
            ).scalar()
            
            if max_id is None:
                # No hay sellers, empezar en 1
                user_id_to_use = SELLER_ID_MIN
            elif max_id >= SELLER_ID_MAX:
                # Rango de sellers agotado
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Rango de IDs para sellers agotado (max: {SELLER_ID_MAX})"
                )
            else:
                user_id_to_use = max_id + 1
        else:
            # Buscar max ID en rango de admin/marketing (9001+)
            max_id = db.query(func.max(User.user_id)).filter(
                User.user_id >= ADMIN_MARKETING_ID_MIN
            ).scalar()
            
            if max_id is None:
                # No hay admin/marketing, empezar en 9001
                user_id_to_use = ADMIN_MARKETING_ID_MIN
            else:
                user_id_to_use = max_id + 1
    
    db_user = User(
        user_id=user_id_to_use,
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        full_name=user.full_name,
        role=user.role,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Auto-crear grupo para sellers
    if user.role == UserRole.seller:
        auto_crear_grupo_seller(db, db_user)
    
    return db_user

""" Actualizar un usuario interno """
def update_user(db: Session, user_id: int, user: UserUpdate) -> Optional[User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None

    update_data = user.model_dump(exclude_unset=True)

    # Validar unicidad del username
    if "username" in update_data and update_data["username"] != db_user.username:
        existing_user = (
            db.query(User)
            .filter(User.username == update_data["username"], User.user_id != user_id)
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso por otro usuario."
            )

    # Validar unicidad del email
    """if "email" in update_data and update_data["email"] != db_user.email:
        existing_email = (
            db.query(User)
            .filter(User.email == update_data["email"], User.user_id != user_id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso por otro usuario."
            )"""

    # Hashear nueva contraseña
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]

    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


"""" Eliminar un usuario interno (hard delete) """
def delete_user(db: Session, user_id: int) -> Optional[User]:
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

""" Autenticar un usuario interno """
def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:    
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # Verificar contrasenia usando Argon2
    if not verify_password(password, user.password_hash):
        return None
    
    return user

""" Obtener todos los usuarios de un rol especifico """
def get_users_by_role(db: Session, role: UserRole) -> List[User]:
    # Obtiene todos los usuarios de un rol especifico
    return db.query(User).filter(
        User.role == role,
        User.is_active == True
    ).all()


""" Obtener todos los usuarios sellers """
def get_sellers(db: Session) -> List[User]:
    return db.query(User).filter(
        User.role == UserRole.seller,
        User.is_active == True
    ).all()

""" Obtener vendedores asociados a los grupos de un usuario marketing """
def get_sellers_in_marketing_groups(db: Session, marketing_id: int) -> List[User]:
    # Obtener ids de grupos del usuario marketing
    user_groups = get_user_groups(db, marketing_id)
    
    if not user_groups:
        return []
    
    # Filtrar vendedores que esten en esos grupos
    seller_ids = db.query(GroupSeller.seller_id).filter(
        GroupSeller.sales_group_id.in_([group for group in user_groups])
    ).distinct().all()
    
    seller_ids = [sid[0] for sid in seller_ids]
    
    sellers = db.query(User).filter(
        User.user_id.in_(seller_ids),
        User.is_active == True
    ).all()
    
    return sellers