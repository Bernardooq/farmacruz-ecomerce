"""
Utilidad de Cálculo de Precios para FARMACRUZ

Este módulo centraliza toda la lógica de cálculo de precios para asegurar
consistencia en toda la aplicación.

Sistema de Precios:
1. base_price: Precio base del producto (sin markup ni IVA)
2. markup_percentage: % de ganancia según lista de precios del cliente
3. iva_percentage: % de IVA (impuesto)
4. final_price = (base_price * (1 + markup/100)) * (1 + iva/100)

Todos los cálculos usan Decimal para precisión financiera.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy.orm import Session

from db.base import Product, CustomerInfo, PriceList, PriceListItem
from schemas.price_list import PriceCalculation
from schemas.product import ProductWithPrice


def calculate_final_price(
    base_price: Decimal,
    markup_percentage: Decimal,
    iva_percentage: Decimal
) -> PriceCalculation:
    """
    Calcula el precio final con desglose completo de markup e IVA
    
    Fórmula paso a paso:
    1. price_with_markup = base_price * (1 + markup_percentage/100)
    2. iva_amount = price_with_markup * (iva_percentage/100)
    3. final_price = price_with_markup + iva_amount
    
    Ejemplo:
        base_price = 100.00
        markup_percentage = 25.00 (25%)
        iva_percentage = 16.00 (16%)
        
        price_with_markup = 100 * 1.25 = 125.00
        iva_amount = 125 * 0.16 = 20.00
        final_price = 125 + 20 = 145.00
    
    Args:
        base_price: Precio base del producto
        markup_percentage: Porcentaje de ganancia (ej: 25.00 para 25%)
        iva_percentage: Porcentaje de IVA (ej: 16.00 para 16%)
    
    Returns:
        PriceCalculation con desglose completo de precios
    
    Raises:
        ValueError: Si base_price es negativo
    """
    # === VALIDACIONES ===
    if base_price < 0:
        raise ValueError("El precio base no puede ser negativo")
    
    # Convertir a Decimal para cálculos precisos (importante para dinero)
    base_price = Decimal(str(base_price))
    markup_percentage = Decimal(str(markup_percentage))
    iva_percentage = Decimal(str(iva_percentage))
    
    # === CÁLCULO DE PRECIO CON MARKUP ===
    # Ejemplo: 25% markup = multiplicar por 1.25
    markup_multiplier = Decimal('1') + (markup_percentage / Decimal('100'))
    price_with_markup = base_price * markup_multiplier
    
    # === CÁLCULO DE IVA ===
    # Ejemplo: 16% IVA de 125.00 = 20.00
    iva_multiplier = iva_percentage / Decimal('100')
    iva_amount = price_with_markup * iva_multiplier
    
    # === CÁLCULO DE PRECIO FINAL ===
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


def get_customer_markup(
    db: Session,
    customer_id: int,  # CORREGIDO: era user_id
    product_id: Optional[int] = None
) -> Decimal:
    """
    Obtiene el porcentaje de markup para un cliente
    
    El markup puede ser:
    1. Específico por producto (si el producto tiene markup en la lista)
    2. General de la lista de precios (si no hay markup específico)
    3. 0% si el cliente no tiene lista de precios asignada
    
    Args:
        db: Sesión de base de datos
        customer_id: ID del cliente (CORREGIDO: era user_id)
        product_id: ID del producto (opcional, para markup específico)
    
    Returns:
        Porcentaje de markup como Decimal (ej: 25.00 para 25%)
        Retorna 0 si el cliente no tiene lista de precios
    """
    # === OBTENER INFORMACIÓN DEL CLIENTE ===
    customer_info = db.query(CustomerInfo).filter(
        CustomerInfo.customer_id == customer_id  # CORREGIDO: era user_id
    ).first()
    
    # Si no tiene CustomerInfo o no tiene lista de precios asignada
    if not customer_info or not customer_info.price_list_id:
        return Decimal('0')
    
    # === BUSCAR MARKUP ESPECÍFICO POR PRODUCTO ===
    if product_id:
        price_list_item = db.query(PriceListItem).filter(
            PriceListItem.price_list_id == customer_info.price_list_id,
            PriceListItem.product_id == product_id
        ).first()
        
        # Si hay markup específico para este producto, usarlo
        if price_list_item:
            return Decimal(str(price_list_item.markup_percentage))
    
    # === USAR MARKUP GENERAL DE LA LISTA ===
    # Si no hay markup específico, retornar 0 (sin markup)
    # NOTA: En el esquema v2.1, el markup está en PriceListItem, no en PriceList
    # Si se necesita un markup por defecto, agregarlo a la tabla PriceList
    return Decimal('0')


def calculate_product_price_for_customer(
    db: Session,
    product_id: int,
    customer_id: int  # CORREGIDO: era user_id
) -> Optional[ProductWithPrice]:
    """
    Calcula el precio completo de un producto para un cliente específico
    
    Incluye:
    - Información completa del producto
    - Markup del cliente aplicado
    - Cálculo de IVA
    - Precio final
    
    Args:
        db: Sesión de base de datos
        product_id: ID del producto
        customer_id: ID del cliente (CORREGIDO: era user_id)
    
    Returns:
        ProductWithPrice con todos los precios calculados
        None si el producto no existe
    """
    # === OBTENER PRODUCTO ===
    product = db.query(Product).filter(
        Product.product_id == product_id
    ).first()
    
    if not product:
        return None
    
    # === OBTENER MARKUP DEL CLIENTE ===
    markup_percentage = get_customer_markup(
        db,
        customer_id=customer_id,
        product_id=product_id
    )
    
    # === CALCULAR DESGLOSE DE PRECIOS ===
    price_calc = calculate_final_price(
        base_price=product.base_price,
        markup_percentage=markup_percentage,
        iva_percentage=product.iva_percentage
    )
    
    # === CONSTRUIR RESPUESTA ===
    return ProductWithPrice(
        product_id=product.product_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        base_price=product.base_price,
        iva_percentage=product.iva_percentage,
        image_url=product.image_url,
        stock_count=product.stock_count,
        is_active=product.is_active,
        category_id=product.category_id,
        category=product.category,
        # Precios calculados
        markup_percentage=price_calc.markup_percentage,
        price_with_markup=price_calc.price_with_markup,
        iva_amount=price_calc.iva_amount,
        final_price=price_calc.final_price
    )
