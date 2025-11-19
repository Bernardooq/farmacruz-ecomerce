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
      <div 
        className="modal-content modal-content--large" 
        onClick={(e) => e.stopPropagation()}
        style={{
          maxWidth: '900px',
          width: '90%',
          maxHeight: '90vh',
          overflow: 'auto'
        }}
      >
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>
        
        <div 
          className="product-details"
          style={{
            display: 'grid',
            gridTemplateColumns: window.innerWidth > 768 ? '1fr 1fr' : '1fr',
            gap: '30px',
            padding: '20px'
          }}
        >
          <div 
            className="product-details__image"
            style={{
              width: '100%',
              maxWidth: '400px',
              margin: window.innerWidth <= 768 ? '0 auto' : '0'
            }}
          >
            <img 
              src={product.image_url || '/images/default-product.jpg'} 
              alt={product.name}
              style={{
                width: '100%',
                height: 'auto',
                borderRadius: '8px',
                objectFit: 'cover'
              }}
            />
          </div>
          
          <div className="product-details__info">
            <h2 
              className="product-details__title"
              style={{
                fontSize: window.innerWidth <= 768 ? '1.5rem' : '2rem',
                marginBottom: '10px'
              }}
            >
              {product.name}
            </h2>
            <p 
              className="product-details__sku"
              style={{
                color: '#7f8c8d',
                fontSize: '0.9rem',
                marginBottom: '15px'
              }}
            >
              SKU: {product.sku}
            </p>
            
            <div 
              className="product-details__price"
              style={{
                fontSize: window.innerWidth <= 768 ? '1.8rem' : '2.5rem',
                fontWeight: 'bold',
                color: '#27ae60',
                marginBottom: '15px'
              }}
            >
              ${Number(product.price).toFixed(2)} MXN
            </div>
            
            <div 
              className="product-details__stock"
              style={{
                marginBottom: '20px',
                padding: '10px',
                borderRadius: '5px',
                backgroundColor: isAvailable ? '#d4edda' : '#f8d7da'
              }}
            >
              {isAvailable ? (
                <span 
                  className="stock-available"
                  style={{
                    color: '#155724',
                    fontWeight: 'bold'
                  }}
                >
                  ✓ En stock ({product.stock_count} unidades disponibles)
                </span>
              ) : (
                <span 
                  className="stock-unavailable"
                  style={{
                    color: '#721c24',
                    fontWeight: 'bold'
                  }}
                >
                  ✗ Producto agotado
                </span>
              )}
            </div>
            
            <div 
              className="product-details__description"
              style={{
                marginBottom: '25px',
                lineHeight: '1.6'
              }}
            >
              <h3 style={{ marginBottom: '10px', fontSize: '1.2rem' }}>Descripción</h3>
              <p style={{ color: '#555' }}>
                {product.description || 'Sin descripción disponible'}
              </p>
            </div>
            
            {isAvailable && (
              <div 
                className="product-details__actions"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '15px'
                }}
              >
                <div 
                  className="quantity-selector"
                  style={{
                    display: 'flex',
                    flexDirection: window.innerWidth <= 768 ? 'column' : 'row',
                    alignItems: window.innerWidth <= 768 ? 'stretch' : 'center',
                    gap: '10px'
                  }}
                >
                  <label style={{ fontWeight: 'bold' }}>Cantidad:</label>
                  <div 
                    className="quantity-controls"
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '10px',
                      justifyContent: window.innerWidth <= 768 ? 'center' : 'flex-start'
                    }}
                  >
                    <button 
                      onClick={() => handleQuantityChange(-1)}
                      disabled={quantity <= 1}
                      className="qty-btn"
                      style={{
                        width: '40px',
                        height: '40px',
                        fontSize: '1.5rem',
                        border: '1px solid #ddd',
                        borderRadius: '5px',
                        backgroundColor: quantity <= 1 ? '#f0f0f0' : '#fff',
                        cursor: quantity <= 1 ? 'not-allowed' : 'pointer'
                      }}
                    >
                      -
                    </button>
                    <span 
                      className="qty-display"
                      style={{
                        fontSize: '1.2rem',
                        fontWeight: 'bold',
                        minWidth: '40px',
                        textAlign: 'center'
                      }}
                    >
                      {quantity}
                    </span>
                    <button 
                      onClick={() => handleQuantityChange(1)}
                      disabled={quantity >= product.stock_count}
                      className="qty-btn"
                      style={{
                        width: '40px',
                        height: '40px',
                        fontSize: '1.5rem',
                        border: '1px solid #ddd',
                        borderRadius: '5px',
                        backgroundColor: quantity >= product.stock_count ? '#f0f0f0' : '#fff',
                        cursor: quantity >= product.stock_count ? 'not-allowed' : 'pointer'
                      }}
                    >
                      +
                    </button>
                  </div>
                </div>
                
                {message && (
                  <div 
                    className={`message ${message.includes('Error') ? 'message--error' : 'message--success'}`}
                    style={{
                      padding: '10px',
                      borderRadius: '5px',
                      textAlign: 'center',
                      backgroundColor: message.includes('Error') ? '#f8d7da' : '#d4edda',
                      color: message.includes('Error') ? '#721c24' : '#155724',
                      fontWeight: 'bold'
                    }}
                  >
                    {message}
                  </div>
                )}
                
                <button
                  className="btn-add-to-cart"
                  onClick={handleAddToCart}
                  disabled={adding}
                  style={{
                    padding: '15px 30px',
                    fontSize: '1.1rem',
                    fontWeight: 'bold',
                    backgroundColor: adding ? '#95a5a6' : '#3498db',
                    color: 'white',
                    border: 'none',
                    borderRadius: '5px',
                    cursor: adding ? 'not-allowed' : 'pointer',
                    transition: 'background-color 0.3s'
                  }}
                  onMouseEnter={(e) => {
                    if (!adding) e.target.style.backgroundColor = '#2980b9';
                  }}
                  onMouseLeave={(e) => {
                    if (!adding) e.target.style.backgroundColor = '#3498db';
                  }}
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
