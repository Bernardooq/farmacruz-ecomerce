"""
API routes for production-optimized DBF sync.

Utiliza ThreadPoolExecutor para procesamiento independiente de workers.
Los workers de Uvicorn responden inmediatamente y quedan libres.
Los syncs se procesan en threads dedicados del pool.
"""

import gzip
import json
import logging
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from db.base import User
from db.session import SessionLocal
from crud import crud_dbf_upload

# Configurar logger
logger = logging.getLogger(__name__)

# ==========================================
# THREAD POOL DEDICADO (independiente de workers Uvicorn)
# ==========================================
# Este pool ejecuta syncs en threads separados
# max_workers=2: Máximo 2 syncs simultáneos, el resto espera en cola
executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="sync_thread_"
)

logger.info(f"ThreadPoolExecutor iniciado con max_workers=2")


# Response schema
class ResultadoSincronizacion(BaseModel):
    creados: int
    actualizados: int
    errores: int = 0
    detalle_errores: List[str] = []


router = APIRouter()


async def decompress_request(request: Request) -> Dict[str, Any]:
    """Helper to handle GZIP decompression"""
    try:
        body = await request.body()
        if request.headers.get("Content-Encoding") == "gzip":
            print(f"Decompressing GZIP payload: {len(body)/1024:.2f} KB")
            decompressed = gzip.decompress(body)
            return json.loads(decompressed.decode('utf-8'))
        return json.loads(body.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Decompression/JSON error: {str(e)}")


def _process_productos_thread(categorias: list, productos: list):
    """Ejecuta en thread separado del ThreadPool"""
    db = SessionLocal()
    try:
        start = time.time()
        logger.info(f"[THREAD-SYNC] Iniciando sync de {len(productos)} productos + {len(categorias)} categorias")
        
        resultado = crud_dbf_upload.process_productos_from_json(
            categorias=categorias,
            productos=productos,
            db=db
        )
        
        elapsed = time.time() - start
        logger.info(
            f"[THREAD-SYNC] Productos completado en {elapsed:.2f}s - "
            f"Creados: {resultado['creados']}, Actualizados: {resultado['actualizados']}, Errores: {resultado['errores']}"
        )
    except Exception as e:
        logger.error(f"[THREAD-SYNC] Error fatal en productos: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/productos-json", status_code=202)
async def upload_productos_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user)
):
    """
    Step 1: Upload Products and Categories
    Payload: { "categorias": [...], "productos": [...] }
    """
    try:
        data = await decompress_request(request)
        
        if "productos" not in data:
            raise HTTPException(status_code=400, detail="Missing 'productos' list")
        
        categorias = data.get("categorias", [])
        productos = data["productos"]
        
        # Encolar en ThreadPool (worker se libera inmediatamente)
        executor.submit(_process_productos_thread, categorias, productos)
        
        return {
            "status": "sync_initiated",
            "message": f"Procesando {len(productos)} productos en thread pool",
            "total_items": len(productos) + len(categorias)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_productos_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def _process_listas_thread(listas: list):
    """Ejecuta en thread separado del ThreadPool"""
    db = SessionLocal()
    try:
        start = time.time()
        logger.info(f"[THREAD-SYNC] Iniciando sync de {len(listas)} listas de precios")
        
        resultado = crud_dbf_upload.process_listas_precios_from_json(
            listas=listas,
            db=db
        )
        
        elapsed = time.time() - start
        logger.info(
            f"[THREAD-SYNC] Listas completado en {elapsed:.2f}s - "
            f"Creados: {resultado['creados']}, Actualizados: {resultado['actualizados']}, Errores: {resultado['errores']}"
        )
    except Exception as e:
        logger.error(f"[THREAD-SYNC] Error fatal en listas: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/listas-precios-json", status_code=202)
async def upload_listas_precios_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user)
):
    """
    Step 2: Upload Unique Price Lists (Headers)
    Payload: { "listas": [ {"price_list_id": 1, "name": "Lista A"}, ... ] }
    """
    try:
        data = await decompress_request(request)
        
        if "listas" not in data:
            raise HTTPException(status_code=400, detail="Missing 'listas' list")
        
        listas = data["listas"]
        
        executor.submit(_process_listas_thread, listas)
        
        return {
            "status": "sync_initiated",
            "message": f"Procesando {len(listas)} listas en thread pool",
            "total_items": len(listas)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_listas_precios_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")



def _process_items_thread(items: list):
    """Ejecuta en thread separado del ThreadPool (operación más pesada - ~18k items)"""
    db = SessionLocal()
    try:
        start = time.time()
        logger.info(f"[THREAD-SYNC] Iniciando sync de {len(items)} items de listas")
        
        resultado = crud_dbf_upload.process_items_precios_from_json(
            items=items,
            db=db
        )
        
        elapsed = time.time() - start
        logger.info(
            f"[THREAD-SYNC] Items completado en {elapsed:.2f}s - "
            f"Creados: {resultado['creados']}, Actualizados: {resultado['actualizados']}, Errores: {resultado['errores']}"
        )
        
        if elapsed > 10:
            logger.warning(f"Items tardó {elapsed:.2f}s - considerar batching")
    except Exception as e:
        logger.error(f"[THREAD-SYNC] Error fatal en items: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/items-precios-json", status_code=202)
async def upload_items_precios_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user)
):
    """
    Step 3: Upload Price List Items (Relations)
    Payload: { "items": [ {"price_list_id": 1, "product_id": "...", ...}, ... ] }
    """
    try:
        data = await decompress_request(request)
    
        if "items" not in data:
            raise HTTPException(status_code=400, detail="Missing 'items' list")
        
        items = data["items"]
        
        executor.submit(_process_items_thread, items)
        
        return {
            "status": "sync_initiated",
            "message": f"Procesando {len(items)} items en thread pool",
            "total_items": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_items_precios_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    

def _process_sellers_thread(sellers: list):
    """Ejecuta en thread separado del ThreadPool"""
    db = SessionLocal()
    try:
        start = time.time()
        logger.info(f"[THREAD-SYNC] Iniciando sync de {len(sellers)} vendedores")
        
        resultado = crud_dbf_upload.process_sellers_from_json(
            sellers=sellers,
            db=db
        )
        
        elapsed = time.time() - start
        logger.info(
            f"[THREAD-SYNC] Sellers completado en {elapsed:.2f}s - "
            f"Creados: {resultado['creados']}, Actualizados: {resultado['actualizados']}, Errores: {resultado['errores']}"
        )
    except Exception as e:
        logger.error(f"[THREAD-SYNC] Error fatal en sellers: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/sellers-json", status_code=202)
async def upload_sellers_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user)
):
    """
    Step 4: Upload Sellers (Agents)
    Payload: { "sellers": [ {"user_id": 1, "username": "...", ...}, ... ] }
    """
    try:
        data = await decompress_request(request)
        
        if "sellers" not in data:
            raise HTTPException(status_code=400, detail="Missing 'sellers' list")
        
        sellers = data["sellers"]
        
        executor.submit(_process_sellers_thread, sellers)
        
        return {
            "status": "sync_initiated",
            "message": f"Procesando {len(sellers)} vendedores en thread pool",
            "total_items": len(sellers)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_sellers_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


def _process_customers_thread(customers: list):
    """Ejecuta en thread separado del ThreadPool"""
    db = SessionLocal()
    try:
        start = time.time()
        logger.info(f"[THREAD-SYNC] Iniciando sync de {len(customers)} clientes")
        
        resultado = crud_dbf_upload.process_customers_from_json(
            customers=customers,
            db=db
        )
        
        elapsed = time.time() - start
        logger.info(
            f"[THREAD-SYNC] Customers completado en {elapsed:.2f}s - "
            f"Creados: {resultado['creados']}, Actualizados: {resultado['actualizados']}, Errores: {resultado['errores']}"
        )
    except Exception as e:
        logger.error(f"[THREAD-SYNC] Error fatal en customers: {str(e)}")
        traceback.print_exc()
    finally:
        db.close()

@router.post("/customers-json", status_code=202)
async def upload_customers_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user)
):
    """
    Step 5: Upload Customers
    Payload: { "customers": [ {"customer_id": 1, "username": "...", ...}, ... ] }
    """
    try:
        data = await decompress_request(request)
        
        if "customers" not in data:
            raise HTTPException(status_code=400, detail="Missing 'customers' list")
        
        customers = data["customers"]
        
        executor.submit(_process_customers_thread, customers)
        
        return {
            "status": "sync_initiated",
            "message": f"Procesando {len(customers)} clientes en thread pool",
            "total_items": len(customers)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en upload_customers_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")