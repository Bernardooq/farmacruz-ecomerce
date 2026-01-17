"""
CRUD para Edicion de Pedidos

Funciones para que marketing/admin puedan editar pedidos:
- Agregar/eliminar productos
- Modificar cantidades
- Recalcular precios automaticamente

Los precios se calculan segun la lista de precios del cliente.
"""

from typing import List
from uuid import UUID
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.base import Order, OrderItem, Product, PriceListItem, CustomerInfo, OrderStatus
from schemas.order_edit import OrderItemEdit

"""Edita los items de un pedido existente"""
def edit_order_items(db: Session, order_id: UUID, items: List[OrderItemEdit], customer_id: int) -> Order:    
    # Obtener el pedido
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    # Validar que el pedido NO este cancelado o entregado
    if order.status in [OrderStatus.cancelled, OrderStatus.delivered]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede editar un pedido en estado '{order.status.value}'"
        )
    
    # Obtener la lista de precios del cliente
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id
    ).first()
    
    if not customer_info or not customer_info.price_list_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El cliente no tiene una lista de precios asignada"
        )
    
    price_list_id = customer_info.price_list_id
    
    # Obtener items existentes del pedido
    existing_items = {item.order_item_id: item for item in order.items}
    
    # IDs de items que se mantendran/actualizaran
    items_to_keep = set()
    
    # Procesar cada item de la solicitud
    new_total = Decimal('0.00')
    
    for item_data in items:
        # Obtener informacion del producto
        product = db.query(Product).filter(Product.product_id == item_data.product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto '{item_data.product_id}' no encontrado"
            )
        
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto '{product.name}' no esta activo"
            )
        
        # Obtener markup de la lista de precios
        price_item = db.query(PriceListItem).filter(
            PriceListItem.price_list_id == price_list_id,
            PriceListItem.product_id == item_data.product_id
        ).first()
        
        if not price_item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El producto '{product.name}' no esta en la lista de precios del cliente"
            )
        
        # Calcular precio final
        base_price = Decimal(str(product.base_price or 0))
        markup_percentage = Decimal(str(price_item.markup_percentage or 0))
        iva_percentage = Decimal(str(product.iva_percentage or 0))
        
        price_with_markup = base_price * (1 + markup_percentage / 100)
        final_price = price_with_markup * (1 + iva_percentage / 100)
        
        # Si el item ya existe, actualizarlo
        if item_data.order_item_id and item_data.order_item_id in existing_items:
            existing_item = existing_items[item_data.order_item_id]
            existing_item.quantity = item_data.quantity
            existing_item.product_id = item_data.product_id
            existing_item.base_price = base_price
            existing_item.markup_percentage = markup_percentage
            existing_item.iva_percentage = iva_percentage
            existing_item.final_price = final_price
            
            items_to_keep.add(item_data.order_item_id)
        else:
            # Crear nuevo item
            new_item = OrderItem(
                order_id=order_id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                base_price=base_price,
                markup_percentage=markup_percentage,
                iva_percentage=iva_percentage,
                final_price=final_price
            )
            db.add(new_item)
        
        # Sumar al total
        new_total += final_price * item_data.quantity
    
    # Eliminar items que ya no estan en la lista
    for item_id, item in existing_items.items():
        if item_id not in items_to_keep:
            db.delete(item)
    
    # Actualizar el total del pedido
    order.total_amount = new_total
    
    db.commit()
    db.refresh(order)
    
    return order
