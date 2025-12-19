import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';

export default function CartItem({ item, onQuantityChange, onRemove }) {
  // Extract data from backend structure
  const product = item.product || {};
  const image = product.image_url || '';
  const name = product.name || 'Producto';

  // Backend already calculated final_price with markup + IVA
  const price = product.final_price || product.base_price || 0;

  const quantity = item.quantity || 1;
  const stock = product.stock_count || 0;

  // Estado local para el input (permite escribir sin validar)
  const [inputValue, setInputValue] = useState(quantity);

  // Sincronizar inputValue cuando quantity cambie desde afuera
  if (inputValue !== quantity && document.activeElement?.type !== 'number') {
    setInputValue(quantity);
  }

  // Auto-remove if out of stock
  if (stock < 1) {
    onRemove(item);
  }

  const total = (price * quantity).toFixed(2);

  const handleInputChange = (e) => {
    // Solo actualizar el valor local, NO validar ni llamar onQuantityChange
    setInputValue(e.target.value);
  };

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
      // Usar el valor válido
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

  return (
    <article className="cart-item">
      <div className="cart-item__product">
        <img src={image} alt={name} className="cart-item__image" />
        <div className="cart-item__details">
          <h3 className="cart-item__name">{name}</h3>
          <p className="cart-item__price">${price.toFixed(2)} MXN</p>
        </div>
      </div>

      <div className="cart-item__quantity">
        <div className="quantity-selector">
          <button
            className="quantity-selector__btn"
            onClick={handleDecrement}
            disabled={quantity <= 1}
          >
            -
          </button>

          <input
            type="number"
            value={inputValue}
            min="1"
            max={stock}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={(e) => {
              if (e.key === '-' || e.key === 'e' || e.key === '.' || e.key === ',') {
                e.preventDefault();
              }
              // Enter tambien aplica el cambio
              if (e.key === 'Enter') {
                e.target.blur();
              }
            }}
          />

          <button
            className="quantity-selector__btn"
            onClick={handleIncrement}
            disabled={quantity >= stock}
          >
            +
          </button>
        </div>
      </div>

      <p className="cart-item__total">${total}</p>

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