"""
Utilidades para manejo de grupos de ventas

Funciones para gestionar la asignación automática de clientes a grupos de vendedores.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from db.base import User, SalesGroup, GroupSeller, CustomerInfo
from crud.crud_sales_group import create_sales_group, assign_seller_to_group, assign_customer_to_sales_group, remove_customer_from_sales_group




def bulk_ensure_seller_groups(db: Session, seller_ids: List[int]) -> None:
    """
    Asegura que existan grupos y asignaciones para una lista de sellers.
    Crea los grupos faltantes y asigna los sellers a ellos.
    
    Args:
        db: Sesión de base de datos
        seller_ids: Lista de IDs de vendedores
    """
    if not seller_ids:
        return

    # 1. Obtener todos los sellers en una sola query
    sellers = db.query(User).filter(User.user_id.in_(seller_ids)).all()
    if not sellers:
        return
        
    seller_map = {s.user_id: s for s in sellers}
    
    # 2. Crear nombres de grupos esperados
    expected_group_names = [f"Grupo {seller.full_name}" for seller in sellers]
    
    # 3. Obtener grupos existentes en una sola query
    existing_groups = db.query(SalesGroup).filter(
        SalesGroup.group_name.in_(expected_group_names)
    ).all()
    group_name_map = {g.group_name: g for g in existing_groups}
    
    # 4. Crear grupos faltantes en bulk
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
        stmt = insert(SalesGroup).values(groups_to_create)
        db.execute(stmt)
        # db.flush() # flush no es suficiente si queremos que la siguiente query los vea si no hacemos commit? 
        # En la misma transaccion deberia verse.
        
        # Re-fetch newly created groups to get proper ORM objects
        new_group_names = [g['group_name'] for g in groups_to_create]
        new_groups = db.query(SalesGroup).filter(
            SalesGroup.group_name.in_(new_group_names)
        ).all()
        for group in new_groups:
            group_name_map[group.group_name] = group
            
    # 5. Ensure all expected groups are in the map (already done by update)
    
    # 6. Asignar sellers a sus grupos (bulk upsert)
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
        db.commit()


def auto_crear_grupo_seller(db: Session, user: User) -> None:
    """
    Auto-crea un grupo para un seller si no existe.
    Wrapper para bulk_ensure_seller_groups.
    """
    bulk_ensure_seller_groups(db, [user.user_id])


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
    
    # Asignar cliente al grupo
    # Si ya tiene un grupo asignado y es diferente, removerlo primero
    customer_info = db.query(CustomerInfo).filter(CustomerInfo.customer_id == customer_id).first()
    
    if customer_info and customer_info.sales_group_id:
        if customer_info.sales_group_id == group.sales_group_id:
            return # Ya esta en el grupo correcto
            
        # Remover del grupo anterior
        try:
            remove_customer_from_sales_group(db, customer_info.sales_group_id, customer_id)
        except Exception as e:
            print(f"Error removing customer from previous group: {e}")
            
    # Asignar al nuevo grupo (ahora seguro porque no tiene grupo o es el mismo)
    try:
        if not customer_info:
            # Si no existe info, crud_sales_group fallara porque espera que exista
            # Creamos info basica primero
            new_info = CustomerInfo(
                customer_id=customer_id,
                business_name=f"Cliente {customer_id}"
            )
            db.add(new_info)
            db.commit()
            
        assign_customer_to_sales_group(db, group.sales_group_id, customer_id)
    except Exception as e:
        print(f"Error assigning customer to group: {e}")
        # Fallback: actualizacion directa si falla lo anterior
        if customer_info:
            customer_info.sales_group_id = group.sales_group_id
            db.commit()


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
    
    # 2. Asegurar grupos y asignaciones de sellers (Reutilizamos logica)
    bulk_ensure_seller_groups(db, unique_agent_ids)
    
    # 3. Obtener sellers y grupos para mapeo (necesario para asignar clientes)
    sellers = db.query(User).filter(User.user_id.in_(unique_agent_ids)).all()
    seller_map = {s.user_id: s for s in sellers}
    
    expected_group_names = [f"Grupo {seller.full_name}" for seller in sellers]
    existing_groups = db.query(SalesGroup).filter(
        SalesGroup.group_name.in_(expected_group_names)
    ).all()
    group_name_map = {g.group_name: g for g in existing_groups}
    
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
