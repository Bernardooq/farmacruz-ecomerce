"""
CRUD para Sincronizacion desde DBF

Este modulo maneja todas las operaciones de base de datos para
la sincronizacion masiva desde archivos DBF.

Usa UPSERT (insert si no existe, update si existe) para mantener
sincronizados los IDs del DBF con PostgreSQL.
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select, column
from datetime import datetime, timezone

from db.base import PriceList, Product, PriceListItem, Category, Customer, CustomerInfo, User
from crud.crud_customer import get_password_hash

from utils.sales_group_utils import bulk_ensure_seller_groups

# CATEGORiAS
""" Guarda una nueva categoria si no existe (basado en nombre) """
def guardar_o_actualizar_categoria(db: Session, name: str, description: str = None, updated_at: datetime = None) -> Tuple[bool, str]:
    try:
        # Usar UPSERT atomico con ON CONFLICT
        stmt = insert(Category).values(
            name=name,
            description=description,
            updated_at=updated_at or datetime.now(timezone.utc)
        )
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['name'],
            set_={
                'description': stmt.excluded.description,
                'updated_at': stmt.excluded.updated_at
            }
        ).returning(Category.category_id, (column('xmax') == 0).label('is_insert'))
        
        # Ejecutar y obtener resultado
        result = db.execute(stmt).first()
        
        if result:
            fue_creado = result.is_insert
            return (fue_creado, None)
        else:
            # Should not happen
            return (False, "No result from upsert")
        
    except Exception as e:
        # Fallback si xmax no soportado o error de dialecto
        db.rollback()
        return (False, str(e))


# LISTAS DE PRECIOS
""" Verifica si una lista de precios existe """
def verificar_si_lista_existe(db: Session, lista_id: int) -> bool:
    lista_existente = db.query(PriceList).filter(
        PriceList.price_list_id == lista_id
    ).first()
    
    return lista_existente is not None

""" Guarda o actualiza una lista de precios (UPSERT) """
def guardar_o_actualizar_lista(db: Session, lista_id: int, nombre: str, descripcion: str = None, esta_activa: bool = True, updated_at: datetime = None) -> Tuple[bool, str]:
    try:
        # Verificar si ya existe
        ya_existe = verificar_si_lista_existe(db, lista_id)
        
        # Preparar los datos
        datos_lista = {"price_list_id": lista_id, "list_name": nombre, "description": descripcion, "is_active": esta_activa,
            "updated_at": updated_at or datetime.now(timezone.utc)}
        
        # UPSERT: Insertar o actualizar segun exista
        statement = insert(PriceList).values(**datos_lista)
        statement = statement.on_conflict_do_update(
            index_elements=['price_list_id'],
            set_={
                'list_name': statement.excluded.list_name,
                'description': statement.excluded.description,
                'is_active': statement.excluded.is_active,
                'updated_at': statement.excluded.updated_at
            }
        )
        
        db.execute(statement)
        
        # Retornar si fue creada (True) o actualizada (False)
        fue_creada = not ya_existe
        return fue_creada, None
        
    except Exception as error:
        return False, str(error)



""" BULK UPSERT de productos (OPTIMIZADO) """
def bulk_sync_prods(db: Session, productos: List[dict]) -> Tuple[int, int, List[str]]:
    if not productos:
        return 0, 0, []
    
    creados = 0
    actualizados = 0
    errores = []
    
    try:
        # 1. Resolver categorías en bulk
        category_names = {p.get('category_name') for p in productos if p.get('category_name')}
        categories = db.query(Category).filter(Category.name.in_(category_names)).all()
        cat_map = {c.name: c.category_id for c in categories}
        
        # 2. Obtener IDs de productos existentes para contar
        product_ids = [p.get('product_id') for p in productos if p.get('product_id')]
        existing_products = db.query(Product.product_id).filter(
            Product.product_id.in_(product_ids)
        ).all()
        existing_ids = {p.product_id for p in existing_products}
        
        # 3. Preparar datos para el UPSERT
        prod_data_list = []
        for p in productos:
            p_id = p.get('product_id')
            if not p_id: continue

            category_id = cat_map.get(p.get('category_name'))
            
            # Contar creados vs actualizados
            if p_id in existing_ids:
                actualizados += 1
            else:
                creados += 1
                
            prod_data_list.append({
                "product_id": p_id,
                "codebar": p.get('codebar'),
                "name": p.get('name', 'Producto Sincronizado'),
                "description": p.get('description'),
                "descripcion_2": p.get('descripcion_2'),
                "unidad_medida": p.get('unidad_medida'),
                "base_price": float(p.get('base_price', 0.0)),
                "iva_percentage": float(p.get('iva_percentage', 0.0)),
                "stock_count": int(p.get('stock_count', 0)),
                "is_active": p.get('is_active', True),
                "category_id": category_id,
                "image_url": p.get('image_url'),
                "updated_at": p.get('updated_at') or datetime.now(timezone.utc)
            })
            
        # 4. Ejecutar el BULK UPSERT con PostgreSQL ON CONFLICT
        stmt = insert(Product).values(prod_data_list)
        stmt = stmt.on_conflict_do_update(
            index_elements=['product_id'],
            set_={
                'codebar': stmt.excluded.codebar,
                'name': stmt.excluded.name,
                'description': stmt.excluded.description,
                'descripcion_2': stmt.excluded.descripcion_2,
                'unidad_medida': stmt.excluded.unidad_medida,
                'base_price': stmt.excluded.base_price,
                'iva_percentage': stmt.excluded.iva_percentage,
                'stock_count': stmt.excluded.stock_count,
                'is_active': stmt.excluded.is_active,
                'category_id': stmt.excluded.category_id,
                'image_url': stmt.excluded.image_url,
                'updated_at': stmt.excluded.updated_at
            }
        )
        
        db.execute(stmt)
        return creados, actualizados, errores
        
    except Exception as error:
        errores.append(f"Error en bulk UPSERT de productos: {str(error)}")
        return 0, 0, errores


""" BULK UPSERT de items de listas de precios (OPTIMIZADO) """
def bulk_upsert_price_list_items(db: Session, items: List[dict]) -> Tuple[int, int, int, List[str]]:
    if not items:
        return 0, 0, 0, []
    
    creados = 0
    actualizados = 0
    omitidos = 0
    errores = []
    
    try:
        # Filtrar items válidos (productos que existen)
        valid_items = []
        product_ids = [item.get('product_id') for item in items if item.get('product_id')]
        
        # Obtener productos existentes en una sola query
        existing_products = db.query(Product.product_id).filter(
            Product.product_id.in_(product_ids)
        ).all()
        existing_product_ids = {p.product_id for p in existing_products}
        
        # Filtrar solo items con productos válidos
        for item in items:
            p_id = item.get('product_id')
            if p_id in existing_product_ids:
                valid_items.append(item)
            else:
                omitidos += 1
        
        if not valid_items:
            return 0, 0, omitidos, []
        
        # Obtener items existentes para saber cuántos son updates vs inserts
        existing_items_query = db.query(PriceListItem.price_list_id, PriceListItem.product_id).filter(
            PriceListItem.price_list_id.in_([item.get('price_list_id') for item in valid_items if item.get('price_list_id')])
        ).all()
        existing_keys = {(item.price_list_id, item.product_id) for item in existing_items_query}
        
        # Contar creados vs actualizados
        for item in valid_items:
            key = (item.get('price_list_id'), item.get('product_id'))
            if key in existing_keys:
                actualizados += 1
            else:
                creados += 1
        
        # BULK UPSERT usando PostgreSQL's ON CONFLICT
        stmt = insert(PriceListItem).values(valid_items)
        stmt = stmt.on_conflict_do_update(
            index_elements=['price_list_id', 'product_id'],
            set_={
                'markup_percentage': stmt.excluded.markup_percentage,
                'final_price': stmt.excluded.final_price,
                'updated_at': stmt.excluded.updated_at
            }
        )
        
        db.execute(stmt)
        
        return creados, actualizados, omitidos, errores
        
    except Exception as error:
        errores.append(f"Error en bulk upsert: {str(error)}")
        return 0, 0, omitidos, errores


""" BULK UPSERT de clientes"""
def bulk_upsert_customers(db: Session, customers: List[dict]) -> Tuple[int, int, List[str]]:
    """
    Inserta o actualiza multiples clientes en una sola operacion
    """
    if not customers:
        return 0, 0, []
    
    creados = 0
    actualizados = 0
    errores = []
    
    try:
        # Obtener customer_ids existentes para contar creados vs actualizados
        customer_ids = [c.get('customer_id') for c in customers if c.get('customer_id')]
        existing_customers = db.query(Customer.customer_id).filter(
            Customer.customer_id.in_(customer_ids)
        ).all()
        existing_ids = {c.customer_id for c in existing_customers}
        
        # Contar creados vs actualizados
        for customer in customers:
            c_id = customer.get('customer_id')
            if not c_id: continue
            if c_id in existing_ids:
                actualizados += 1
            else:
                creados += 1
        
        # OPTIMIZACIÓN: Hashear contraseñas unicas solamente (en lugar de todas)
        password_hashes = {}
        for c in customers:
            password = c.get('password')
            if password and password not in password_hashes:
                password_hashes[password] = get_password_hash(password)
        
        # Preparar datos de Customer reutilizando hashes pre-calculados
        customers_data = []
        for c in customers:
            c_id = c.get('customer_id')
            if not c_id: continue
            
            pwd_hash = password_hashes.get(c.get('password'))
            username = c.get('username', f"cust_{c_id}")
            
            customers_data.append({
                "customer_id": c_id,
                "username": username,
                "email": c.get('email') or f"{username}@farmacruz.local",
                "full_name": c.get('full_name') or username,
                "password_hash": pwd_hash,  # Reutilizar hash
                "is_active": True,
                "agent_id": c.get('agent_id'),
                "updated_at": c.get('updated_at') or datetime.now(timezone.utc)
            })
        
        # BULK UPSERT Customer
        stmt_customer = insert(Customer).values(customers_data)
        stmt_customer = stmt_customer.on_conflict_do_update(
            index_elements=['customer_id'],
            set_={
                'email': stmt_customer.excluded.email,
                'full_name': stmt_customer.excluded.full_name,
                'agent_id': stmt_customer.excluded.agent_id,
                'updated_at': stmt_customer.excluded.updated_at
            }
        )
        db.execute(stmt_customer)
        db.flush()
        
        # Preparar datos de CustomerInfo
        customers_info_data = []
        for c in customers:
            c_id = c.get('customer_id')
            if not c_id: continue
            
            customers_info_data.append({
                "customer_id": c_id,
                "business_name": c.get('business_name') or c.get('full_name') or f"Cliente {c_id}",
                "rfc": c.get('rfc'),
                "price_list_id": c.get('price_list_id'),
                "address_1": c.get('address_1'),
                "address_2": c.get('address_2'),
                "address_3": c.get('address_3'),
                "telefono_1": c.get('telefono_1'),
                "telefono_2": c.get('telefono_2')
            })
        
        # BULK UPSERT CustomerInfo
        stmt_info = insert(CustomerInfo).values(customers_info_data)
        stmt_info = stmt_info.on_conflict_do_update(
            index_elements=['customer_id'],
            set_={
                'business_name': stmt_info.excluded.business_name,
                'rfc': stmt_info.excluded.rfc,
                'price_list_id': stmt_info.excluded.price_list_id,
                'address_1': stmt_info.excluded.address_1,
                'telefono_1': stmt_info.excluded.telefono_1,
                'telefono_2': stmt_info.excluded.telefono_2
            }
        )
        db.execute(stmt_info)
        
        # Auto-asignar clientes con agent_id a grupos de vendedores (OPTIMIZADO)
        customers_with_agents = [
            {'customer_id': c.get('customer_id'), 'agent_id': c.get('agent_id')}
            for c in customers if c.get('agent_id') and c.get('customer_id')
        ]
        if customers_with_agents:
            from utils.sales_group_utils import bulk_assign_customers_to_agent_groups
            bulk_assign_customers_to_agent_groups(db, customers_with_agents)
        
        return creados, actualizados, errores
        
    except Exception as error:
        errores.append(f"Error en bulk upsert de clientes: {str(error)}")
        return 0, 0, errores


# VENDEDORES (SELLERS)
def bulk_upsert_sellers(db: Session, sellers: List[dict]) -> Tuple[int, int, List[str]]:
    """
    Inserta o actualiza multiples vendedores en una sola operacion
    """
    if not sellers:
        return 0, 0, []
    
    creados = 0
    actualizados = 0
    errores = []
    
    try:
        # Obtener user_ids existentes
        user_ids = [s.get('user_id') for s in sellers if s.get('user_id')]
        existing_users = db.query(User.user_id).filter(
            User.user_id.in_(user_ids)
        ).all()
        existing_ids = {u.user_id for u in existing_users}
        
        # Contar creados vs actualizados
        for seller in sellers:
            s_id = seller.get('user_id')
            if not s_id: continue
            if s_id in existing_ids:
                actualizados += 1
            else:
                creados += 1
        
        # OPTIMIZACIÓN: Hashear contraseñas únicas solamente
        password_hashes = {}
        for s in sellers:
            password = s.get('password')
            if password and password not in password_hashes:
                password_hashes[password] = get_password_hash(password)
        
        # Preparar datos de User con contraseñas pre-hasheadas y rol seller
        sellers_data = []
        for s in sellers:
            s_id = s.get('user_id')
            if not s_id: continue
            
            pwd_hash = password_hashes.get(s.get('password'))
            username = s.get('username', f"user_{s_id}")
            
            sellers_data.append({
                "user_id": s_id,
                "username": username,
                "email": s.get('email') or f"{username}@farmacruz.local",
                "full_name": s.get('full_name') or username,
                "password_hash": pwd_hash,  # Reutilizar hash
                "role": 'seller',
                "is_active": s.get('is_active', True),
                "updated_at": s.get('updated_at') or datetime.now(timezone.utc)
            })
        
        # BULK UPSERT User
        stmt = insert(User).values(sellers_data)
        stmt = stmt.on_conflict_do_update(
            index_elements=['user_id'],
            set_={
                'email': stmt.excluded.email,
                'full_name': stmt.excluded.full_name,
                'updated_at': stmt.excluded.updated_at
            }
        )
        db.execute(stmt)
        
        # Asegurar que existan grupos para estos sellers
        bulk_ensure_seller_groups(db, user_ids)
        
        return creados, actualizados, errores
        
    except Exception as error:
        errores.append(f"Error en bulk upsert de vendedores: {str(error)}")
        return 0, 0, errores


def limpiar_items_no_sincronizados(db: Session, last_sync: datetime, force: bool = False):
    """
    Desactiva o elimina productos, categorias, listas y items que no fueron 
    actualizados desde la fecha de ultima sincronizacion.
    
    SEGURIDAD: 
    1. Restamos 20 minutos adicionales a last_sync para evitar race conditions 
       con hilos de procesamiento en segundo plano (async).
    2. Si el cleanup desactivaría más del 20% del catálogo, abortamos por seguridad
       a menos que se pase force=True.
    """
    from datetime import timedelta
    # Aplicar buffer de seguridad de 20 minutos
    last_sync_buffered = last_sync - timedelta(minutes=20)
    
    # 1. SEGURIDAD: Contar cuántos se desactivarían
    total_products = db.query(Product).count()
    to_deactivate = db.query(Product).filter(
        Product.updated_at < last_sync_buffered,
        Product.is_active == True
    ).count()
    
    if total_products > 100 and to_deactivate > (total_products * 0.20) and not force:
        msg = (
            f"SAFETY ABORT: Se intentaron desactivar {to_deactivate} productos de un total de {total_products} "
            f"({(to_deactivate/total_products)*100:.1f}%). El límite de seguridad es 20%. "
            f"Esto ocurre si solo sincronizaste una parte pequeña del catálogo. "
            f"Usa force=True en la petición para confirmar que deseas desactivar el resto."
        )
        print(msg)
        return False
        
    # Proceder con la desactivación/eliminación
    # Desactivar productos no actualizados
    db.query(Product).filter(Product.updated_at < last_sync_buffered).update({Product.is_active: False})
    
    # Eliminar categorias no actualizadas SOLO si no tienen productos asociados
    subq = select(Product.category_id).distinct()
    db.query(Category).filter(
        Category.updated_at < last_sync_buffered,
        ~Category.category_id.in_(subq)
    ).delete(synchronize_session=False)
    
    # Eliminar relaciones producto-lista no actualizadas
    db.query(PriceListItem).filter(PriceListItem.updated_at < last_sync_buffered).delete(synchronize_session=False)

    # Desactivar listas de precios no actualizadas
    db.query(PriceList).filter(PriceList.updated_at < last_sync_buffered).update({PriceList.is_active: False})
    
    return True