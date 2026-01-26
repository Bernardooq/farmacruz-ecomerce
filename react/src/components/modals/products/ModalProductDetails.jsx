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

  // Resetear estado al abrir el modal
  useEffect(() => {
    if (isOpen) {
      setQuantity(1);
      setMessage('');
      setAdding(false);
    }
  }, [isOpen]);


  if (!isOpen || !product) return null;

  const isAvailable = product.stock_count > 0 && product.is_active;

  // Calcular cuántas unidades ya tiene en el carrito
  const existingItem = items.find(item => item.product?.product_id === product.product_id);
  const currentQuantityInCart = existingItem ? existingItem.quantity : 0;

  /**
   * Maneja la adición del producto al carrito
   * Incluye validación de autenticación y prevención de doble-click
   */
  const handleAddToCart = async () => {
    // Prevenir doble click
    if (adding) return;

    if (!isAuthenticated) {
      setMessage('Inicia sesión para agregar productos');
      setTimeout(() => setMessage(''), MESSAGE_TIMEOUT);
      return;
    }

    try {
      setAdding(true);
      await addToCart(product.product_id, Number(quantity));
      setMessage('¡Producto agregado al carrito!');
      setTimeout(() => {
        setMessage('');
        onClose();
      }, SUCCESS_CLOSE_DELAY);
    } catch (error) {
      // Si es una advertencia (se agregó pero con límite), mostrar como información
      if (error.isWarning) {
        setMessage(error.message);
      } else {
        setMessage(error.message || 'Error al agregar producto');
      }
      setTimeout(() => setMessage(''), WARNING_TIMEOUT);
    } finally {
      setAdding(false);
    }
  };

  /**
   * Incrementa o decrementa la cantidad
   */
  const handleQuantityChange = (delta) => {
    const newQty = quantity + delta;
    if (newQty >= 1 && newQty <= product.stock_count) {
      setQuantity(newQty);
    }
  };

  /**
   * Maneja cambios en el input de cantidad
   */
  const handleInputChange = (e) => {
    const value = e.target.value;
    if (value === '') {
      setQuantity('');
      return;
    }

    const newQty = Number(value);
    if (!isNaN(newQty) && newQty >= 1 && newQty <= product.stock_count) {
      setQuantity(newQty);
    }
  };

  /**
   * Valida y corrige la cantidad cuando el input pierde el foco
   */
  const handleInputBlur = () => {
    if (quantity === '' || quantity < 1) {
      setQuantity(1);
    } else if (quantity > product.stock_count) {
      setQuantity(product.stock_count);
    } else {
      setQuantity(Math.floor(Number(quantity)));
    }
  };

  // Render del modal
  return (
    <div className="modal-overlay enable" onClick={onClose}>
      <div
        className="modal-content modal-content--large"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Botón cerrar */}
        <button className="modal-close" onClick={onClose} aria-label="Cerrar modal">
          &times;
        </button>

        {/* Wrapper con scroll para todo el contenido */}
        <div style={{ maxHeight: '85vh', overflowY: 'auto', padding: '1rem' }}>
          <div className="product-details">
            {/* Imagen del producto */}
            <div className="product-details__image">
              <img
                src={product.image_url || '../../../images/default-product.jpg'}
                alt={product.name}
              />
            </div>

            {/* Información del producto */}
            <div className="product-details__info">
              <h2 className="product-details__title">
                {product.name}
              </h2>

              <p className="product-details__codebar">
                Codifo de barras: {product.codebar}
              </p>

              <div className="product-details__price">
                ${Number(product.final_price || product.base_price || 0).toFixed(2)} MXN
              </div>

              {/* Estado de stock */}
              <div className={`product-details__stock ${isAvailable ? 'product-details__stock--available' : 'product-details__stock--unavailable'}`}>
                {isAvailable ? (
                  <>
                    <span className="stock-available">
                      ✓ En stock ({product.stock_count} unidades disponibles)
                    </span>
                    {currentQuantityInCart > 0 && (
                      <span className="stock-in-cart">
                        Ya tienes {currentQuantityInCart} en tu carrito
                      </span>
                    )}
                  </>
                ) : (
                  <span className="stock-unavailable">
                    ✗ Producto agotado
                  </span>
                )}
              </div>

              {/* Descripción */}
              <div className="product-details__description">
                <h3>Descripción</h3>
                <p>
                  {product.description || 'Sin descripción disponible'}
                </p>
                <br />
                {product.descripcion_2 && (
                  <p>
                    {product.descripcion_2}
                  </p>
                )}
              </div>

              {/* Acciones (solo si está disponible) */}
              {isAvailable && (
                <div className="product-details__actions">
                  {/* Selector de cantidad */}
                  <div className="quantity-selector">
                    <label>Cantidad:</label>
                    <div className="quantity-controls">
                      <button
                        onClick={() => handleQuantityChange(-1)}
                        disabled={quantity <= 1}
                        className="qty-btn"
                        aria-label="Disminuir cantidad"
                      >
                        -
                      </button>

                      <input
                        type="number"
                        className="qty-input"
                        value={quantity}
                        onChange={handleInputChange}
                        onBlur={handleInputBlur}
                        min="1"
                        max={product.stock_count}
                        onKeyDown={(e) => {
                          if (e.key === '-' || e.key === 'e' || e.key === '.' || e.key === ',') {
                            e.preventDefault();
                          }
                        }}
                        aria-label="Cantidad"
                      />

                      <button
                        onClick={() => handleQuantityChange(1)}
                        disabled={quantity >= product.stock_count}
                        className="qty-btn"
                        aria-label="Aumentar cantidad"
                      >
                        +
                      </button>
                    </div>
                  </div>

                  {/* Mensaje de feedback */}
                  {message && (
                    <div className={`message ${message.includes('Error') ? 'message--error' : 'message--success'}`}>
                      {message}
                    </div>
                  )}

                  {/* Botón agregar al carrito */}
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

          {/* Productos Similares */}
          <SimilarProducts
            productId={product.product_id}
            onProductSelect={onProductSelect}
          />
        </div>
      </div>
    </div>
  );
}
