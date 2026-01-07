"""
CRUD para Sincronización desde DBF

Este módulo maneja todas las operaciones de base de datos para
la sincronización masiva desde archivos DBF.

Usa UPSERT (insert si no existe, update si existe) para mantener
sincronizados los IDs del DBF con PostgreSQL.
"""

from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime

from db.base import PriceList, Product, PriceListItem, Category


# CATEGORÍAS

def guardar_o_actualizar_categoria(
    db: Session,
    name: str,
    description: str = None
) -> Tuple[bool, str]:
    """
    Guarda una nueva categoría si no existe (basado en nombre)
    
    Como category_id es SERIAL (auto-generado), solo verificamos por nombre.
    Si ya existe una categoría con ese nombre, no hacemos nada.
    
    Args:
        db: Sesión de base de datos
        name: Nombre de la categoría
        description: Descripción opcional
        
    Returns:
        Tupla (fue_creada, mensaje_error)
        - fue_creada: True si se creó, False si ya existía
        - mensaje_error: None si todo OK, string con error si falló
    """
    try:
        # Verificar si ya existe una categoría con ese nombre
        categoria_existente = db.query(Category).filter(
            Category.name == name
        ).first()
        
        if categoria_existente:
            # Ya existe, no hacemos nada
            return (False, None)
        
        # No existe, crear nueva
        nueva_categoria = Category(
            name=name,
            description=description
        )
        db.add(nueva_categoria)
        db.flush()  # Para obtener el ID generado si lo necesitamos
        
        return (True, None)
        
    except Exception as e:
        return (False, str(e))


# LISTAS DE PRECIOS

def verificar_si_lista_existe(db: Session, lista_id: int) -> bool:
    """
    Verifica si una lista de precios ya está en la base de datos
    
    Args:
        db: Sesión de base de datos
        lista_id: ID de la lista a verificar
        
    Returns:
        True si existe, False si no
    """
    lista_existente = db.query(PriceList).filter(
        PriceList.price_list_id == lista_id
    ).first()
    
    return lista_existente is not None


def guardar_o_actualizar_lista(
    db: Session,
    lista_id: int,
    nombre: str,
    descripcion: str = None,
    esta_activa: bool = True
) -> Tuple[bool, str]:
    """
    Guarda una nueva lista o actualiza una existente (UPSERT)
    
    Si la lista ya existe (por ID), la actualiza.
    Si no existe, crea una nueva con ese ID.
    
    Args:
        db: Sesión de base de datos
        lista_id: ID de la lista (viene del DBF)
        nombre: Nombre de la lista
        descripcion: Descripción opcional
        esta_activa: Si la lista está activa
        
    Returns:
        Tupla (fue_creada, mensaje_error)
        - fue_creada: True si se creó, False si se actualizó
        - mensaje_error: None si todo bien, str con error si falló
    """
    try:
        # Verificar si ya existe
        ya_existe = verificar_si_lista_existe(db, lista_id)
        
        # Preparar los datos
        datos_lista = {
            "price_list_id": lista_id,
            "list_name": nombre,
            "description": descripcion,
            "is_active": esta_activa
        }
        
        # UPSERT: Insertar o actualizar según exista
        statement = insert(PriceList).values(**datos_lista)
        statement = statement.on_conflict_do_update(
            index_elements=['price_list_id'],
            set_={
                'list_name': statement.excluded.list_name,
                'description': statement.excluded.description,
                'is_active': statement.excluded.is_active
            }
        )
        
        db.execute(statement)
        
        # Retornar si fue creada (True) o actualizada (False)
        fue_creada = not ya_existe
        return fue_creada, None
        
    except Exception as error:
        return False, str(error)


# PRODUCTOS

def verificar_si_producto_existe(db: Session, producto_id: str) -> bool:
    """
    Verifica si un producto ya está en la base de datos
    
    Args:
        db: Sesión de base de datos
        producto_id: ID del producto a verificar (tipo "FAR74")
        
    Returns:
        True si existe, False si no
    """
    producto_existente = db.query(Product).filter(
        Product.product_id == producto_id
    ).first()
    
    return producto_existente is not None


def verificar_si_categoria_existe(db: Session, categoria_id: int) -> bool:
    """
    Verifica si una categoría existe en la base de datos
    
    Args:
        db: Sesión de base de datos
        categoria_id: ID de la categoría
        
    Returns:
        True si existe, False si no
    """
    categoria = db.query(Category).filter(
        Category.category_id == categoria_id
    ).first()
    
    return categoria is not None


def buscar_categoria_por_nombre(
    db: Session,
    nombre: str
) -> Category:
    """
    Busca una categoría por su nombre
    
    Args:
        db: Sesión de base de datos
        nombre: Nombre de la categoría
        
    Returns:
        Objeto Category si se encuentra, None si no
    """
    categoria = db.query(Category).filter(
        Category.name == nombre
    ).first()
    
    return categoria    


def guardar_o_actualizar_producto(
    db: Session,
    producto_id: str,  # Cambiado a str para IDs tipo "FAR74"
    codebar: str,
    nombre: str,
    descripcion: str = None,
    descripcion_2: str = None,  # Nueva: descripción manual (admin)
    unidad_medida: str = None,  # Nueva: "piezas", "cajas", etc.
    precio_base: float = 0.0,
    porcentaje_iva: float = 0.0,
    cantidad_stock: int = 0,
    esta_activo: bool = True,
    category_name: str = None,
    url_imagen: str = None,
    preservar_descripcion_2: bool = False  # Si True, no tocar descripcion_2 existente
) -> Tuple[bool, str]:
    """
    Guarda un nuevo producto o actualiza uno existente (UPSERT)
    
    Si el producto ya existe (por ID), lo actualiza.
    Si no existe, crea uno nuevo con ese ID.
    
    IMPORTANTE sobre descripcion_2:
    --------------------------------
    - Si preservar_descripcion_2=True: NO actualiza descripcion_2 (lo deja como está)
    - Esto es útil al sincronizar desde DBF (que no tiene descripcion_2)
    - Solo actualiza descripcion_2 cuando el admin lo edita manualmente
    
    Args:
        db: Sesión de base de datos
        producto_id: ID del producto tipo "FAR74" (viene del DBF)
        codebar: Código codebar único del producto
        nombre: Nombre del producto
        descripcion: Descripción principal (del DBF)
        descripcion_2: Descripción adicional (editada por admin, ej: receta)
        unidad_medida: Unidad de medida ("piezas", "cajas", "frascos")
        precio_base: Precio sin markup ni IVA
        porcentaje_iva: % de IVA (ej: 16.00)
        cantidad_stock: Cantidad en inventario
        esta_activo: Si el producto está visible
        categoria_id: ID de la categoría (opcional)
        url_imagen: URL de la imagen (opcional, puede ser None)
        preservar_descripcion_2: Si True, mantiene el valor existente de descripcion_2
        
    Returns:
        Tupla (fue_creado, mensaje_error)
        - fue_creado: True si se creó, False si se actualizó
        - mensaje_error: None si todo bien, str con error si falló
    """
    try:
        # Obtener categoria_id desde el nombre si se proporciona
        categoria_id = buscar_categoria_por_nombre(db, category_name).category_id if category_name else None
        
        # Validar categoría si se proporciona
        if categoria_id and not verificar_si_categoria_existe(db, categoria_id):
            return False, f"La categoría ID {categoria_id} no existe"
        
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
            "unidad_medida": unidad_medida,
            "base_price": precio_base,
            "iva_percentage": porcentaje_iva,
            "stock_count": cantidad_stock,
            "is_active": esta_activo,
            "category_id": categoria_id,
            "image_url": url_imagen
        }
        
        # Manejar descripcion_2 con lógica especial
        if preservar_descripcion_2 and ya_existe:
            # Si sincronizan desde DBF, PRESERVAR el valor existente
            # No incluir descripcion_2 en el update
            pass  # No agregar descripcion_2 a datos_producto
        else:
            # Si es creación nueva O si el admin lo está editando
            datos_producto["descripcion_2"] = descripcion_2
        
        # UPSERT: Insertar o actualizar según exista
        statement = insert(Product).values(**datos_producto)
        
        # Definir qué campos actualizar si hay conflicto
        campos_a_actualizar = {
            'codebar': statement.excluded.codebar,
            'name': statement.excluded.name,
            'description': statement.excluded.description,
            'unidad_medida': statement.excluded.unidad_medida,
            'base_price': statement.excluded.base_price,
            'iva_percentage': statement.excluded.iva_percentage,
            'stock_count': statement.excluded.stock_count,
            'is_active': statement.excluded.is_active,
            'category_id': statement.excluded.category_id,
            'image_url': statement.excluded.image_url
        }
        
        # Solo actualizar descripcion_2 si NO estamos preservando
        if not (preservar_descripcion_2 and ya_existe):
            campos_a_actualizar['descripcion_2'] = statement.excluded.descripcion_2
        
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


# RELACIONES PRODUCTO-LISTA (MARKUPS)

def verificar_si_relacion_existe(
    db: Session,
    lista_id: int,
    producto_id: str  # Cambiado a str para match con Product.product_id
) -> bool:
    """
    Verifica si ya existe una relación producto-lista
    
    Args:
        db: Sesión de base de datos
        lista_id: ID de la lista de precios
        producto_id: ID del producto
        
    Returns:
        True si existe, False si no
    """
    relacion_existente = db.query(PriceListItem).filter(
        PriceListItem.price_list_id == lista_id,
        PriceListItem.product_id == producto_id
    ).first()
    
    return relacion_existente is not None


def guardar_o_actualizar_markup(
    db: Session,
    lista_id: int,
    producto_id: str,  # Cambiado a str para match con Product.product_id
    porcentaje_markup: float
) -> Tuple[bool, str]:
    """
    Guarda o actualiza el markup de un producto en una lista (UPSERT)
    
    Si la relación ya existe, actualiza el markup.
    Si no existe, crea la relación nueva.
    
    Args:
        db: Sesión de base de datos
        lista_id: ID de la lista de precios
        producto_id: ID del producto
        porcentaje_markup: % de ganancia (ej: 25.00)
        
    Returns:
        Tupla (fue_creada, mensaje_error)
        - fue_creada: True si se creó, False si se actualizó
        - mensaje_error: None si todo bien, str con error si falló
    """
    try:
        # Verificar si la lista existe
        if not verificar_si_lista_existe(db, lista_id):
            return False, f"La lista de precios ID {lista_id} no existe"
        
        # Verificar si el producto existe
        if not verificar_si_producto_existe(db, producto_id):
            return False, f"El producto ID {producto_id} no existe"
        
        # Verificar si ya existe la relación
        ya_existe = verificar_si_relacion_existe(db, lista_id, producto_id)
        
        # Preparar los datos
        datos_relacion = {
            "price_list_id": lista_id,
            "product_id": producto_id,
            "markup_percentage": porcentaje_markup,
            "updated_at": datetime.now()
        }
        
        # UPSERT: Insertar o actualizar según exista
        statement = insert(PriceListItem).values(**datos_relacion)
        statement = statement.on_conflict_do_update(
            index_elements=['price_list_id', 'product_id'],
            set_={
                'markup_percentage': statement.excluded.markup_percentage,
                'updated_at': statement.excluded.updated_at
            }
        )
        
        db.execute(statement)
        
        # Retornar si fue creada (True) o actualizada (False)
        fue_creada = not ya_existe
        return fue_creada, None
        
    except Exception as error:
        return False, str(error)


# CLIENTES (CUSTOMERS)

def guardar_o_actualizar_cliente(
    db: Session,
    customer_id: int,
    username: str,
    email: str,
    full_name: str,
    password: str,
    # CustomerInfo fields
    business_name: str = None,
    rfc: str = None,
    price_list_id: int = None,
    sales_group_id: int = None,
    address_1: str = None,
    address_2: str = None,
    address_3: str = None
) -> Tuple[bool, str]:
    """
    Guarda o actualiza un cliente completo (Customer + CustomerInfo) - UPSERT
    
    Si el cliente ya existe (por ID), actualiza sus datos.
    Si no existe, crea uno nuevo con ese ID.
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente (viene del DBF)
        username: Nombre de usuario
        email: Email del cliente
        full_name: Nombre completo
        password: Contraseña (se hasheará)
        business_name: Nombre comercial (para CustomerInfo)
        rfc: RFC del cliente (para CustomerInfo)
        price_list_id: ID de lista de precios asignada
        sales_group_id: ID del grupo de ventas
        address_1: Dirección principal
        address_2: Dirección de entrega
        address_3: Dirección de facturación
        
    Returns:
        Tupla (fue_creado, mensaje_error)
        - fue_creado: True si se creó, False si se actualizó
        - mensaje_error: None si todo bien, str con error si falló
    """
    from db.base import Customer, CustomerInfo
    from crud.crud_customer import get_password_hash
    
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
            "is_active": True
        }
        
        # UPSERT Customer
        statement = insert(Customer).values(**datos_customer)
        statement = statement.on_conflict_do_update(
            index_elements=['customer_id'],
            set_={
                'username': statement.excluded.username,
                'email': statement.excluded.email,
                'full_name': statement.excluded.full_name,
                'password_hash': statement.excluded.password_hash,
                'is_active': statement.excluded.is_active
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
                'business_name': statement_info.excluded.business_name,
                'rfc': statement_info.excluded.rfc,
                'price_list_id': statement_info.excluded.price_list_id,
                'sales_group_id': statement_info.excluded.sales_group_id,
                'address_1': statement_info.excluded.address_1,
                'address_2': statement_info.excluded.address_2,
                'address_3': statement_info.excluded.address_3
            }
        )
        
        db.execute(statement_info)
        
        # Retornar si fue creado (True) o actualizado (False)
        fue_creado = not ya_existe
        return fue_creado, None
        
    except Exception as error:
        return False, str(error)
