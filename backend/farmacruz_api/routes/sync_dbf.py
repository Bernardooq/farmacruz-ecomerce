"""
Rutas para Sincronizacion desde Archivos DBF

Este modulo maneja la sincronizacion masiva de datos desde archivos DBF
del sistema legacy de FarmaCruz hacia la base de datos PostgreSQL.

¿Que hace este sistema?
-----------------------
Permite mantener sincronizados los datos entre:
- Sistema viejo (archivos DBF de Visual FoxPro)
- Sistema nuevo (PostgreSQL)

¿Como funciona?
--------------
1. Recibes datos del DBF en lotes (batches)
2. Para cada registro:
   - Si ya EXISTE (por ID) → Se ACTUALIZA
   - Si NO existe → Se CREA nuevo
3. Retornas un resumen: cuantos creados, actualizados, errores

ORDEN IMPORTANTE:
----------------
Debes sincronizar en este orden (porque hay dependencias):
1. PRIMERO → Listas de precios (son contenedores)
2. SEGUNDO → Productos (dependen de categorias)
3. TERCERO → Relaciones producto-lista (dependen de ambos anteriores)

Permisos:
--------
Solo administradores pueden usar estos endpoints.
"""

from datetime import datetime
from typing import List
from schemas.category import CategorySync
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from db.base import User
from schemas.price_list import PriceListCreate, PriceListItemCreate, PriceListItemCreateBulk, PriceListItemSync
from schemas.product import ProductCreate, ProductCreate2
from schemas.customer import CustomerSync  # Nuevo import
from crud import crud_sync


# Crear router con prefijo /sync
router = APIRouter()


# SCHEMAS DE RESPUESTA
class CleanupSchema(BaseModel):
    last_sync: datetime

class ResultadoSincronizacion(BaseModel):
    """
    Resultado de una operacion de sincronizacion
    
    Te dice exactamente que paso con tus datos:
    - Cuantos se recibieron
    - Cuantos se crearon (nuevos)
    - Cuantos se actualizaron (ya existian)
    - Cuantos tuvieron errores
    - Detalle de los errores
    """
    total_recibidos: int  # Total de registros que enviaste
    creados: int  # Registros nuevos que se crearon
    actualizados: int  # Registros que ya existian y se actualizaron
    errores: int  # Registros que tuvieron algun problema
    detalle_errores: List[str] = []  # Descripcion de cada error


# ENDPOINT: SINCRONIZAR LISTAS DE PRECIOS

@router.post("/price-lists", response_model=ResultadoSincronizacion)
def sincronizar_listas_de_precios(listas: List[PriceListCreate], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """
    Sincroniza listas de precios desde el DBF (en lote)
    """
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(total_recibidos=len(listas), creados=0, actualizados=0, errores=0, detalle_errores=[])
    
    # Procesar cada lista una por una
    for lista in listas:
        try:
            # Intentar guardar o actualizar la lista
            fue_creada, mensaje_error = crud_sync.guardar_o_actualizar_lista(
                db=db, lista_id=lista.price_list_id, nombre=lista.list_name, descripcion=lista.description, 
                esta_activa=lista.is_active if lista.is_active is not None else True, updated_at=lista.updated_at if lista.updated_at else None
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



@router.post("/categories", response_model=ResultadoSincronizacion)
def sincronizar_categorias(categorias: List[CategorySync], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """
    Sincroniza categorias desde el DBF (en lote)
    """
    resultado = ResultadoSincronizacion(total_recibidos=len(categorias), creados=0, actualizados=0, errores=0, detalle_errores=[])
    
    for categoria in categorias:
        try:
            fue_creada, mensaje_error = crud_sync.guardar_o_actualizar_categoria(db=db, name=categoria.name, description=categoria.description, updated_at=categoria.updated_at if categoria.updated_at else None
            )
            
            if mensaje_error:
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Categoria '{categoria.name}': {mensaje_error}"
                )
            elif fue_creada:
                resultado.creados += 1
            else:
                resultado.actualizados += 1
                
        except Exception as error_inesperado:
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Categoria '{categoria.name}': Error inesperado - {str(error_inesperado)}"
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
def sincronizar_productos(productos: List[ProductCreate2], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    """
    Sincroniza productos del catalogo desde el DBF (en lote)
    """
    # Preparar el contador de resultados
    resultado = ResultadoSincronizacion(total_recibidos=len(productos), creados=0, actualizados=0, errores=0, detalle_errores=[])
    
    # Procesar cada producto uno por uno con savepoints
    for producto in productos:
        # Crear un savepoint para este producto (sub-transaccion)
        savepoint = db.begin_nested()
        
        try:
            # Intentar guardar o actualizar el producto
            fue_creado, mensaje_error = crud_sync.guardar_o_actualizar_producto(
                db=db, producto_id=producto.product_id, codebar=producto.codebar, nombre=producto.name, descripcion=producto.description,
                descripcion_2=producto.descripcion_2, unidad_medida=producto.unidad_medida, precio_base=float(producto.base_price), porcentaje_iva=float(producto.iva_percentage) if producto.iva_percentage else 0.0,
                cantidad_stock=producto.stock_count if producto.stock_count else 0, esta_activo=producto.is_active if producto.is_active is not None else True,
                category_name=producto.category_name, url_imagen=producto.image_url, updated_at=producto.updated_at if producto.updated_at else None)
            
            # Si hubo error, hacer rollback del savepoint y registrarlo
            if mensaje_error:
                savepoint.rollback()
                resultado.errores += 1
                resultado.detalle_errores.append(
                    f"Producto ID {producto.product_id} (codebar: {producto.codebar}): {mensaje_error}"
                )
            # Si todo bien, confirmar savepoint y contar
            else:
                savepoint.commit()
                if fue_creado:
                    resultado.creados += 1
                else:
                    resultado.actualizados += 1
                
        except Exception as error_inesperado:
            # Hacer rollback del savepoint en caso de error
            savepoint.rollback()
            resultado.errores += 1
            resultado.detalle_errores.append(
                f"Producto ID {producto.product_id} (codebar: {producto.codebar}): "
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


# ENDPOINT: SINCRONIZAR ITEMS DE LISTAS (BULK)
@router.post("/price-list-items", response_model=ResultadoSincronizacion)
def sincronizar_items(
    items: List[PriceListItemSync], 
    usuario_actual: User = Depends(get_current_admin_user), 
    db: Session = Depends(get_db)
):
    """
    Sincroniza items de listas de precios en modo BULK
    """
    # Convertir items de Pydantic a dict para bulk upsert
    items_dict = [
        {
            "price_list_id": item.price_list_id,
            "product_id": item.product_id,
            "markup_percentage": float(item.markup_percentage),
            "final_price": float(item.final_price) if item.final_price else None,
            "updated_at": item.updated_at or datetime.now()
        }
        for item in items
    ]
    
    # Ejecutar bulk upsert
    creados, actualizados, omitidos, errores_lista = crud_sync.bulk_upsert_price_list_items(db, items_dict)
    
    resultado = ResultadoSincronizacion(
        total_recibidos=len(items),
        creados=creados,
        actualizados=actualizados,
        errores=omitidos, 
        detalle_errores=errores_lista
    )
    # Guardar cambios
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar los cambios: {str(error_commit)}"
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
    """
    # Convertir clientes de Pydantic a dict para bulk upsert
    clientes_dict = [
        {
            "customer_id": cliente.customer_id,
            "username": cliente.username,
            "email": cliente.email or f"{cliente.username}@farmacruz.com",
            "full_name": cliente.full_name or cliente.username,
            "password": cliente.password,
            "business_name": cliente.business_name,
            "rfc": cliente.rfc,
            "price_list_id": cliente.price_list_id,
            "sales_group_id": cliente.sales_group_id,
            "address_1": cliente.address_1,
            "address_2": cliente.address_2,
            "address_3": cliente.address_3,
            "agent_id": cliente.agent_id if cliente.agent_id else None,
            "updated_at": cliente.updated_at if cliente.updated_at else None
        }
        for cliente in clientes
    ]
    
    # Ejecutar bulk upsert
    creados, actualizados, errores_lista = crud_sync.bulk_upsert_customers(db, clientes_dict)
    
    # Preparar resultado
    resultado = ResultadoSincronizacion(
        total_recibidos=len(clientes),
        creados=creados,
        actualizados=actualizados,
        errores=len(errores_lista),
        detalle_errores=errores_lista
    )

    # Guardar todos los cambios en la base de datos
    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


# ENDPOINT: LIMPIEZA POST-SINCRONIZACION
@router.post("/cleanup", response_model=CleanupSchema)
def limpieza_post_sincronizacion(
    last_sync: CleanupSchema,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Desactiva o elimina items que no fueron actualizados desde la ultima sincronizacion
    """
    try:
        crud_sync.limpiar_items_no_sincronizados(db=db, last_sync=last_sync.last_sync)
        db.commit()
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al limpiar items no sincronizados: {str(error)}"
        )
    
    return last_sync