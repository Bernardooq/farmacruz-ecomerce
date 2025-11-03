from typing import Optional
from sqlalchemy.orm import Session
from core.security import get_password_hash, verify_password
from db.base import User, UserRole
from schemas.user import UserCreate, UserUpdate

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Obtiene un usuario por ID"""
    return db.query(User).filter(User.user_id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Obtiene un usuario por username"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Obtiene un usuario por email"""
    return db.query(User).filter(User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Obtiene lista de usuarios"""
    return db.query(User).offset(skip).limit(limit).all()

def create_user(db: Session, user: UserCreate) -> User:
    """Crea un nuevo usuario"""
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
    """Actualiza un usuario"""
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    
    update_data = user.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int) -> Optional[User]:
    """Elimina un usuario"""
    db_user = get_user(db, user_id)
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """Autentica un usuario"""
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user