import { useState, useEffect } from 'react';
import { useCart } from '../../../context/CartContext';
import { useAuth } from '../../../context/AuthContext';
import SimilarProducts from '../../products/SimilarProducts';

const MESSAGE_TIMEOUT = 3000;
const SUCCESS_CLOSE_DELAY = 1500;
const WARNING_TIMEOUT = 4000;

export default function ModalProductDetails({ product, isOpen, onClose, onProductSelect }) {
  const { addToCart, items } = useCart();
  const { isAuthenticated } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => { if (isOpen) { setQuantity(1); setMessage(''); setAdding(false); } }, [isOpen]);

  if (!isOpen || !product) return null;

  const isAvailable = product.stock_count > 0 && product.is_active;
  const existingItem = items.find(item => item.product?.product_id === product.product_id);
  const currentQuantityInCart = existingItem ? existingItem.quantity : 0;

  const handleAddToCart = async () => {
    if (adding) return;
    if (!isAuthenticated) { setMessage('Inicia sesión para agregar productos'); setTimeout(() => setMessage(''), MESSAGE_TIMEOUT); return; }
    try {
      setAdding(true); await addToCart(product.product_id, Number(quantity));
      setMessage('¡Producto agregado al carrito!');
      setTimeout(() => { setMessage(''); onClose(); }, SUCCESS_CLOSE_DELAY);
    } catch (error) {
      setMessage(error.isWarning ? error.message : error.message || 'Error al agregar producto');
      setTimeout(() => setMessage(''), WARNING_TIMEOUT);
    } finally { setAdding(false); }
  };

  const handleQuantityChange = (delta) => { const newQty = quantity + delta; if (newQty >= 1 && newQty <= product.stock_count) setQuantity(newQty); };

  const handleInputChange = (e) => {
    const value = e.target.value; if (value === '') { setQuantity(''); return; }
    const newQty = Number(value); if (!isNaN(newQty) && newQty >= 1 && newQty <= product.stock_count) setQuantity(newQty);
  };

  const handleInputBlur = () => {
    if (quantity === '' || quantity < 1) setQuantity(1);
    else if (quantity > product.stock_count) setQuantity(product.stock_count);
    else setQuantity(Math.floor(Number(quantity)));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal modal--lg" onClick={(e) => e.stopPropagation()}>
        <div className="modal__header">
          <h2>{product.name}</h2>
          <button className="modal__close" onClick={onClose} aria-label="Cerrar modal">&times;</button>
        </div>
        <div className="modal__body modal__body--scroll">
          <div className="product-details">
            <div className="product-details__image">
              <img src={product.image_url || '../../../images/default-product.jpg'} loading='lazy' alt={product.name} />
            </div>
            <div className="product-details__info">
              <div>
                <span className="product-details__codebar">Codigo: {product.codebar}</span>
              </div>
              <div className="product-details__price">${Number(product.final_price || product.base_price || 0).toFixed(2)} MXN</div>

              <div className={`stock-badge ${isAvailable ? 'stock-badge--in-stock' : 'stock-badge--out-of-stock'}`}>
                {isAvailable ? (
                  <>
                    <span>✓ En stock ({product.stock_count} unidades disponibles)</span>
                    {currentQuantityInCart > 0 && (<span className="stock-badge__cart-info">Ya tienes {currentQuantityInCart} en tu carrito</span>)}
                  </>
                ) : (<span>✗ Producto agotado</span>)}
              </div>

              <div className="product-details__description">
                <h3>Descripción</h3>
                {product.costo_publico && <p><strong>Costo Público:</strong> ${product.costo_publico}</p>}
                <p>{product.description || 'Sin descripción disponible'}</p>
                {product.descripcion_2 && <p>{product.descripcion_2}</p>}
              </div>

              {isAvailable && (
                <div className="product-details__actions">
                  <div className="quantity-selector">
                    <label className="form-group__label">Cantidad:</label>
                    <div className="quantity-controls">
                      <button className="btn btn--secondary btn--sm" onClick={() => handleQuantityChange(-1)} disabled={quantity <= 1} aria-label="Disminuir cantidad">-</button>
                      <input className="input input--sm" type="number" value={quantity} onChange={handleInputChange} onBlur={handleInputBlur} min="1" max={product.stock_count}
                        onKeyDown={(e) => { if (['-', 'e', '.', ','].includes(e.key)) e.preventDefault(); }}
                        aria-label="Cantidad" style={{ width: '60px', textAlign: 'center' }}
                      />
                      <button className="btn btn--secondary btn--sm" onClick={() => handleQuantityChange(1)} disabled={quantity >= product.stock_count} aria-label="Aumentar cantidad">+</button>
                    </div>
                  </div>

                  {message && (
                    <div className={`alert ${message.includes('Error') ? 'alert--danger' : 'alert--success'}`}>{message}</div>
                  )}

                  <button className="btn btn--primary btn--block" onClick={handleAddToCart} disabled={adding}>
                    {adding ? 'Agregando...' : 'Agregar al Carrito'}
                  </button>
                </div>
              )}
            </div>
          </div>

          <SimilarProducts productId={product.product_id} onProductSelect={onProductSelect} />
        </div>
      </div>
    </div>
  );
}
