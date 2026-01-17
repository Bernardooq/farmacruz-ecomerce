/**
 * CartItem.jsx
 * ============
 * Componente de item individual en el carrito
 * 
 * Representa un producto en el carrito con controles para modificar
 * cantidad y removerlo. Incluye validación de stock y manejo de estado local.
 * 
 * Props:
 * @param {Object} item - Item del carrito del backend
 * @param {function} onQuantityChange - Callback para cambiar cantidad
 * @param {function} onRemove - Callback para remover item
 * 
 * Estructura de item:
 * - product: Objeto de producto con datos completos
 * - quantity: Cantidad actual en el carrito
 * - cart_cache_id: ID del item en el carrito
 * 
 * Características:
 * - Control de cantidad con botones +/- e input directo
 * - Validación automática de stock
 * - Auto-remoción si producto queda sin stock
 * - Input local permite escribir sin validar (solo valida al perder foco)
 * - Precio usa final_price del backend (incluye IVA)
 * 
 * Validaciones:
 * - Mínimo: 1 unidad
 * - Máximo: stock disponible
 * - No permite valores negativos, decimales o caracteres inválidos
 * 
 * Uso:
 * <CartItem
 *   item={cartItemData}
 *   onQuantityChange={(item, qty) => updateQty(item, qty)}
 *   onRemove={(item) => removeItem(item)}
 * />
 */

import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';

export default function CartItem({ item, onQuantityChange, onRemove }) {
  // ============================================
  // DATA EXTRACTION
  // ============================================

  // Extraer datos del producto
  const product = item.product || {};
  const image = product.image_url || '';
  const name = product.name || 'Producto';

  // Backend already calculated final_price with markup + IVA
  const price = product.final_price || product.base_price || 0;

  const quantity = item.quantity || 1;
  const stock = product.stock_count || 0;

  // ============================================
  // STATE
  // ============================================

  // Estado local para el input (permite escribir sin validar inmediatamente)
  const [inputValue, setInputValue] = useState(quantity);

  // Sincronizar inputValue cuando quantity cambie desde afuera
  // (solo si no estamos editando el input actualmente)
  if (inputValue !== quantity && document.activeElement?.type !== 'number') {
    setInputValue(quantity);
  }

  // ============================================
  // SIDE EFFECTS
  // ============================================

  // Auto-remover si el producto se queda sin stock
  if (stock < 1) {
    onRemove(item);
  }

  // ============================================
  // CALCULATIONS
  // ============================================

  const total = (price * quantity).toFixed(2);

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja cambios en el input de cantidad
   * Solo actualiza estado local sin validar
   */
  const handleInputChange = (e) => {
    setInputValue(e.target.value);
  };

  /**
   * Valida y aplica la cantidad cuando el input pierde el foco
   * Valida rangos y limita al stock disponible
   */
  const handleInputBlur = () => {
    const value = Number(inputValue);

    if (stock < 1) {
      // Sin stock, remover item
      onRemove(item);
    } else if (!value || isNaN(value) || value < 1) {
      // Valor inválido, resetear a 1
      setInputValue(1);
      onQuantityChange(item, 1);
    } else if (value > stock) {
      // Excede stock, limitar al máximo disponible
      setInputValue(stock);
      onQuantityChange(item, stock);
    } else {
      // Valor válido, aplicar (redondear hacia abajo)
      onQuantityChange(item, Math.floor(value));
    }
  };

  /**
   * Incrementa la cantidad en 1
   * Valida que no exceda el stock
   */
  const handleIncrement = () => {
    if (quantity < stock) {
      const newQty = quantity + 1;
      setInputValue(newQty);
      onQuantityChange(item, newQty);
    }
  };

  /**
   * Decrementa la cantidad en 1
   * Mínimo permitido: 1
   */
  const handleDecrement = () => {
    if (quantity > 1) {
      const newQty = quantity - 1;
      setInputValue(newQty);
      onQuantityChange(item, newQty);
    }
  };

  // ============================================
  // RENDER
  // ============================================
  return (
    <article className="cart-item">
      {/* Información del producto */}
      <div className="cart-item__product">
        <img src={image} alt={name} className="cart-item__image" />
        <div className="cart-item__details">
          <h3 className="cart-item__name">{name}</h3>
          <p className="cart-item__price">${price.toFixed(2)} MXN</p>
        </div>
      </div>

      {/* Selector de cantidad */}
      <div className="cart-item__quantity">
        <div className="quantity-selector">
          {/* Botón decrementar */}
          <button
            className="quantity-selector__btn"
            onClick={handleDecrement}
            disabled={quantity <= 1}
            aria-label="Disminuir cantidad"
          >
            -
          </button>

          {/* Input de cantidad */}
          <input
            type="number"
            value={inputValue}
            min="1"
            max={stock}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={(e) => {
              // Prevenir caracteres inválidos
              if (e.key === '-' || e.key === 'e' || e.key === '.' || e.key === ',') {
                e.preventDefault();
              }
              // Enter aplica el cambio
              if (e.key === 'Enter') {
                e.target.blur();
              }
            }}
            aria-label="Cantidad"
          />

          {/* Botón incrementar */}
          <button
            className="quantity-selector__btn"
            onClick={handleIncrement}
            disabled={quantity >= stock}
            aria-label="Aumentar cantidad"
          >
            +
          </button>
        </div>
      </div>

      {/* Total del item */}
      <p className="cart-item__total">${total}</p>

      {/* Botón remover */}
      <button
        className="cart-item__remove-btn"
        onClick={() => onRemove(item)}
        aria-label="Eliminar item"
      >
        <FontAwesomeIcon icon={faTimes} />
      </button>
    </article>
  );
}