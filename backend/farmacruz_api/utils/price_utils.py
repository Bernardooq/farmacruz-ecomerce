"""
Utilidades centralizadas para cálculo de precios.

Flujo de precios:
1. base_price × (1 + markup%) = precio sin IVA (price_without_iva)
2. price_without_iva × (1 + iva%) = precio final con IVA (final_price)
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session
from db.base import Product, PriceListItem


# Tolerancia para considerar precios "similares" (1%)
PRICE_TOLERANCE_PERCENTAGE = Decimal('0.01')


def calculate_final_price_with_markup(
    base_price: Decimal,
    markup_percentage: Decimal,
    stored_final_price: Optional[Decimal] = None
) -> Decimal:
    """
    Calcula el precio CON MARKUP pero SIN IVA.
    Este es el precio que se guarda en price_without_iva de orderitems.
    
    Args:
        base_price: Precio base del producto (sin IVA, sin markup)
        markup_percentage: Porcentaje de markup a aplicar
        stored_final_price: Precio final almacenado en BD de pricelistitems (opcional)
    
    Returns:
        Precio con markup, SIN IVA, redondeado a 2 decimales
    
    Lógica:
        1. calculated_price = base_price * (1 + markup_percentage/100)
        2. Si stored_final_price existe y difiere en menos del 1%:
           → Usar stored_final_price (confiamos en lo almacenado)
        3. Si no existe o difiere mucho:
           → Usar calculated_price
    """
    # Convertir a Decimal
    base_price = Decimal(str(base_price))
    markup_percentage = Decimal(str(markup_percentage))
    
    # Calcular precio con markup
    markup_multiplier = Decimal('1') + (markup_percentage / Decimal('100'))
    calculated_price = base_price * markup_multiplier
    
    # Redondear a 2 decimales
    two_places = Decimal('0.01')
    calculated_price = calculated_price.quantize(two_places, rounding=ROUND_HALF_UP)
    
    # Si no hay precio almacenado, usar el calculado
    if stored_final_price is None:
        return calculated_price
    
    stored_final_price = Decimal(str(stored_final_price))
    
    # Calcular diferencia porcentual
    if stored_final_price > 0:
        diff = abs(calculated_price - stored_final_price)
        diff_percentage = diff / stored_final_price
        
        # Si la diferencia es menor al 1%, usar el almacenado
        if diff_percentage <= PRICE_TOLERANCE_PERCENTAGE:
            return stored_final_price
    
    # Si difieren mucho o stored_final_price es 0, usar el calculado
    return calculated_price


def get_product_final_price(
    db: Session,
    product: Product,
    price_list_id: int
) -> Optional[dict]:
    """
    Obtiene el precio con markup (SIN IVA) de un producto para una lista de precios.
    
    Args:
        db: Sesión de base de datos
        product: Producto
        price_list_id: ID de lista de precios
    
    Returns:
        Dict con información de precio o None si no hay PriceListItem
        {
            "base_price": Decimal,
            "markup_percentage": Decimal,
            "final_price": Decimal
        }
    """
    # Buscar item en lista de precios
    price_item = db.query(PriceListItem).filter(
        PriceListItem.price_list_id == price_list_id,
        PriceListItem.product_id == product.product_id
    ).first()
    
    if not price_item:
        return None
    
    # Calcular precio final
    base_price = Decimal(str(product.base_price or 0))
    markup_percentage = Decimal(str(price_item.markup_percentage or 0))
    stored_final_price = Decimal(str(price_item.final_price)) if price_item.final_price else None
    
    final_price = calculate_final_price_with_markup(
        base_price=base_price,
        markup_percentage=markup_percentage,
        stored_final_price=stored_final_price
    )
    
    return {
        "base_price": base_price,
        "markup_percentage": markup_percentage,
        "final_price": final_price
    }


def format_price_info(
    base_price: Decimal,
    markup_percentage: Decimal,
    final_price: Decimal
) -> dict:
    """
    Formatea información de precio para respuestas API.
    
    Returns:
        {
            "base_price": float,
            "markup_percentage": float,
            "markup_amount": float,
            "final_price": float
        }
    """
    base_price = Decimal(str(base_price))
    markup_percentage = Decimal(str(markup_percentage))
    final_price = Decimal(str(final_price))
    
    markup_amount = final_price - base_price
    
    return {
        "base_price": round(float(base_price), 2),
        "markup_percentage": round(float(markup_percentage), 2),
        "markup_amount": round(float(markup_amount), 2),
        "final_price": round(float(final_price), 2)
    }


def apply_iva(price: Decimal, iva_percentage: Decimal) -> Decimal:
    """
    Aplica IVA a un precio.
    
    Args:
        price: Precio sin IVA (ya con markup)
        iva_percentage: Porcentaje de IVA (ej: 16.0)
    
    Returns:
        Precio con IVA, redondeado a 2 decimales
    """
    price = Decimal(str(price))
    iva_percentage = Decimal(str(iva_percentage))
    
    iva_multiplier = Decimal('1') + (iva_percentage / Decimal('100'))
    price_with_iva = price * iva_multiplier
    
    two_places = Decimal('0.01')
    return price_with_iva.quantize(two_places, rounding=ROUND_HALF_UP)
