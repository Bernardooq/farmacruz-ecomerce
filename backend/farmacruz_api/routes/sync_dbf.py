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
1. Se reciben datos del DBF en lotes (batches)
2. Para cada registro:
   - Si ya EXISTE (por ID) → Se ACTUALIZA
   - Si NO existe → Se CREA nuevo
3. Retornar resumen: cuantos creados, actualizados, errores

Permisos:
--------
Solo administradores pueden usar estos endpoints.
"""

from datetime import datetime, timezone
from typing import List
from schemas.category import CategorySync
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from db.base import User
from schemas.price_list import PriceListCreate, PriceListItemCreate, PriceListItemCreateBulk, PriceListItemSync
from schemas.product import ProductCreate2
from schemas.customer import CustomerSync  
from schemas.user import SellerSync  
from crud import crud_sync


# Crear router con prefijo /sync
router = APIRouter()


# SCHEMAS DE RESPUESTA
class CleanupSchema(BaseModel):
    last_sync: datetime

class ResultadoSincronizacion(BaseModel):
    total_recibidos: int  # Total de registros enviados
    creados: int  # Registros nuevos que se crearon
    actualizados: int  # Registros que ya existian y se actualizaron
    errores: int  # Registros que tuvieron algun problema
    detalle_errores: List[str] = []  # Descripcion de cada error


""" POST /price-lists - Sincronizar listas de precios """
@router.post("/price-lists", response_model=ResultadoSincronizacion)
def sincronizar_listas_de_precios(listas: List[PriceListCreate], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
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


""" POST /categories - Sincronizar categorias"""
@router.post("/categories", response_model=ResultadoSincronizacion)
def sincronizar_categorias(categorias: List[CategorySync], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
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


""" POST /products - Sincronizar productos """
@router.post("/products", response_model=ResultadoSincronizacion)
def sincronizar_productos(productos: List[ProductCreate2], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    # Convertir productos de Pydantic a dict para bulk upsert
    productos_dict = [
        {
            "product_id": p.product_id,
            "codebar": p.codebar,
            "name": p.name,
            "description": p.description if p.description else None,
            "descripcion_2": p.descripcion_2 if p.descripcion_2 else None,
            "unidad_medida": p.unidad_medida,
            "base_price": float(p.base_price),
            "iva_percentage": float(p.iva_percentage) if p.iva_percentage else 0.0,
            "stock_count": p.stock_count if p.stock_count else 0,
            "is_active": p.is_active if p.is_active is not None else True,
            "category_name": p.category_name if p.category_name else None,
            "image_url": p.image_url if p.image_url else None,
            "updated_at": p.updated_at if p.updated_at else None
        }
        for p in productos
    ]
    
    # Ejecutar bulk upsert
    creados, actualizados, errores_lista = crud_sync.bulk_sync_prods(db, productos_dict)
    
    # Preparar resultado
    resultado = ResultadoSincronizacion(
        total_recibidos=len(productos),
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
            detail=f"No se pudieron guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


""" POST /price-list-items - Sincronizar items de listas de precios """
@router.post("/price-list-items", response_model=ResultadoSincronizacion)
def sincronizar_items(items: List[PriceListItemSync], 
    usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    # Convertir items de Pydantic a dict para bulk upsert
    items_dict = [
        {
            "price_list_id": item.price_list_id,
            "product_id": item.product_id,
            "markup_percentage": float(item.markup_percentage),
            "final_price": float(item.final_price) if item.final_price else None,
            "updated_at": item.updated_at or datetime.now(timezone.utc)
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



""" POST /customers - Sincronizar clientes """
@router.post("/customers", response_model=ResultadoSincronizacion)
def sincronizar_clientes(
    clientes: List[CustomerSync],  # Cambiado a CustomerSync
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Convertir clientes de Pydantic a dict para bulk upsert
    clientes_dict = [
        {
            "customer_id": cliente.customer_id,
            "username": cliente.username,
            "email": cliente.email or f"{cliente.username}@farmacruz.com",
            "full_name": cliente.full_name or cliente.username,
            "password": cliente.password,
            "business_name": cliente.business_name if cliente.business_name else None,
            "rfc": cliente.rfc if cliente.rfc else None,
            "price_list_id": cliente.price_list_id if cliente.price_list_id else None,
            "address_1": cliente.address_1 if cliente.address_1 else None,
            "address_2": cliente.address_2 if cliente.address_2 else None,
            "address_3": cliente.address_3 if cliente.address_3 else None,
            "telefono_1": cliente.telefono_1 if cliente.telefono_1 else None,
            "telefono_2": cliente.telefono_2 if cliente.telefono_2 else None,
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

""" POST /sellers - Sincronizar vendedores """
@router.post("/sellers", response_model=ResultadoSincronizacion)
def sincronizar_vendedores(vendedores: List[SellerSync], usuario_actual: User = Depends(get_current_admin_user), db: Session = Depends(get_db)):
    # Convertir a dict para bulk upsert
    vendedores_dict = [
        {
            "user_id": v.user_id,
            "username": v.username,
            "email": v.email or f"{v.username}@farmacruz.local",
            "full_name": v.full_name or v.username,
            "password": v.password,
            "is_active": v.is_active,
            "updated_at": v.updated_at if v.updated_at else None
        }
        for v in vendedores
    ]
    
    # Ejecutar bulk upsert
    creados, actualizados, errores_lista = crud_sync.bulk_upsert_sellers(db, vendedores_dict)
    resultado = ResultadoSincronizacion(
        total_recibidos=len(vendedores),
        creados=creados,
        actualizados=actualizados,
        errores=len(errores_lista),
        detalle_errores=errores_lista
    )

    try:
        db.commit()
    except Exception as error_commit:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar los cambios: {str(error_commit)}"
        )
    
    return resultado


""" POST /cleanup - Limpiar productos, categorias, listas y items no sincronizados """
@router.post("/cleanup", response_model=CleanupSchema)
def limpieza_post_sincronizacion(
    last_sync: CleanupSchema,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Desactiva o elimina productos, categorias, listas y items que no fueron sincronizados.
    NO toca usuarios (customers ni sellers)."""
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


""" POST /cleanup-users - Limpiar usuarios (customers y sellers) no sincronizados """
@router.post("/cleanup-users", response_model=CleanupSchema)
def limpieza_users_post_sincronizacion(
    last_sync: CleanupSchema,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Desactiva customers y sellers que no fueron sincronizados recientement."""
    try:
        crud_sync.limpiar_users_no_sincronizados(db=db, last_sync=last_sync.last_sync)
        db.commit()
    except Exception as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al limpiar usuarios no sincronizados: {str(error)}"
        )
    
    return last_sync