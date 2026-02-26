import { useState } from 'react';
import { useCart } from '../../context/CartContext';
import { useAuth } from '../../context/AuthContext';

const MESSAGE_TIMEOUT = 3000;
const SUCCESS_TIMEOUT = 2000;

export default function ProductCard({ product, onProductClick }) {
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');
  const [lastWasWarning, setLastWasWarning] = useState(false);

  const {
    product_id, image_url, name, category_id,
    stock_count, is_active, final_price, base_price
  } = product;

  const isAvailable = stock_count > 0 && is_active;
  const displayPrice = final_price !== null && final_price !== undefined ? final_price : base_price;
  const priceLabel = final_price !== null && final_price !== undefined ? 'Precio (IVA incluido)' : 'Precio base';

  // ── Quantity helpers (mirrors ModalProductDetails logic) ──────────────
  const handleQuantityChange = (delta) => {
    const newQty = quantity + delta;
    if (newQty >= 1 && newQty <= stock_count) setQuantity(newQty);
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    if (value === '') { setQuantity(''); return; }
    const newQty = Number(value);
    if (!isNaN(newQty) && newQty >= 1 && newQty <= stock_count) setQuantity(newQty);
  };

  const handleInputBlur = () => {
    if (quantity === '' || quantity < 1) setQuantity(1);
    else if (quantity > stock_count) setQuantity(stock_count);
    else setQuantity(Math.floor(Number(quantity)));
  };

  // ── Add to cart ───────────────────────────────────────────────────────
  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      setMessage('Inicia sesión para agregar productos');
      setTimeout(() => setMessage(''), MESSAGE_TIMEOUT);
      return;
    }
    try {
      setAdding(true);
      await addToCart(product_id, Number(quantity));
      setLastWasWarning(false);
      setMessage('¡Producto agregado!');
      setTimeout(() => setMessage(''), SUCCESS_TIMEOUT);
    } catch (error) {
      setLastWasWarning(!!error.isWarning);
      setMessage(error.message || 'Error al agregar producto');
      setTimeout(() => setMessage(''), MESSAGE_TIMEOUT);
    } finally {
      setAdding(false);
    }
  };

  return (
    <article className="product-card">
      <img
        src={image_url || '../../images/default-product.jpg'}
        alt={name}
        className="product-card__image"
      />

      <div className="product-card__info">
        <h3 className="product-card__name">{name}</h3>
        <p className="product-card__category">
          {product.category?.name ?? `Categoría ${product.category_id}`}
        </p>

        {displayPrice !== undefined && displayPrice !== null && (
          <div className="product-card__price-container">
            <p className="product-card__price">
              ${Number(displayPrice).toFixed(2)} MXN
            </p>
            {final_price !== undefined && (
              <small className="product-card__price-label">{priceLabel}</small>
            )}
          </div>
        )}

        <p className={`stock-badge ${isAvailable ? 'stock-badge--available' : 'stock-badge--out'}`}>
          {isAvailable ? (
            <>En stock: <strong>{stock_count} unidades</strong></>
          ) : (
            <>Agotado</>
          )}
        </p>

        {message && (
          <p className={`product-card__message${lastWasWarning ? ' product-card__message--warning' : ''}`}>
            {message}
          </p>
        )}

        {/* Quantity control – only shown when the product is available */}
        {isAvailable && (
          <div className="product-card__quantity-controls">
            <button
              className="btn btn--secondary btn--sm product-card__qty-btn"
              onClick={() => handleQuantityChange(-1)}
              disabled={quantity <= 1}
              aria-label="Disminuir cantidad"
            >
              −
            </button>

            <input
              className="input input--sm product-card__qty-input"
              type="number"
              value={quantity}
              onChange={handleInputChange}
              onBlur={handleInputBlur}
              onKeyDown={(e) => {
                if (['-', 'e', '.', ','].includes(e.key)) e.preventDefault();
              }}
              min="1"
              max={stock_count}
              aria-label="Cantidad"
            />

            <button
              className="btn btn--secondary btn--sm product-card__qty-btn"
              onClick={() => handleQuantityChange(1)}
              disabled={quantity >= stock_count}
              aria-label="Aumentar cantidad"
            >
              +
            </button>
          </div>
        )}

        <div className="product-card__buttons">
          <button
            className="btn btn--secondary btn--sm"
            onClick={() => onProductClick(product)}
          >
            Ver Detalles
          </button>

          <button
            className="btn btn--primary btn--sm"
            disabled={!isAvailable || adding}
            onClick={handleAddToCart}
          >
            {adding ? 'Agregando...' : 'Agregar al Carrito'}
          </button>
        </div>
      </div>
    </article>
  );
}