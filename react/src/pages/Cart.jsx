import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { userService } from '../services/userService';
import SearchBar from '../layout/SearchBar';
import Footer from '../layout/Footer';
import CartItemList from '../components/CartItemList';
import CartSummary from '../components/CartSummary';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';

export default function Cart() {
  const { items, loading, updateQuantity, removeItem, checkout } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState(null);
  const [processingCheckout, setProcessingCheckout] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [customerInfo, setCustomerInfo] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState('address_1'); // Default to address_1

  // Cargar información del cliente al montar
  useEffect(() => {
    const loadCustomerInfo = async () => {
      try {
        const data = await userService.getCurrentUserCustomerInfo();
        setCustomerInfo(data);
      } catch (err) {
        console.error('Error loading customer info:', err);
      }
    };

    if (user) {
      loadCustomerInfo();
    }
  }, [user]);

  const handleQuantityChange = async (item, newQty) => {
    if (newQty < 1) return;

    // Validate stock availability
    if (newQty > item.product.stock_count) {
      setError(`Solo hay ${item.product.stock_count} unidades disponibles de ${item.product.name}`);
      setTimeout(() => setError(null), 3000);
      return;
    }

    try {
      setError(null);
      await updateQuantity(item.cart_cache_id, newQty);
    } catch (err) {
      setError('Error al actualizar cantidad. Intenta de nuevo.');
      console.error('Failed to update quantity:', err);
    }
  };

  const handleRemove = async (item) => {
    try {
      setError(null);
      await removeItem(item.cart_cache_id);
    } catch (err) {
      setError('Error al eliminar producto. Intenta de nuevo.');
      console.error('Failed to remove item:', err);
    }
  };

  const handleCheckoutClick = () => {
    setShowConfirmModal(true);
  };

  const handleConfirmCheckout = async () => {
    try {
      setError(null);
      setShowConfirmModal(false);
      setProcessingCheckout(true);

      // Convert selected address to number (address_1 -> 1, address_2 -> 2, address_3 -> 3)
      const addressNumber = parseInt(selectedAddress.replace('address_', ''));

      await checkout(addressNumber);
      navigate('/profile');
    } catch (err) {
      setError('Error al procesar el pedido. Intenta de nuevo.');
      console.error('Checkout failed:', err);
    } finally {
      setProcessingCheckout(false);
    }
  };

  if (loading) {
    return (
      <>
        <SearchBar />
        <LoadingSpinner message="Cargando carrito..." />
        <Footer />
      </>
    );
  }

  return (
    <>
      <SearchBar />
      <main className="cart-page">
        <div className="container">
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          {items.length === 0 ? (
            <div className="empty-cart">
              <p>Tu carrito está vacío</p>
              <button
                className="btn-primary"
                onClick={() => navigate('/products')}
              >
                Ir a Productos
              </button>
            </div>
          ) : (
            <div className="cart-layout">
              <CartItemList
                items={items}
                onQuantityChange={handleQuantityChange}
                onRemove={handleRemove}
              />
              <CartSummary
                items={items}
                onCheckout={handleCheckoutClick}
                processingCheckout={processingCheckout}
              />
            </div>
          )}
        </div>
      </main>
      <Footer />

      {/* Modal de confirmacion */}
      {showConfirmModal && (
        <div className="modal-overlay enable" onClick={() => setShowConfirmModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button
              className="modal-close"
              onClick={() => setShowConfirmModal(false)}
              aria-label="Cerrar modal"
            >
              &times;
            </button>

            <div className="modal-header">
              <h2>Confirmar Pedido</h2>
            </div>

            <div className="modal-body">
              <p className="confirm-message">
                ¿Desea confirmar su pedido?
              </p>

              <div className="address-box">
                <p className="address-box__label">
                  Se enviará a:
                </p>

                {/* Address selector */}
                <select
                  value={selectedAddress}
                  onChange={(e) => setSelectedAddress(e.target.value)}
                  className="address-selector"
                  style={{
                    width: '100%',
                    padding: '0.75rem',
                    marginBottom: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid #ddd',
                    fontSize: '1rem'
                  }}
                >
                  {customerInfo?.address_1 && (
                    <option value="address_1">
                      Dirección 1: {customerInfo.address_1}
                    </option>
                  )}
                  {customerInfo?.address_2 && (
                    <option value="address_2">
                      Dirección 2: {customerInfo.address_2}
                    </option>
                  )}
                  {customerInfo?.address_3 && (
                    <option value="address_3">
                      Dirección 3: {customerInfo.address_3}
                    </option>
                  )}
                </select>

                {/* Show selected address */}
                <p className="address-box__address" style={{ marginTop: '0.5rem' }}>
                  {customerInfo?.[selectedAddress] || 'Sin dirección registrada'}
                </p>
              </div>

              {!customerInfo?.address_1 && !customerInfo?.address_2 && !customerInfo?.address_3 && (
                <p className="address-warning">
                  Por favor, actualiza tu dirección en tu perfil antes de continuar
                </p>
              )}
            </div>

            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => setShowConfirmModal(false)}
              >
                Cancelar
              </button>
              <button
                className="btn-primary"
                onClick={handleConfirmCheckout}
                disabled={
                  (!customerInfo?.address_1 && !customerInfo?.address_2 && !customerInfo?.address_3) ||
                  processingCheckout
                }
              >
                {processingCheckout ? 'Procesando...' : 'Confirmar Pedido'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}