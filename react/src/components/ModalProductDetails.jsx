import { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function ModalProductDetails({ product, isOpen, onClose }) {
  const { addToCart } = useCart();
  const { isAuthenticated } = useAuth();
  const [quantity, setQuantity] = useState(1);
  const [adding, setAdding] = useState(false);
  const [message, setMessage] = useState('');

  if (!isOpen || !product) return null;

  const isAvailable = product.stock_count > 0 && product.is_active;

  const handleAddToCart = async () => {
    if (!isAuthenticated) {
      setMessage('Inicia sesión para agregar productos');
      setTimeout(() => setMessage(''), 3000);
      return;
    }

    try {
      setAdding(true);
      await addToCart(product.product_id, quantity);
      setMessage('¡Producto agregado al carrito!');
      setTimeout(() => {
        setMessage('');
        onClose();
      }, 1500);
    } catch (error) {
      setMessage('Error al agregar producto');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setAdding(false);
    }
  };

  const handleQuantityChange = (delta) => {
    const newQty = quantity + delta;
    if (newQty >= 1 && newQty <= product.stock_count) {
      setQuantity(newQty);
    }
  };

  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div className="modal-content modal-content--large" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>
        
        <div className="product-details">
          <div className="product-details__image">
            <img 
              src={product.image_url || '/images/default-product.jpg'} 
              alt={product.name}
            />
          </div>
          
          <div className="product-details__info">
            <h2 className="product-details__title">{product.name}</h2>
            <p className="product-details__sku">SKU: {product.sku}</p>
            
            <div className="product-details__price">
              ${Number(product.price).toFixed(2)}
            </div>
            
            <div className="product-details__stock">
              {isAvailable ? (
                <span className="stock-available">
                  ✓ En stock ({product.stock_count} unidades disponibles)
                </span>
              ) : (
                <span className="stock-unavailable">
                  ✗ Producto agotado
                </span>
              )}
            </div>
            
            <div className="product-details__description">
              <h3>Descripción</h3>
              <p>{product.description || 'Sin descripción disponible'}</p>
            </div>
            
            {isAvailable && (
              <div className="product-details__actions">
                <div className="quantity-selector">
                  <label>Cantidad:</label>
                  <div className="quantity-controls">
                    <button 
                      onClick={() => handleQuantityChange(-1)}
                      disabled={quantity <= 1}
                      className="qty-btn"
                    >
                      -
                    </button>
                    <span className="qty-display">{quantity}</span>
                    <button 
                      onClick={() => handleQuantityChange(1)}
                      disabled={quantity >= product.stock_count}
                      className="qty-btn"
                    >
                      +
                    </button>
                  </div>
                </div>
                
                {message && (
                  <div className={`message ${message.includes('Error') ? 'message--error' : 'message--success'}`}>
                    {message}
                  </div>
                )}
                
                <button
                  className="btn-add-to-cart"
                  onClick={handleAddToCart}
                  disabled={adding}
                >
                  {adding ? 'Agregando...' : 'Agregar al Carrito'}
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
