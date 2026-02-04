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
from sqlalchemy import or_, func

from core.security import get_password_hash, verify_password
from db.base import Customer, CustomerInfo
from schemas.customer import CustomerCreate, CustomerUpdate
from utils.sales_group_utils import assign_customer_to_agent_group


"""Obtiene un cliente por ID con su informacion comercial"""
def get_customer(db: Session, customer_id: int) -> Optional[Customer]:
    return db.query(Customer).options(
        joinedload(Customer.customer_info)  # Pre-cargar info comercial
    ).filter(Customer.customer_id == customer_id).first()

"""Obtiene un cliente por username"""
def get_customer_by_username(db: Session, username: str) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.username == username).first()

"""Obtiene un cliente por email"""
def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.email == email).first()

"""Obtiene lista de clientes con busqueda opcional"""
def get_customers(db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None, 
                  user_id: Optional[int] = None, user_role = None) -> List[Customer]:    
    from db.base import UserRole
    
    query = db.query(Customer).options(
        joinedload(Customer.customer_info)
    )
    
    # Si es Marketing, filtrar por grupos
    if user_role and user_role == UserRole.marketing and user_id:
        from crud.crud_sales_group import get_user_groups
        
        user_group_ids = get_user_groups(db, user_id)
        
        if not user_group_ids:
            # Si no tiene grupos asignados, no puede ver clientes
            return []
        
        # Filtrar clientes que pertenecen a los grupos del usuario
        query = query.join(
            CustomerInfo,
            Customer.customer_id == CustomerInfo.customer_id
        ).filter(
            CustomerInfo.sales_group_id.in_(user_group_ids)
        )
    
    # Buscar en nombre, username y email todo tolower
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                func.lower(Customer.full_name).like(search_term),
                func.lower(Customer.username).like(search_term),
                func.lower(Customer.email).like(search_term)
            )
        )
    
    return query.offset(skip).limit(limit).all()

"""Crea un nuevo cliente"""
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
        agent_id=customer.agent_id,  # Asignar agente
        is_active=True
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    
    # Auto-asignar al grupo del agente si tiene agent_id
    if customer.agent_id:
        assign_customer_to_agent_group(db, db_customer.customer_id, customer.agent_id)
    
    return db_customer

"""Actualiza un cliente existente"""
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
    """if "email" in update_data and update_data["email"] != db_customer.email:
        existing_email = (
            db.query(Customer)
            .filter(Customer.email == update_data["email"], Customer.customer_id != customer_id)
            .first()
        )
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso por otro cliente."
            )"""

    # Hashear nueva contraseña
    if "password" in update_data and update_data["password"]:
        update_data["password_hash"] = get_password_hash(update_data["password"])
        del update_data["password"]

    # Actualizar campos
    for field, value in update_data.items():
        setattr(db_customer, field, value)

    db.commit()
    db.refresh(db_customer)
    
    # Auto-asignar al grupo del agente si cambió el agent_id
    if "agent_id" in update_data and update_data["agent_id"]:
        assign_customer_to_agent_group(db, customer_id, update_data["agent_id"])
    
    return db_customer


"""Elimina un cliente y su informacion"""
def delete_customer(db: Session, customer_id: int) -> Optional[Customer]:    
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

"""Autentica un cliente del e-commerce"""
def authenticate_customer(db: Session, username: str,password: str) -> Optional[Customer]:
    customer = get_customer_by_username(db, username)
    if not customer:
        return None
    # Verificar contrasenia
    if not verify_password(password, customer.password_hash):
        return None
    
    return customer

"""Obtiene la informacion comercial de un cliente"""
def get_customer_info(db: Session, customer_id: int) -> Optional[CustomerInfo]:
    return db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()

"""Busca la informacion comercial de un cliente"""
def create_or_update_customer_info(db: Session, customer_info: CustomerInfo, customer_id: int) -> CustomerInfo:
    existing_info = get_customer_info(db, customer_id)
    
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
        address_3=customer_info.address_3,
        telefono_1=customer_info.telefono_1,
        telefono_2=customer_info.telefono_2
    )
    db.add(new_info)
    db.commit()
    db.refresh(new_info)
    return new_info