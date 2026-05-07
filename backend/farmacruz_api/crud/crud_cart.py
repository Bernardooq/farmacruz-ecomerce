"""
Funciones para manejar el carrito temporal de clientes:
- Ver items del carrito
- Agregar productos al carrito
- Actualizar cantidades
- Eliminar items
- Vaciar carrito completo
- Obtener conteo de items en el carrito
El carrito se limpia cuando se crea un pedido.
"""

from decimal import Decimal
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from utils.price_utils import get_catalog_product_info
from db.base import CartCache, CustomerInfo, PriceListItem, Product
import pandas as pd
import io

"""Obtiene todos los items en el carrito de un cliente con detalles del producto y precios"""
def get_cart(db: Session, customer_id: int) -> List[dict]: 
    cart_items = db.query(CartCache).options(
        joinedload(CartCache.product).joinedload(Product.category)
    ).filter(
        CartCache.customer_id == customer_id
    ).all()
    
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    # Enriquecer con informacion del producto en formato anidado usando middleware
    result = []
    for item in cart_items:
        if not item.product:
            continue
            
        product_data = None
        if customer_info and customer_info.price_list_id:
            product_data = get_catalog_product_info(db, item.product, customer_info.price_list_id)
        
        # Si no hay lista de precios o no se encontro el item, construir dict basico seguro
        if not product_data:
            product_data = {
                'product_id': item.product.product_id,
                'codebar': item.product.codebar,
                'name': item.product.name,
                'description': item.product.description,
                'descripcion_2': item.product.descripcion_2,
                'unidad_medida': item.product.unidad_medida,
                'iva_percentage': float(item.product.iva_percentage or 0),
                'image_url': item.product.image_url,
                'stock_count': item.product.stock_count,
                'is_active': item.product.is_active,
                'category_id': item.product.category_id,
                'category': {
                    'category_id': item.product.category.category_id,
                    'name': item.product.category.name
                } if item.product.category else None,
                'final_price': None,
                'image_version': item.product.image_version,
            }
            
        result.append({
            "cart_cache_id": item.cart_cache_id,
            "customer_id": item.customer_id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "added_at": item.added_at,
            "updated_at": item.updated_at,
            "product": product_data
        })
    
    return result

"""Agrega un producto al carrito o incrementa su cantidad si ya existe"""
def add_to_cart(db: Session, customer_id: int, product_id: str, quantity: int = 1, cap_at_stock: bool = False) -> CartCache:
    # Validaciones 
    product = db.query(Product).filter(
        Product.product_id == product_id
    ).first()
    
    if not product or not product.is_active:
        raise ValueError("Producto no disponible")
    
    # Verificar si el item ya esta en el carrito
    cart_item = db.query(CartCache).filter(
        CartCache.customer_id == customer_id,
        CartCache.product_id == product_id
    ).first()
    
    current_qty = cart_item.quantity if cart_item else 0
    total_qty = current_qty + quantity
    
    if total_qty > product.stock_count:
        if cap_at_stock:
            total_qty = product.stock_count
            if total_qty == current_qty:
                raise ValueError("Ya tienes el máximo stock disponible en el carrito")
        else:
            raise ValueError(f"Cantidad excede el stock disponible ({product.stock_count})")
    
    if cart_item:
        cart_item.quantity = total_qty
        cart_item.updated_at = datetime.now(timezone.utc)
    else:
        cart_item = CartCache(
            customer_id=customer_id,
            product_id=product_id,
            quantity=total_qty
        )
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)
    return cart_item


"""Actualiza la cantidad de un item en el carrito"""
def update_cart_item(db: Session, cart_id: int, quantity: int) -> Optional[CartCache]:
    cart_item = db.query(CartCache).options(joinedload(CartCache.product)).filter(
        CartCache.cart_cache_id == cart_id
    ).first()
    
    if not cart_item:
        return None
    
    if quantity <= 0:
        db.delete(cart_item)
        cart_item = None
    else:
        # Validar stock disponible antes de actualizar
        if cart_item.product and quantity > cart_item.product.stock_count:
            raise ValueError(f"Solo hay {cart_item.product.stock_count} unidades disponibles")
            
        cart_item.quantity = quantity
        cart_item.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    return cart_item


"""Elimina un item especifico del carrito"""
def remove_from_cart(db: Session, cart_id: int) -> bool:
    cart_item = db.query(CartCache).filter(
        CartCache.cart_cache_id == cart_id
    ).first()
    
    if cart_item:
        db.delete(cart_item)
        db.commit()
        return True
    
    return False

"""Vacía todo el carrito de un cliente"""
def clear_cart(db: Session, customer_id: int) -> int:
    deleted_count = db.query(CartCache).filter(
        CartCache.customer_id == customer_id
    ).delete()
    
    db.commit()
    return deleted_count

"""Obtiene el numero total de items en el carrito de un cliente"""
def get_cart_item_count(db: Session, customer_id: int) -> int:
    return db.query(func.count(CartCache.cart_cache_id)).filter(
        CartCache.customer_id == customer_id
    ).scalar() or 0

"""Importa productos al carrito desde un archivo Excel"""
def import_cart_from_excel(db: Session, customer_id: int, file_content: bytes) -> dict:
    try:
        df = pd.read_excel(io.BytesIO(file_content), header=None)
    except Exception as e:
        raise ValueError(f"Error al leer el archivo Excel: {str(e)}")

    notifications = []
    
    for index, row in df.iterrows():
        # Validar que existan al menos 2 columnas
        if len(row) < 2:
            continue
            
        codebar_raw = row[0]
        qty_raw = row[1]
        
        # Ignorar filas vacías o donde la cantidad no sea un número (posible header)
        if pd.isna(codebar_raw) or pd.isna(qty_raw):
            continue
            
        try:
            qty = int(qty_raw)
            if qty <= 0:
                continue
        except (ValueError, TypeError):
            # Si la cantidad no se puede convertir a int, probablemente sea un header
            continue
            
        codebar = str(codebar_raw).strip()
        if codebar.endswith(".0"):
            codebar = codebar[:-2]
            
        # Buscar el producto
        product = db.query(Product).filter(
            Product.codebar == codebar
        ).first()
        
        if not product:
            notifications.append(f"❌ Código '{codebar}': Producto no encontrado.")
            continue

            
        if not product.is_active:
            notifications.append(f"❌ '{product.name}': El producto no está activo.")
            continue

            
        if product.stock_count <= 0:
            notifications.append(f"❌ '{product.name}': Producto sin stock disponible.")
            continue

            
        # Verificar si el item ya está en el carrito
        cart_item = db.query(CartCache).filter(
            CartCache.customer_id == customer_id,
            CartCache.product_id == product.product_id
        ).first()
        
        current_qty = cart_item.quantity if cart_item else 0
        total_qty = current_qty + qty
        
        # Ajustar por límite de stock
        if total_qty > product.stock_count:
            added_qty = product.stock_count - current_qty
            if added_qty <= 0:
                notifications.append(f"⚠️ '{product.name}': Ya tienes el máximo stock en tu carrito.")
                continue
            else:
                total_qty = product.stock_count
                notifications.append(f"⚠️ '{product.name}': Cantidad ajustada al máximo disponible ({product.stock_count}).")
        else:
            notifications.append(f"✅ '{product.name}': {qty} unidades agregadas.")

            
        # Actualizar o crear item en el carrito
        if cart_item:
            cart_item.quantity = total_qty
            cart_item.updated_at = datetime.now(timezone.utc)
        else:
            new_cart_item = CartCache(
                customer_id=customer_id,
                product_id=product.product_id,
                quantity=total_qty
            )
            db.add(new_cart_item)
            
    db.commit()
    
    return {
        "message": "Importación finalizada",
        "notifications": notifications
    }
