"""
CRUD para Clientes (Customers)

Funciones para manejar clientes del e-commerce:
- Operaciones CRUD basicas
- Autenticacion
- Busqueda
- Manejo de CustomerInfo asociado

Los clientes estan separados de usuarios internos (admin, marketing, seller).
"""

from fastapi import HTTPException, status
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from core.security import get_password_hash, verify_password
from db.base import Customer, CustomerInfo
from schemas.customer import CustomerCreate, CustomerUpdate


def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    # Obtiene un cliente por ID con su informacion comercial

    return db.query(Customer).options(
        joinedload(Customer.customer_info)  # Pre-cargar info comercial
    ).filter(Customer.customer_id == customer_id).first()


def get_customer_by_username(db: Session, username: str) -> Optional[Customer]:
    # Obtiene un cliente por username
    return db.query(Customer).filter(Customer.username == username).first()


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    # Obtiene un cliente por email
    return db.query(Customer).filter(Customer.email == email).first()


def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None) -> List[Customer]:
    # Obtiene lista de clientes con busqueda opcional
    
    query = db.query(Customer).options(
        joinedload(Customer.customer_info)
    )
    
    # Buscar en nombre, username y email 
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
    # Crea un nuevo cliente
    # Hashear contrasenia
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


def update_customer(db: Session, customer_id: int, customer: CustomerUpdate) -> Optional[Customer]:
    db_customer = get_customer(db, customer_id)
    if not db_customer:
        return None

    update_data = customer.model_dump(exclude_unset=True)

    # Validar unicidad del username
    if "username" in update_data and update_data["username"] != db_customer.username:
        existing_customer = (
            db.query(Customer)
            .filter(Customer.username == update_data["username"], Customer.customer_id != customer_id)
            .first()
        )
        if existing_customer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El nombre de usuario ya está en uso por otro cliente."
            )

    # Validar unicidad del email
    if "email" in update_data and update_data["email"] != db_customer.email:
        existing_email = (
            db.query(Customer)
            .filter(Customer.email == update_data["email"], Customer.customer_id != customer_id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso por otro cliente."
            )

    # Hashear nueva contraseña
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]

    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    db.commit()
    db.refresh(db_customer)
    return db_customer



def delete_customer(db: Session, customer_id: int) -> Optional[Customer]:
    # Elimina un cliente y su informacion

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


def authenticate_customer(db: Session, username: str,password: str) -> Optional[Customer]:
    # Autentica un cliente del e-commerce

    customer = get_customer_by_username(db, username)
    if not customer:
        return None
    
    # Verificar contrasenia
    if not verify_password(password, customer.password_hash):
        return None
    
    return customer


def get_customer_info(db: Session, customer_id: int) -> Optional[CustomerInfo]:
    # Obtiene la informacion comercial de un cliente    
    return db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()


def buscar_customer_info(db: Session, customer_id: int) -> Optional[CustomerInfo]:
    # Busca la informacion comercial de un cliente
    return db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()


def create_or_update_customer_info(db: Session, customer_info: CustomerInfo, customer_id: int) -> CustomerInfo:
    # Crea o actualiza la informacion comercial de un cliente
    existing_info = buscar_customer_info(db, customer_id)
    
    if existing_info:
        # Actualizar existente y agregar como campo el id
        update_data = customer_info.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field != 'customer_info_id':  # No actualizar el ID
                setattr(existing_info, field, value)
        db.commit()
        return existing_info
    # Crear nuevo CustomerInfo
    new_info = CustomerInfo(
        customer_id=customer_id,
        business_name=customer_info.business_name or '',
        rfc=customer_info.rfc,
        sales_group_id=customer_info.sales_group_id,
        price_list_id=customer_info.price_list_id,
        address_1=customer_info.address_1,
        address_2=customer_info.address_2,
        address_3=customer_info.address_3
    )
    db.add(new_info)
    db.commit()
    db.refresh(new_info)
    return new_info