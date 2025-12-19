"""
CRUD para Clientes (Customers)

Funciones para manejar clientes del e-commerce:
- Operaciones CRUD básicas
- Autenticación
- Búsqueda
- Manejo de CustomerInfo asociado

Los clientes están separados de usuarios internos (admin, marketing, seller).
"""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from core.security import get_password_hash, verify_password
from db.base import Customer
from schemas.customer import CustomerCreate, CustomerUpdate


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """
    Obtiene un cliente por ID con su información comercial
    
    Pre-carga CustomerInfo para evitar queries adicionales.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente
        
    Returns:
        Cliente encontrado con customer_info, o None si no existe
    """
    return db.query(Customer).options(
        joinedload(Customer.customer_info)  # Pre-cargar info comercial
    ).filter(Customer.customer_id == customer_id).first()


def get_customer_by_username(db: Session, username: str) -> Optional[Customer]:
    """
    Obtiene un cliente por username
    
    Útil para autenticación y verificación de duplicados.
    
    Args:
        db: Sesión de base de datos
        username: Nombre de usuario único
        
    Returns:
        Cliente encontrado o None si no existe
    """
    return db.query(Customer).filter(Customer.username == username).first()


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    """
    Obtiene un cliente por email
    
    Args:
        db: Sesión de base de datos
        email: Email del cliente
        
    Returns:
        Cliente encontrado o None si no existe
    """
    return db.query(Customer).filter(Customer.email == email).first()


def get_customers(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None
) -> List[Customer]:
    """
    Obtiene lista de clientes con búsqueda opcional
    
    Pre-carga CustomerInfo para cada cliente.
    
    Args:
        db: Sesión de base de datos
        skip: Número de registros a saltar (paginación)
        limit: Máximo de registros a devolver
        search: Buscar por nombre, username o email
        
    Returns:
        Lista de clientes con su customer_info
    """
    query = db.query(Customer).options(
        joinedload(Customer.customer_info)
    )
    
    # === BÚSQUEDA MÚLTIPLE ===
    # Buscar en nombre, username y email para mejor UX
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


def create_customer(db: Session, customer: CustomerCreate) -> Customer:
    """
    Crea un nuevo cliente
    
    El ID debe ser proporcionado por el admin (para sincronización
    con sistemas externos).
    
    Args:
        db: Sesión de base de datos
        customer: Schema con datos del cliente a crear
        
    Returns:
        Cliente creado
    """
    # Hashear contraseña
    hashed_password = get_password_hash(customer.password)
    
    db_customer = Customer(
        customer_id=customer.customer_id,  # Proporcionado por admin
        username=customer.username,
        email=customer.email,
        password_hash=hashed_password,
        full_name=customer.full_name,
        is_active=True
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


def update_customer(
    db: Session,
    customer_id: int,
    customer: CustomerUpdate
) -> Optional[Customer]:
    """
    Actualiza un cliente existente
    
    Si se proporciona una nueva contraseña, se hashea antes de guardar.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente a actualizar
        customer: Schema con campos a actualizar
        
    Returns:
        Cliente actualizado o None si no existe
    """
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None
    
    update_data = customer.model_dump(exclude_unset=True)
    
    # === HASHEAR NUEVA CONTRASEÑA ===
    if 'password' in update_data and update_data['password']:
        update_data['password_hash'] = get_password_hash(update_data['password'])
        del update_data['password']  # No guardar en texto plano
    
    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_customer, field, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer


def delete_customer(db: Session, customer_id: int) -> Optional[Customer]:
    """
    Elimina un cliente y su información comercial
    
    Elimina en cascada:
    1. CustomerInfo (información comercial)
    2. Customer (usuario)
    
    Esto también elimina pedidos y carrito por CASCADE en la BD.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente a eliminar
        
    Returns:
        Cliente eliminado o None si no existía
    """
    from db.base import CustomerInfo
    
    db_customer = get_customer(db, customer_id)
    if db_customer:
        # Primero eliminar CustomerInfo para evitar errores de FK
        db.query(CustomerInfo).filter(
            CustomerInfo.customer_id == customer_id
        ).delete()
        
        # Luego eliminar el Customer
        db.delete(db_customer)
        db.commit()
    
    return db_customer


def authenticate_customer(
    db: Session,
    username: str,
    password: str
) -> Optional[Customer]:
    """
    Autentica un cliente del e-commerce
    
    Verifica credenciales usando Argon2 para comparación segura.
    
    Args:
        db: Sesión de base de datos
        username: Nombre de usuario
        password: Contraseña en texto plano
        
    Returns:
        Cliente autenticado si las credenciales son válidas, None si no
    """
    customer = get_customer_by_username(db, username)
    if not customer:
        return None
    
    # Verificar contraseña
    if not verify_password(password, customer.password_hash):
        return None
    
    return customer
