"""
API routes for production-optimized DBF sync.
"""

import gzip
import json
import traceback
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from dependencies import get_db, get_current_admin_user
from db.base import User
from crud import crud_dbf_upload


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


@router.post("/productos-json", response_model=ResultadoSincronizacion)
async def upload_productos_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Step 1: Upload Products and Categories
    Payload: { "categorias": [...], "productos": [...] }
    """
    try:
        data = await decompress_request(request)
        
        if "productos" not in data:
            raise HTTPException(status_code=400, detail="Missing 'productos' list")
            
        resultado = crud_dbf_upload.process_productos_from_json(
            categorias=data.get("categorias", []),
            productos=data["productos"],
            db=db
        )
        
        return ResultadoSincronizacion(**resultado)
    except Exception as e:
        print(f"CRITICAL ERROR in upload_productos_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/listas-precios-json", response_model=ResultadoSincronizacion)
async def upload_listas_precios_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Step 2: Upload Unique Price Lists (Headers)
    Payload: { "listas": [ {"price_list_id": 1, "name": "Lista A"}, ... ] }
    """
    try:
        data = await decompress_request(request)
        
        if "listas" not in data:
            raise HTTPException(status_code=400, detail="Missing 'listas' list")
            
        resultado = crud_dbf_upload.process_listas_precios_from_json(
            listas=data["listas"],
            db=db
        )
        
        return ResultadoSincronizacion(**resultado)
    except Exception as e:
        print(f"CRITICAL ERROR in upload_listas_precios_json: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


    return ResultadoSincronizacion(**resultado)


@router.post("/items-precios-json", response_model=ResultadoSincronizacion)
async def upload_items_precios_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Step 3: Upload Price List Items (Relations)
    Payload: { "items": [ {"price_list_id": 1, "product_id": "...", ...}, ... ] }
    """
    data = await decompress_request(request)
    
    if "items" not in data:
        raise HTTPException(status_code=400, detail="Missing 'items' list")
        
    resultado = crud_dbf_upload.process_items_precios_from_json(
        items=data["items"],
        db=db
    )
    
    return ResultadoSincronizacion(**resultado)


@router.post("/sellers-json", response_model=ResultadoSincronizacion)
async def upload_sellers_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Step 4: Upload Sellers (Agents)
    Payload: { "sellers": [ {"user_id": 1, "username": "...", ...}, ... ] }
    """
    data = await decompress_request(request)
    
    if "sellers" not in data:
        raise HTTPException(status_code=400, detail="Missing 'sellers' list")
        
    resultado = crud_dbf_upload.process_sellers_from_json(
        sellers=data["sellers"],
        db=db
    )
    
    return ResultadoSincronizacion(**resultado)


@router.post("/customers-json", response_model=ResultadoSincronizacion)
async def upload_customers_json(
    request: Request,
    usuario_actual: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Step 5: Upload Customers
    Payload: { "customers": [ {"customer_id": 1, "username": "...", ...}, ... ] }
    """
    data = await decompress_request(request)
    
    if "customers" not in data:
        raise HTTPException(status_code=400, detail="Missing 'customers' list")
        
    resultado = crud_dbf_upload.process_customers_from_json(
        customers=data["customers"],
        db=db
    )
    
    return ResultadoSincronizacion(**resultado)