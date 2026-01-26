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
from datetime import datetime, timezone

from db.base import PriceList, Product, PriceListItem, Category, Customer, CustomerInfo, User
from crud.crud_customer import get_password_hash

from utils.price_utils import calculate_final_price_with_markup
from decimal import Decimal

# CATEGORiAS
""" Guarda una nueva categoria si no existe (basado en nombre) """
def guardar_o_actualizar_categoria(db: Session, name: str, description: str = None, updated_at: datetime = None) -> Tuple[bool, str]:
    try:
        # Verificar si ya existe una categoria con ese nombre
        categoria_existente = db.query(Category).filter(
            Category.name == name
        ).first()
        
        if categoria_existente:
            # Update existente
            categoria_existente.description = description
            categoria_existente.updated_at = updated_at or datetime.now(timezone.utc)
            db.add(categoria_existente)
            db.flush()
            return (False, None)  # False = fue actualizada, no creada
        else:
            # No existe, crear nueva
            nueva_categoria = Category(name=name, description=description, updated_at=updated_at or datetime.now(timezone.utc))
            db.add(nueva_categoria)
            db.flush()  # Para obtener el ID generado si lo necesitamos
            return (True, None)  # True = fue creada
        
    except Exception as e:
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


# PRODUCTOS
""" Verifica si un producto existe """
def verificar_si_producto_existe(db: Session, producto_id: str) -> bool:
    producto_existente = db.query(Product).filter(
        Product.product_id == producto_id
    ).first()
    
    return producto_existente is not None

""" Verifica si una categoria existe """
def verificar_si_categoria_existe(db: Session, categoria_id: int) -> bool:
    # Verifica si una categoria existe en la base de datos
    categoria = db.query(Category).filter(
        Category.category_id == categoria_id
    ).first()
    
    return categoria is not None

""" Busca una categoria por su nombre """
def buscar_categoria_por_nombre(db: Session, nombre: str) -> Category:
    # Busca una categoria por su nombre
    categoria = db.query(Category).filter(
        Category.name == nombre
    ).first()
    
    return categoria    

""" Guarda o actualiza un producto (UPSERT) """
def guardar_o_actualizar_producto(db: Session, producto_id: str, codebar: str, nombre: str, descripcion: str = None, descripcion_2: str = None, unidad_medida: str = None,
    precio_base: float = 0.0, porcentaje_iva: float = 0.0, cantidad_stock: int = 0, esta_activo: bool = True, category_name: str = None,
    url_imagen: str = None, updated_at: datetime = None) -> Tuple[bool, str]:
    # Guarda un nuevo producto o actualiza uno existente (UPSERT)
    try:
        # Obtener categoria_id desde el nombre si se proporciona
        categoria_id = buscar_categoria_por_nombre(db, category_name).category_id if category_name else None
        
        # Validar categoria si se proporciona
        if categoria_id and not verificar_si_categoria_existe(db, categoria_id):
            return False, f"La categoria ID {categoria_id} no existe"
        
        # Verificar si ya existe
        producto_existente = db.query(Product).filter(
            Product.product_id == producto_id
        ).first()
        ya_existe = producto_existente is not None
        
        # Preparar los datos base
        datos_producto = {
            "product_id": producto_id,
            "codebar": codebar,
            "name": nombre,
            "description": descripcion,
            "descripcion_2": descripcion_2,
            "unidad_medida": unidad_medida,
            "base_price": precio_base,
            "iva_percentage": porcentaje_iva,
            "stock_count": cantidad_stock,
            "is_active": esta_activo,
            "category_id": categoria_id,
            "image_url": url_imagen,
            "updated_at": updated_at or datetime.now(timezone.utc)
        }
                
        statement = insert(Product).values(**datos_producto)
        
        # Definir que campos actualizar si hay conflicto
        campos_a_actualizar = {
            'codebar': statement.excluded.codebar,
            'name': statement.excluded.name,
            'description': statement.excluded.description,
            'descripcion_2': statement.excluded.descripcion_2,
            'unidad_medida': statement.excluded.unidad_medida,
            'base_price': statement.excluded.base_price,
            'iva_percentage': statement.excluded.iva_percentage,
            'stock_count': statement.excluded.stock_count,
            'is_active': statement.excluded.is_active,
            'category_id': statement.excluded.category_id,
            'image_url': statement.excluded.image_url,
            'updated_at': statement.excluded.updated_at
        }
        
        
        statement = statement.on_conflict_do_update(
            index_elements=['product_id'],
            set_=campos_a_actualizar
        )
        
        db.execute(statement)
        
        # Retornar si fue creado (True) o actualizado (False)
        fue_creado = not ya_existe
        return fue_creado, None
        
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
        category_names = {p['category_name'] for p in productos if p.get('category_name')}
        categories = db.query(Category).filter(Category.name.in_(category_names)).all()
        cat_map = {c.name: c.category_id for c in categories}
        
        # 2. Obtener IDs de productos existentes para contar
        product_ids = [p['product_id'] for p in productos]
        existing_products = db.query(Product.product_id).filter(
            Product.product_id.in_(product_ids)
        ).all()
        existing_ids = {p.product_id for p in existing_products}
        
        # 3. Preparar datos para el UPSERT
        prod_data_list = []
        for p in productos:
            category_id = cat_map.get(p.get('category_name'))
            
            # Contar creados vs actualizados
            if p['product_id'] in existing_ids:
                actualizados += 1
            else:
                creados += 1
                
            prod_data_list.append({
                "product_id": p['product_id'],
                "codebar": p['codebar'],
                "name": p['name'],
                "description": p.get('description'),
                "descripcion_2": p.get('descripcion_2'),
                "unidad_medida": p.get('unidad_medida'),
                "base_price": p['base_price'],
                "iva_percentage": p.get('iva_percentage', 0.0),
                "stock_count": p.get('stock_count', 0),
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


# RELACIONES PRODUCTO-LISTA (MARKUPS)
""" Verifica si una relacion producto-lista existe """
def verificar_si_relacion_existe(db: Session, lista_id: int, producto_id: str) -> bool:
    # Verifica si ya existe una relacion producto-lista
    relacion_existente = db.query(PriceListItem).filter(
        PriceListItem.price_list_id == lista_id,
        PriceListItem.product_id == producto_id
    ).first()
    
    return relacion_existente is not None

""" Guarda o actualiza el markup de un producto en una lista (UPSERT) """
def guardar_o_actualizar_markup(db: Session, lista_id: int, producto_id: str, porcentaje_markup: float, final_price: float, updated_at: datetime) -> Tuple[bool, str]:
    # Guarda o actualiza el markup de un producto en una lista (UPSERT)
    try:
        # Verificar si la lista existe
        if not verificar_si_lista_existe(db, lista_id):
            return False, f"La lista de precios ID {lista_id} no existe"
        
        # Verificar si el producto existe - SKIP silenciosamente si no existe
        if not verificar_si_producto_existe(db, producto_id):
            return None, None  # None indica "skip" (no es error, solo se omite)
        
        # Verificar si ya existe la relacion
        ya_existe = verificar_si_relacion_existe(db, lista_id, producto_id)

        if final_price is None:
            # Calcular el precio final usando utilidad centralizada
            
            product = db.query(Product).filter(Product.product_id == producto_id).first()
            if product:
                final_price = float(calculate_final_price_with_markup(
                    base_price=Decimal(str(product.base_price or 0)),
                    markup_percentage=Decimal(str(porcentaje_markup)),
                    stored_final_price=None
                ))

        # Preparar los datos
        datos_relacion = {
            "price_list_id": lista_id,
            "product_id": producto_id,
            "markup_percentage": porcentaje_markup,
            "final_price": final_price,
            "updated_at": updated_at
        }
        
        # UPSERT: Insertar o actualizar segun exista
        statement = insert(PriceListItem).values(**datos_relacion)
        statement = statement.on_conflict_do_update(
            index_elements=['price_list_id', 'product_id'],
            set_={
                'markup_percentage': statement.excluded.markup_percentage,
                'final_price': statement.excluded.final_price,
                'updated_at': statement.excluded.updated_at
            }
        )
        
        db.execute(statement)
        
        # Retornar si fue creada (True) o actualizada (False)
        fue_creada = not ya_existe
        return fue_creada, None
        
    except Exception as error:
        return False, str(error)


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
        product_ids = [item['product_id'] for item in items]
        
        # Obtener productos existentes en una sola query
        existing_products = db.query(Product.product_id).filter(
            Product.product_id.in_(product_ids)
        ).all()
        existing_product_ids = {p.product_id for p in existing_products}
        
        # Filtrar solo items con productos válidos
        for item in items:
            if item['product_id'] in existing_product_ids:
                valid_items.append(item)
            else:
                omitidos += 1
        
        if not valid_items:
            return 0, 0, omitidos, []
        
        # Obtener items existentes para saber cuántos son updates vs inserts
        existing_items_query = db.query(PriceListItem.price_list_id, PriceListItem.product_id).filter(
            PriceListItem.price_list_id.in_([item['price_list_id'] for item in valid_items])
        ).all()
        existing_keys = {(item.price_list_id, item.product_id) for item in existing_items_query}
        
        # Contar creados vs actualizados
        for item in valid_items:
            key = (item['price_list_id'], item['product_id'])
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

# CLIENTES (CUSTOMERS)
""" Guarda o actualiza un cliente completo (Customer + CustomerInfo) - UPSERT """
def guardar_o_actualizar_cliente(db: Session, customer_id: int, username: str, email: str, full_name: str, password: str, business_name: str = None, rfc: str = None,
    price_list_id: int = None, sales_group_id: int = None, address_1: str = None, address_2: str = None, address_3: str = None, agent_id: int = None, updated_at: datetime = None) -> Tuple[bool, str]:
    # Guarda o actualiza un cliente completo (Customer + CustomerInfo) - UPSERT
    
    try:
        # Verificar si ya existe
        customer_existente = db.query(Customer).filter(
            Customer.customer_id == customer_id
        ).first()
        ya_existe = customer_existente is not None
        
        # Hashear contraseña
        password_hash = get_password_hash(password)
        
        # Preparar datos del Customer
        datos_customer = {
            "customer_id": customer_id,
            "username": username,
            "email": email,
            "full_name": full_name,
            "password_hash": password_hash,
            "is_active": True,
            "agent_id": agent_id,
            "updated_at": updated_at or datetime.now(timezone.utc)
        }
        
        # UPSERT Customer
        statement = insert(Customer).values(**datos_customer)
        statement = statement.on_conflict_do_update(
            index_elements=['customer_id'],
            set_={
                'email': statement.excluded.email,
                'full_name': statement.excluded.full_name,
                'is_active': statement.excluded.is_active,
                'agent_id': statement.excluded.agent_id,
                'updated_at': statement.excluded.updated_at 
            }
            )
        
        db.execute(statement)
        db.flush()  # Asegurar que el customer existe antes de crear info
        
        # Preparar datos del CustomerInfo
        datos_info = {
            "customer_id": customer_id,
            "business_name": business_name or full_name,  # Usar full_name si no hay business_name
            "rfc": rfc,
            "price_list_id": price_list_id,
            "sales_group_id": sales_group_id,
            "address_1": address_1,
            "address_2": address_2,
            "address_3": address_3
        }
        
        # UPSERT CustomerInfo
        statement_info = insert(CustomerInfo).values(**datos_info)
        statement_info = statement_info.on_conflict_do_update(
            index_elements=['customer_id'],
            set_={
                'rfc': statement_info.excluded.rfc,
                'price_list_id': statement_info.excluded.price_list_id,
                'sales_group_id': statement_info.excluded.sales_group_id,
                'address_1': statement_info.excluded.address_1,
            }
        )
        
        db.execute(statement_info)
        
        # Retornar si fue creado (True) o actualizado (False)
        fue_creado = not ya_existe
        return fue_creado, None
        
    except Exception as error:
        return False, str(error)


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
        customer_ids = [c['customer_id'] for c in customers]
        existing_customers = db.query(Customer.customer_id).filter(
            Customer.customer_id.in_(customer_ids)
        ).all()
        existing_ids = {c.customer_id for c in existing_customers}
        
        # Contar creados vs actualizados
        for customer in customers:
            if customer['customer_id'] in existing_ids:
                actualizados += 1
            else:
                creados += 1
        
        # OPTIMIZACIÓN: Hashear contraseñas unicas solamente (en lugar de todas)
        # Esto reduce 2735 operaciones costosas a solo 1 (si todos usan la misma contraseña)
        password_hashes = {}
        for c in customers:
            password = c['password']
            if password not in password_hashes:
                password_hashes[password] = get_password_hash(password)
        
        # Preparar datos de Customer reutilizando hashes pre-calculados
        customers_data = []
        for c in customers:
            customers_data.append({
                "customer_id": c['customer_id'],
                "username": c['username'],
                "email": c['email'],
                "full_name": c['full_name'],
                "password_hash": password_hashes[c['password']],  # Reutilizar hash
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
                'is_active': stmt_customer.excluded.is_active,
                'agent_id': stmt_customer.excluded.agent_id,
                'updated_at': stmt_customer.excluded.updated_at
            }
        )
        db.execute(stmt_customer)
        db.flush()
        
        # Preparar datos de CustomerInfo
        customers_info_data = []
        for c in customers:
            customers_info_data.append({
                "customer_id": c['customer_id'],
                "business_name": c.get('business_name') or c['full_name'],
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
                'address_2': stmt_info.excluded.address_2,
                'address_3': stmt_info.excluded.address_3,
                'telefono_1': stmt_info.excluded.telefono_1,
                'telefono_2': stmt_info.excluded.telefono_2
            }
        )
        db.execute(stmt_info)
        
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
        user_ids = [s['user_id'] for s in sellers]
        existing_users = db.query(User.user_id).filter(
            User.user_id.in_(user_ids)
        ).all()
        existing_ids = {u.user_id for u in existing_users}
        
        # Contar creados vs actualizados
        for seller in sellers:
            if seller['user_id'] in existing_ids:
                actualizados += 1
            else:
                creados += 1
        
        # OPTIMIZACIÓN: Hashear contraseñas únicas solamente
        password_hashes = {}
        for s in sellers:
            password = s['password']
            if password not in password_hashes:
                password_hashes[password] = get_password_hash(password)
        
        # Preparar datos de User con contraseñas pre-hasheadas y rol seller
        sellers_data = []
        for s in sellers:
            sellers_data.append({
                "user_id": s['user_id'],
                "username": s['username'],
                "email": s['email'],
                "full_name": s['full_name'],
                "password_hash": password_hashes[s['password']],  # Reutilizar hash
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
                'is_active': stmt.excluded.is_active,
                'updated_at': stmt.excluded.updated_at
            }
        )
        db.execute(stmt)
        
        return creados, actualizados, errores
        
    except Exception as error:
        errores.append(f"Error en bulk upsert de vendedores: {str(error)}")
        return 0, 0, errores


def limpiar_items_no_sincronizados(db: Session, last_sync: datetime):
    """
    Desactiva o elimina items que no fueron actualizados desde la fecha de ultima sincronizacion.
    
    - Productos no actualizados: Se desactivan (is_active = False)
    - Listas de precios no actualizadas: Se eliminan
    - Relaciones producto-lista no actualizadas: Se eliminan
    - Clientes no actualizados: Se desactivan (is_active = False)
    - Vendedores no actualizados: Se desactivan (is_active = False)
    """
    # Desactivar productos no actualizados
    db.query(Product).filter(Product.updated_at < last_sync).update({Product.is_active: False})
    
    # Desactivar listas de precios no actualizadas
    db.query(PriceList).filter(PriceList.updated_at < last_sync).delete(synchronize_session=False)
    
    # Eliminar relaciones producto-lista no actualizadas
    db.query(PriceListItem).filter(PriceListItem.updated_at < last_sync).delete(synchronize_session=False)
    
    # Desactivar clientes no actualizados
    db.query(Customer).filter(Customer.updated_at < last_sync).update({Customer.is_active: False})

    # Desactivar vendedores no actualizados
    db.query(User).filter(
        User.role == 'seller',
        User.updated_at < last_sync
    ).update({User.is_active: False})
    