import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';

export default function CartItem({ item, onQuantityChange, onRemove }) {
  // ============================================
  // DATA EXTRACTION
  // ============================================
  const product = item.product || {};
  const image = product.image_url || '';
  const name = product.name || 'Producto';
  const price = product.final_price || product.base_price || 0;
  const quantity = item.quantity || 1;
  const stock = product.stock_count || 0;

  // ============================================
  // STATE
  // ============================================
  const [inputValue, setInputValue] = useState(quantity);

  // Sincronizar inputValue cuando quantity cambie desde afuera
  if (inputValue !== quantity && document.activeElement?.type !== 'number') {
    setInputValue(quantity);
  }

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
  const handleInputChange = (e) => setInputValue(e.target.value);

  const handleInputBlur = () => {
    const value = Number(inputValue);
    if (stock < 1) {
      onRemove(item);
    } else if (!value || isNaN(value) || value < 1) {
      setInputValue(1);
      onQuantityChange(item, 1);
    } else if (value > stock) {
      setInputValue(stock);
      onQuantityChange(item, stock);
    } else {
      onQuantityChange(item, Math.floor(value));
    }
  };

  const handleIncrement = () => {
    if (quantity < stock) {
      const newQty = quantity + 1;
      setInputValue(newQty);
      onQuantityChange(item, newQty);
    }
  };

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
      {/* Producto */}
      <img src={image} alt={name} className="cart-item__image" loading='lazy'/>

      <div className="cart-item__info">
        <h3 className="cart-item__name">{name}</h3>
        <p className="cart-item__price">${price.toFixed(2)} MXN</p>
      </div>

      {/* Selector de cantidad */}
      <div className="cart-item__qty">
        <button
          className="btn btn--icon btn--sm"
          onClick={handleDecrement}
          disabled={quantity <= 1}
          aria-label="Disminuir cantidad"
        >
          −
        </button>

        <input
          type="number"
          className="input"
          value={inputValue}
          min="1"
          max={stock}
          onChange={handleInputChange}
          onBlur={handleInputBlur}
          onKeyDown={(e) => {
            if (e.key === '-' || e.key === 'e' || e.key === '.' || e.key === ',') e.preventDefault();
            if (e.key === 'Enter') e.target.blur();
          }}
          aria-label="Cantidad"
        />

        <button
          className="btn btn--icon btn--sm"
          onClick={handleIncrement}
          disabled={quantity >= stock}
          aria-label="Aumentar cantidad"
        >
          +
        </button>
      </div>

      {/* Total del item */}
      <p className="cart-item__price">${total}</p>

      {/* Botón remover */}
      <button
        className="btn btn--icon btn--danger btn--sm"
        onClick={() => onRemove(item)}
        aria-label="Eliminar item"
      >
        <FontAwesomeIcon icon={faTimes} />
      </button>
    </article>
  );
}