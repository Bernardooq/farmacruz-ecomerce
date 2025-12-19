"""
CRUD para Usuarios Internos del Sistema (Users)

Funciones para manejar usuarios internos (admin, marketing, seller):
- Operaciones CRUD básicas
- Autenticación
- Búsqueda y filtrado por rol

NOTA: Los clientes están en crud_customer.py (tabla separada).
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.security import get_password_hash, verify_password
from db.base import User, UserRole
from schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    """
    Obtiene un usuario interno por ID
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario
        
    Returns:
        Usuario encontrado o None si no existe
    """
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Obtiene un usuario interno por username
    
    Útil para autenticación y verificación de duplicados.
    
    Args:
        db: Sesión de base de datos
        username: Nombre de usuario único
        
    Returns:
        Usuario encontrado o None si no existe
    """
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Obtiene un usuario interno por email
    
    Args:
        db: Sesión de base de datos
        email: Email del usuario
        
    Returns:
        Usuario encontrado o None si no existe
    """
    return db.query(User).filter(User.email == email).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    role: Optional[UserRole] = None,
    search: Optional[str] = None
) -> List[User]:
    """
    Obtiene lista de usuarios internos con filtros opcionales
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Máximo de registros a devolver
        role: Filtrar por rol específico (admin, marketing, seller)
        search: Buscar por nombre completo o username
        
    Returns:
        Lista de usuarios que cumplen con los filtros
    """
    query = db.query(User)
    
    # === FILTRAR POR ROL ===
    if role:
        query = query.filter(User.role == role)
    
    # === BÚSQUEDA POR NOMBRE O USERNAME ===
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_term),
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    """
    Crea un nuevo usuario interno
    
    La contraseña se hashea usando Argon2 antes de guardarla.
    
    Args:
        db: Sesión de base de datos
        user: Schema con datos del usuario a crear
        
    Returns:
        Usuario creado con ID generado
    """
    # Hashear contraseña
    hashed_password = get_password_hash(user.password)
    
    db_user = User(
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
    return db_user


def update_user(
    db: Session,
    user_id: int,
    user: UserUpdate
) -> Optional[User]:
    """
    Actualiza un usuario existente
    
    Si se proporciona una nueva contraseña, se hashea antes de guardar.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario a actualizar
        user: Schema con campos a actualizar
        
    Returns:
        Usuario actualizado o None si no existe
    """
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    
    # === HASHEAR NUEVA CONTRASEÑA ===
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data['password'])
        del update_data['password']  # No guardar contraseña en texto plano
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> Optional[User]:
    """
    Elimina un usuario interno (hard delete)
    
    Warning:
        Esto elimina permanentemente el usuario. Consider

a usar
        is_active=False para soft delete.
    
    Args:
        db: Sesión de base de datos
        user_id: ID del usuario a eliminar
        
    Returns:
        Usuario eliminado o None si no existía
    """
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def authenticate_user(
    db: Session,
    username: str,
    password: str
) -> Optional[User]:
    """
    Autentica un usuario interno
    
    Verifica que el usuario exista y que la contraseña sea correcta
    usando Argon2 para comparación segura.
    
    Args:
        db: Sesión de base de datos
        username: Nombre de usuario
        password: Contraseña en texto plano
        
    Returns:
        Usuario autenticado si las credenciales son válidas, None si no
    """
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # Verificar contraseña usando Argon2
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def get_users_by_role(db: Session, role: UserRole) -> List[User]:
    """
    Obtiene todos los usuarios de un rol específico
    
    Útil para listar todos los sellers, marketing managers, etc.
    
    Args:
        db: Sesión de base de datos
        role: Rol a filtrar (admin, marketing, seller)
        
    Returns:
        Lista de usuarios con ese rol
    """
    return db.query(User).filter(
        User.role == role,
        User.is_active == True
    ).all()
