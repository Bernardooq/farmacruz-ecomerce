"""
Rutas para Sincronización desde Archivos DBF

Este módulo maneja la sincronización masiva de datos desde archivos DBF
del sistema legacy de FarmaCruz hacia la base de datos PostgreSQL.

¿Qué hace este sistema?
-----------------------
Permite mantener sincronizados los datos entre:
- Sistema viejo (archivos DBF de Visual FoxPro)
- Sistema nuevo (PostgreSQL)

¿Cómo funciona?
--------------
1. Recibes datos del DBF en lotes (batches)
2. Para cada registro:
   - Si ya EXISTE (por ID) → Se ACTUALIZA
   - Si NO existe → Se CREA nuevo
3. Retornas un resumen: cuántos creados, actualizados, errores

ORDEN IMPORTANTE:
----------------
Debes sincronizar en este orden (porque hay dependencias):
1. PRIMERO → Listas de precios (son contenedores)
2. SEGUNDO → Productos (dependen de categorías)
3. TERCERO → Relaciones producto-lista (dependen de ambos anteriores)

Permisos:
--------
Solo administradores pueden usar estos endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from db.base import User
from schemas.price_list import PriceListCreate, PriceListItemCreate
from schemas.product import ProductCreate
from schemas.customer import CustomerSync  # Nuevo import
from crud import crud_sync


# Crear router con prefijo /sync
router = APIRouter(prefix="/sync", tags=["sync-dbf"])


# SCHEMAS DE RESPUESTA

class ResultadoSincronizacion(BaseModel):
    """
    Resultado de una operación de sincronización
    
    Te dice exactamente qué pasó con tus datos:
    - Cuántos se recibieron
    - Cuántos se crearon (nuevos)
    - Cuántos se actualizaron (ya existían)
    - Cuántos tuvieron errores
    - Detalle de los errores
    """
    total_recibidos: int  # Total de registros que enviaste
    creados: int  # Registros nuevos que se crearon
    actualizados: int  # Registros que ya existían y se actualizaron
    errores: int  # Registros que tuvieron algún problema
    detalle_errores: List[str] = []  # Descripción de cada error


# ENDPOINT: SINCRONIZAR LISTAS DE PRECIOS

@router.post("/price-lists", response_model=ResultadoSincronizacion)
def sincronizar_listas_de_precios(
    listas: List[PriceListCreate],
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza listas de precios desde el DBF (en lote)
    
    ¿Qué hace?
    ----------
    - Recibe listas de precios del archivo LISTAS.DBF
    - Para cada lista:
      * Si el ID ya existe → ACTUALIZA nombre, descripción, estado
      * Si NO existe → CREA nueva lista con ese ID
    
    ¿Por qué es importante?
    ----------------------
    Las listas son "contenedores" que agrupan productos con sus precios.
    Debes sincronizar las listas ANTES que los productos porque los
    productos necesitan que la lista ya exista.
    
    Ejemplo de uso:
    --------------
    POST /sync/price-lists
    [
        {
            "price_list_id": 1,
            "list_name": "Farmacias Premium",
            "description": "Para farmacias grandes",
            "is_active": true
        }
    ]
    
    Respuesta:
    ---------
    {
        "total_recibidos": 1,
        "creados": 1,
        "actualizados": 0,
        "errores": 0
    }
    """
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(
        total_recibidos=len(listas),
        creados=0,
        actualizados=0,
        errores=0,
        detalle_errores=[]
    )
    
    # Procesar cada lista una por una
    for lista in listas:
        try:
            # Intentar guardar o actualizar la lista
            fue_creada, mensaje_error = crud_sync.guardar_o_actualizar_lista(
                db=db,
                lista_id=lista.price_list_id,
                nombre=lista.list_name,
                descripcion=lista.description,
                esta_activa=lista.is_active if lista.is_active is not None else True
            )
            
            # Si hubo error, registrarlo
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Lista ID {lista.price_list_id}: {mensaje_error}"
                )
            # Si todo bien, contar si fue creada o actualizada
            elif fue_creada:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            # Capturar cualquier error que no hayamos previsto
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Lista ID {lista.price_list_id}: Error inesperado - {str(error_inesperado)}"
            )
    
    # Guardar todos los cambios en la base de datos
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


# ENDPOINT: SINCRONIZAR CATEGORÍAS

class CategorySync(BaseModel):
    """Schema simple para sincronizar categorías"""
    name: str
    description: str = None

@router.post("/categories", response_model=ResultadoSincronizacion)
def sincronizar_categorias(
    categorias: List[CategorySync],
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza categorías desde el DBF (en lote)
    
    ¿Qué hace?
    ----------
    - Recibe categorías únicas extraídas del campo CSE_PROD
    - Para cada categoría:
      * Si el nombre ya existe → NO hace nada (skip)
      * Si NO existe → CREA nueva categoría
    
    Ejemplo de uso:
    --------------
    POST /sync/categories
    [
        {
            "name": "Medicamentos",
            "description": "Productos médicos"
        }
    ]
    """
    resultado = ResultadoSincronizacion(
        total_recibidos=len(categorias),
        creados=0,
        actualizados=0,
        errores=0,
        detalle_errores=[]
    )
    
    for categoria in categorias:
        try:
            fue_creada, mensaje_error = crud_sync.guardar_o_actualizar_categoria(
                db=db,
                name=categoria.name,
                description=categoria.description
            )
            
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Categoría '{categoria.name}': {mensaje_error}"
                )
            elif fue_creada:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Categoría '{categoria.name}': Error inesperado - {str(error_inesperado)}"
            )
    
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


# ENDPOINT: SINCRONIZAR PRODUCTOS

@router.post("/products", response_model=ResultadoSincronizacion)
def sincronizar_productos(
    productos: List[ProductCreate],
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza productos del catálogo desde el DBF (en lote)
    
    ¿Qué hace?
    ----------
    - Recibe productos del archivo PRODUCTOS.DBF
    - Para cada producto:
      * Si el ID ya existe → ACTUALIZA todos sus datos
      * Si NO existe → CREA nuevo producto con ese ID
    
    ¿Qué valida?
    -----------
    - Que las categorías existan (si el producto tiene una)
    - Que los precios sean válidos (≥ 0)
    - Que el IVA esté entre 0 y 100
    
    Ejemplo de uso:
    --------------
    POST /sync/products
    [
        {
            "product_id": 1,
            "sku": "PARACET500",
            "name": "Paracetamol 500mg",
            "base_price": 25.50,
            "iva_percentage": 16.00,
            "stock_count": 100,
            "is_active": true,
            "category_id": 1
        }
    ]
    
    Importante:
    ----------
    - Haber creado las categorias ANTES
    - Los IDs de productos son permanentes (no cambiarlos)
    - El SKU debe ser unico
    """
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(
        total_recibidos=len(productos),
        creados=0,
        actualizados=0,
        errores=0,
        detalle_errores=[]
    )
    
    # Procesar cada producto uno por uno
    for producto in productos:
        try:
            # Intentar guardar o actualizar el producto
            fue_creado, mensaje_error = crud_sync.guardar_o_actualizar_producto(
                db=db,
                producto_id=producto.product_id,
                sku=producto.sku,
                nombre=producto.name,
                descripcion=producto.description,
                descripcion_2=producto.descripcion_2,  # Nueva campo
                unidad_medida=producto.unidad_medida,  # Nuevo campo
                precio_base=float(producto.base_price),
                porcentaje_iva=float(producto.iva_percentage) if producto.iva_percentage else 0.0,
                cantidad_stock=producto.stock_count if producto.stock_count else 0,
                esta_activo=producto.is_active if producto.is_active is not None else True,
                categoria_id=producto.category_id,
                url_imagen=producto.image_url,
                preservar_descripcion_2=True  # IMPORTANTE: NO tocar descripcion_2 al sincronizar DBF
            )
            
            # Si hubo error, registrarlo
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Producto ID {producto.product_id} (SKU: {producto.sku}): {mensaje_error}"
                )
            # Si todo bien, contar si fue creado o actualizado
            elif fue_creado:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            # Capturar cualquier error que no hayamos previsto
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Producto ID {producto.product_id} (SKU: {producto.sku}): "
                f"Error inesperado - {str(error_inesperado)}"
            )
    
    # Guardar todos los cambios en la base de datos
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


# ENDPOINT: SINCRONIZAR MARKUPS (PRODUCTO-LISTA)

class LoteDeMarkups(BaseModel):
    """
    Lote de markups para una lista de precios específica
    
    Agrupa todos los productos de UNA lista con sus porcentajes
    de ganancia (markup).
    """
    price_list_id: int  # ID de la lista de precios
    items: List[PriceListItemCreate]  # Productos con sus markups


@router.post("/price-list-items", response_model=ResultadoSincronizacion)
def sincronizar_markups(
    lote: LoteDeMarkups,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza relaciones producto-lista con sus markups (en lote)
    
    ¿Qué hace?
    ----------
    - Recibe relaciones del archivo PRECIOLIS.DBF
    - Define qué productos están en qué lista
    - Asigna el % de ganancia (markup) de cada producto
    - Para cada relación:
      * Si ya existe → ACTUALIZA el markup
      * Si NO existe → CREA la relación
    
    ¿Qué es el markup?
    -----------------
    Es el porcentaje de ganancia que se agrega al precio base.
    Ejemplo: Si el producto cuesta $100 y el markup es 25%,
    el precio con markup será $125 (antes de IVA).
    
    ¿Por qué por lotes?
    ------------------
    Es más eficiente enviar todos los productos de UNA lista
    en una sola petición, en lugar de uno por uno.
    
    Ejemplo de uso:
    --------------
    POST /sync/price-list-items
    {
        "price_list_id": 1,
        "items": [
            {"product_id": 1, "markup_percentage": 25.00},
            {"product_id": 2, "markup_percentage": 30.00}
        ]
    }
    
    Validaciones:
    ------------
    - La lista de precios debe existir
    - Cada producto debe existir
    - El markup debe ser ≥ 0
    
    Nota importante:
    ---------------
    Debes sincronizar PRIMERO las listas y productos,
    DESPUÉS las relaciones.
    """
    # Verificar que la lista de precios exista
    if not crud_sync.verificar_si_lista_existe(db, lote.price_list_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"La lista de precios ID {lote.price_list_id} no existe. "
                   f"Debes sincronizar las listas ANTES que los markups."
        )
    
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(
        total_recibidos=len(lote.items),
        creados=0,
        actualizados=0,
        errores=0,
        detalle_errores=[]
    )
    
    # Procesar cada relación producto-lista una por una
    for item in lote.items:
        try:
            # Intentar guardar o actualizar el markup
            fue_creada, mensaje_error = crud_sync.guardar_o_actualizar_markup(
                db=db,
                lista_id=lote.price_list_id,
                producto_id=item.product_id,
                porcentaje_markup=float(item.markup_percentage)
            )
            
            # Si hubo error, registrarlo
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Lista {lote.price_list_id} - Producto {item.product_id}: {mensaje_error}"
                )
            # Si todo bien, contar si fue creada o actualizada
            elif fue_creada:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            # Capturar cualquier error que no hayamos previsto
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Lista {lote.price_list_id} - Producto {item.product_id}: "
                f"Error inesperado - {str(error_inesperado)}"
            )
    
    # Guardar todos los cambios en la base de datos
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado



# ENDPOINT: SINCRONIZAR CLIENTES

@router.post("/customers", response_model=ResultadoSincronizacion)
def sincronizar_clientes(
    clientes: List[CustomerSync],  # Cambiado a CustomerSync
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Sincroniza clientes del archivo CLIENTES.DBF (en lote)
    
    ¿Qué hace?
    ----------
    - Recibe clientes del archivo CLIENTES.DBF
    - Para cada cliente:
      * Si el ID ya existe → ACTUALIZA todos sus datos (Customer + CustomerInfo)
      * Si NO existe → CREA nuevo cliente con ese ID
    
    Ejemplo de uso:
    --------------
    POST /sync/customers
    [
        {
            "customer_id": 1,
            "username": "juan_perez",
            "email": "juan@example.com",
            "full_name": "Juan Pérez",
            "password": "FarmaCruz2024!",
            "business_name": "Farmacia Pérez",
            "rfc": "PEPJ800101XXX",
            "price_list_id": 1,
            "address_1": "Calle Principal 123"
        }
    ]
    
    Respuesta:
    ---------
    {
        "total_recibidos": 1,
        "creados": 1,
        "actualizados": 0,
        "errores": 0,
        "detalle_errores": []
    }
    """
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(
        total_recibidos=len(clientes),
        creados=0,
        actualizados=0,
        errores=0,
        detalle_errores=[]
    )
    
    # Procesar cada cliente uno por uno
    for cliente in clientes:
        try:
            # Intentar guardar o actualizar el cliente (Customer + CustomerInfo)
            # Ahora es mucho más simple con CustomerSync
            fue_creado, mensaje_error = crud_sync.guardar_o_actualizar_cliente(
                db=db,
                customer_id=cliente.customer_id,
                username=cliente.username,
                email=cliente.email or f"{cliente.username}@farmacruz.com",
                full_name=cliente.full_name or cliente.username,
                password=cliente.password,
                # CustomerInfo fields - ahora vienen directamente del schema
                business_name=cliente.business_name,
                rfc=cliente.rfc,
                price_list_id=cliente.price_list_id,
                sales_group_id=cliente.sales_group_id,
                address_1=cliente.address_1,
                address_2=cliente.address_2,
                address_3=cliente.address_3
            )
            
            # Si hubo error, registrarlo
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Cliente ID {cliente.customer_id} ({cliente.username}): {mensaje_error}"
                )
            # Si todo bien, contar si fue creado o actualizado
            elif fue_creado:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            # Capturar cualquier error que no hayamos previsto
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Cliente ID {cliente.customer_id}: Error inesperado - {str(error_inesperado)}"
            )
    
    # Guardar todos los cambios en la base de datos
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado
