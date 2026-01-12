"""
CRUD para Usuarios Internos del Sistema (Users)

Funciones para manejar usuarios internos (admin, marketing, seller):
- Operaciones CRUD basicas
- Autenticacion
- Busqueda y filtrado por rol

NOTA: Los clientes estan en crud_customer.py (tabla separada).
"""

from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.security import get_password_hash, verify_password
from db.base import User, UserRole
from schemas.user import UserCreate, UserUpdate


def get_user(db: Session, user_id: int) -> Optional[User]:
    # Obtiene un usuario interno por ID
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    # Obtiene un usuario interno por username
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    # Obtiene un usuario interno por email
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100, role: Optional[UserRole] = None, search: Optional[str] = None) -> List[User]:
    # Obtiene lista de usuarios internos con filtros opcionales
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
                User.username.ilike(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user: UserCreate) -> User:
    # Crea un nuevo usuario interno
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
    if "email" in update_data and update_data["email"] != db_user.email:
        existing_email = (
            db.query(User)
            .filter(User.email == update_data["email"], User.user_id != user_id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso por otro usuario."
            )

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



def delete_user(db: Session, user_id: int) -> Optional[User]:
    # Elimina un usuario interno (hard delete)
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    # Autentica un usuario interno
    
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    # Verificar contrasenia usando Argon2
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def get_users_by_role(db: Session, role: UserRole) -> List[User]:
    # Obtiene todos los usuarios de un rol especifico
    return db.query(User).filter(
        User.role == role,
        User.is_active == True
    ).all()
