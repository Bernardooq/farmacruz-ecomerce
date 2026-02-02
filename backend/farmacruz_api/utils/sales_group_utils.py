"""
Utilidades para manejo de grupos de ventas

Funciones para gestionar la asignación automática de clientes a grupos de vendedores.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from db.base import User, SalesGroup, GroupSeller, CustomerInfo
from crud.crud_sales_group import create_sales_group, assign_seller_to_group, assign_customer_to_sales_group
from schemas.sales_group import SalesGroupCreate


def assign_customer_to_agent_group(db: Session, customer_id: int, agent_id: int) -> None:
    """
    Asigna un cliente al grupo del seller (agent).
    Si el agente no tiene grupo, busca/crea uno llamado 'Grupo {seller.full_name}'.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente a asignar
        agent_id: ID del vendedor/agente
    """
    # Obtener seller
    seller = db.query(User).filter(User.user_id == agent_id).first()
    if not seller:
        return  # Agent no existe, no hacer nada
    
    # Buscar grupo del seller por nombre
    group_name = f"Grupo {seller.full_name}"
    group = db.query(SalesGroup).filter(SalesGroup.group_name == group_name).first()
    
    if not group:
        # Crear grupo
        group = create_sales_group(db, SalesGroupCreate(
            group_name=group_name,
            description=f"Grupo automático para el vendedor {seller.username}",
            is_active=True
        ))
        
        # Asignar seller al grupo
        try:
            assign_seller_to_group(db, group.sales_group_id, seller.user_id)
        except:
            pass  # Ya está asignado
    
    # Asignar cliente al grupo (actualiza sales_group_id en CustomerInfo)
    try:
        assign_customer_to_sales_group(db, group.sales_group_id, customer_id)
    except:
        pass  # Ya está asignado o no tiene CustomerInfo


def bulk_assign_customers_to_agent_groups(db: Session, customer_agent_pairs: List[dict]) -> None:
    """
    Asigna múltiples clientes a grupos de sellers de forma optimizada (BULK).
    
    Args:
        db: Sesión de base de datos
        customer_agent_pairs: Lista de dicts con {'customer_id': int, 'agent_id': int}
    """
    if not customer_agent_pairs:
        return
    
    # 1. Obtener todos los agent_ids únicos
    unique_agent_ids = list({pair['agent_id'] for pair in customer_agent_pairs if pair.get('agent_id')})
    if not unique_agent_ids:
        return
    
    # 2. Obtener todos los sellers en una sola query
    sellers = db.query(User).filter(User.user_id.in_(unique_agent_ids)).all()
    seller_map = {s.user_id: s for s in sellers}
    
    # 3. Crear nombres de grupos esperados
    expected_group_names = [f"Grupo {seller.full_name}" for seller in sellers]
    
    # 4. Obtener grupos existentes en una sola query
    existing_groups = db.query(SalesGroup).filter(
        SalesGroup.group_name.in_(expected_group_names)
    ).all()
    group_name_map = {g.group_name: g for g in existing_groups}
    
    # 5. Crear grupos faltantes en bulk
    groups_to_create = []
    for seller in sellers:
        group_name = f"Grupo {seller.full_name}"
        if group_name not in group_name_map:
            groups_to_create.append({
                'group_name': group_name,
                'description': f"Grupo automático para el vendedor {seller.username}",
                'is_active': True
            })
    
    if groups_to_create:
        stmt = insert(SalesGroup).values(groups_to_create).returning(SalesGroup)
        result = db.execute(stmt)
        new_groups = result.fetchall()
        for group in new_groups:
            group_name_map[group.group_name] = group
    
    db.flush()
    
    # 6. Re-fetch groups to get proper IDs
    existing_groups = db.query(SalesGroup).filter(
        SalesGroup.group_name.in_(expected_group_names)
    ).all()
    group_name_map = {g.group_name: g for g in existing_groups}
    
    # 7. Asignar sellers a sus grupos (bulk upsert)
    seller_assignments = []
    for seller in sellers:
        group_name = f"Grupo {seller.full_name}"
        group = group_name_map.get(group_name)
        if group:
            seller_assignments.append({
                'sales_group_id': group.sales_group_id,
                'seller_id': seller.user_id
            })
    
    if seller_assignments:
        stmt = insert(GroupSeller).values(seller_assignments)
        stmt = stmt.on_conflict_do_nothing(index_elements=['sales_group_id', 'seller_id'])
        db.execute(stmt)
    
    # 8. Asignar clientes a grupos (bulk update de CustomerInfo)
    for pair in customer_agent_pairs:
        agent_id = pair.get('agent_id')
        if not agent_id:
            continue
        
        seller = seller_map.get(agent_id)
        if not seller:
            continue
        
        group_name = f"Grupo {seller.full_name}"
        group = group_name_map.get(group_name)
        if group:
            # Update CustomerInfo con el sales_group_id
            db.query(CustomerInfo).filter(
                CustomerInfo.customer_id == pair['customer_id']
            ).update({'sales_group_id': group.sales_group_id})
