"""
Utilidad de Calculo de Precios para FARMACRUZ

Este modulo centraliza toda la logica de calculo de precios para asegurar
consistencia en toda la aplicacion.

Sistema de Precios:
1. base_price: Precio base del producto (sin markup ni IVA)
2. markup_percentage: % de ganancia segun lista de precios del cliente
3. iva_percentage: % de IVA (impuesto)
4. final_price = (base_price * (1 + markup/100)) * (1 + iva/100)

Todos los calculos usan Decimal para precision financiera.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session

from db.base import Product, CustomerInfo, PriceList, PriceListItem
from schemas.price_list import PriceCalculation
from schemas.product import ProductWithPrice


def calculate_final_price(base_price: Decimal, markup_percentage: Decimal, iva_percentage: Decimal) -> PriceCalculation:
    # Calcula el precio final con desglose completo de markup e IVA
    # Validaciones
    if base_price < 0:
        raise ValueError("El precio base no puede ser negativo")
    
    # Convertir a Decimal para calculos precisos (importante para dinero)
    base_price = Decimal(str(base_price))
    markup_percentage = Decimal(str(markup_percentage))
    iva_percentage = Decimal(str(iva_percentage))
    
    # === CaLCULO DE PRECIO CON MARKUP ===
    markup_multiplier = Decimal('1') + (markup_percentage / Decimal('100'))
    price_with_markup = base_price * markup_multiplier
    
    # === CaLCULO DE IVA ===
    iva_multiplier = iva_percentage / Decimal('100')
    iva_amount = price_with_markup * iva_multiplier
    
    # === CaLCULO DE PRECIO FINAL ===
    final_price = price_with_markup + iva_amount
    
    # === REDONDEO ===
    # Redondear a 2 decimales (centavos) usando redondeo banquero
    two_places = Decimal('0.01')
    base_price = base_price.quantize(two_places, rounding=ROUND_HALF_UP)
    price_with_markup = price_with_markup.quantize(two_places, rounding=ROUND_HALF_UP)
    iva_amount = iva_amount.quantize(two_places, rounding=ROUND_HALF_UP)
    final_price = final_price.quantize(two_places, rounding=ROUND_HALF_UP)
    
    return PriceCalculation(
        base_price=base_price,
        markup_percentage=markup_percentage,
        iva_percentage=iva_percentage,
        price_with_markup=price_with_markup,
        iva_amount=iva_amount,
        final_price=final_price
    )


def get_customer_markup(db: Session, customer_id: int, product_id: Optional[int] = None) -> Decimal:
    # Obtiene el porcentaje de markup para un cliente
    
    # Info cliente
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id 
    ).first()
    
    # Si no tiene CustomerInfo o no tiene lista de precios asignada
    if not customer_info or not customer_info.price_list_id:
        return Decimal('0')
    
    # Markup prod
    if product_id:
        price_list_item = db.query(PriceListItem).filter(
            PriceListItem.price_list_id == customer_info.price_list_id,
            PriceListItem.product_id == product_id
        ).first()
        
        # Si hay markup especifico para este producto, usarlo
        if price_list_item:
            return Decimal(str(price_list_item.markup_percentage))
    
    return Decimal('0')


def calculate_product_price_for_customer(db: Session, product_id: str, customer_id: int ) -> Optional[ProductWithPrice]:
    # Calcula el precio completo de un producto para un cliente especifico
    # Obtener prod
    product = db.query(Product).filter(
        Product.product_id == product_id
    ).first()
    
    if not product:
        return None
    
    # Markup cliente
    markup_percentage = get_customer_markup(
        db,
        customer_id=customer_id,
        product_id=product_id
    )
    
    # Calcular desgloce precios
    price_calc = calculate_final_price(
        base_price=product.base_price,
        markup_percentage=markup_percentage,
        iva_percentage=product.iva_percentage
    )
    
    # Respuesta
    return ProductWithPrice(
        product_id=product.product_id,
        codebar=product.codebar,
        name=product.name,
        description=product.description,
        base_price=product.base_price,
        iva_percentage=product.iva_percentage,
        image_url=product.image_url,
        stock_count=product.stock_count,
        is_active=product.is_active,
        category_id=product.category_id,
        category=product.category,
        markup_percentage=price_calc.markup_percentage,
        price_with_markup=price_calc.price_with_markup,
        iva_amount=price_calc.iva_amount,
        final_price=price_calc.final_price
    )
