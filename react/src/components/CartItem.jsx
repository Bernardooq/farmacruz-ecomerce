import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faTimes } from '@fortawesome/free-solid-svg-icons';

export default function CartItem({ item, onQuantityChange, onRemove }) {
  // Extract data from backend structure
  const product = item.product || {};
  const image = product.image_url || '';
  const name = product.name || 'Producto';
  const price = item.price_at_addition || product.price || 0;
  const quantity = item.quantity || 1;
  const stock = product.stock_count || 0;
  
  // Auto-remove if out of stock
  if (stock < 1) {
    onRemove(item);
  }
  
  const total = (price * quantity).toFixed(2);

  const handleInputChange = (e) => {
    const newQty = Number(e.target.value);
    if (newQty >= 1 && newQty <= stock) {
      onQuantityChange(item, newQty);
    }
  };

  const handleInputBlur = (e) => {
    const value = Number(e.target.value);

    if (stock < 1) {
      onRemove(item);
    } else if (!value || isNaN(value) || value < 1) {
      onQuantityChange(item, 1);
    } else if (value > stock) {
      onQuantityChange(item, stock);
    }
  };

  const handleIncrement = () => {
    if (quantity < stock) {
      onQuantityChange(item, quantity + 1);
    }
  };

  const handleDecrement = () => {
    if (quantity > 1) {
      onQuantityChange(item, quantity - 1);
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
            value={quantity}
            min="1"
            max={stock}
            onChange={handleInputChange}
            onBlur={handleInputBlur}
            onKeyDown={(e) => {
              if (e.key === '-' || e.key === 'e') e.preventDefault();
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