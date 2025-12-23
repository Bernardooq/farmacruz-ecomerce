/**
 * Cart.jsx
 * ========
 * Página del carrito de compras de FarmaCruz
 * 
 * Esta página permite a los clientes revisar su carrito, modificar
 * cantidades, eliminar productos y proceder con el checkout.
 * 
 * Funcionalidades:
 * - Ver items del carrito
 * - Modificar cantidades (con validación de stock)
 * - Eliminar productos del carrito
 * - Seleccionar dirección de envío
 * - Realizar checkout
 * - Ver resumen de precios y total
 * 
 * Permisos:
 * - Solo para clientes autenticados
 */

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

// ============================================
// CONSTANTES
// ============================================
const DEFAULT_ADDRESS = 'address_1';
const ERROR_DISPLAY_DURATION = 3000; // 3 segundos

export default function Cart() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { items, loading, updateQuantity, removeItem, checkout } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  // Estado de datos
  const [customerInfo, setCustomerInfo] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(DEFAULT_ADDRESS);

  // Estado de UI
  const [error, setError] = useState(null);
  const [processingCheckout, setProcessingCheckout] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Cargar información del cliente al montar el componente
   */
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

  // ============================================
  // EVENT HANDLERS
  // ============================================

  /**
   * Maneja el cambio de cantidad de un producto
   * Valida que no se exceda el stock disponible
   */
  const handleQuantityChange = async (item, newQty) => {
    // Validar cantidad mínima
    if (newQty < 1) return;

    // Validar disponibilidad de stock
    if (newQty > item.product.stock_count) {
      setError(`Solo hay ${item.product.stock_count} unidades disponibles de ${item.product.name}`);
      setTimeout(() => setError(null), ERROR_DISPLAY_DURATION);
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

  /**
   * Maneja la eliminación de un producto del carrito
   */
  const handleRemove = async (item) => {
    try {
      setError(null);
      await removeItem(item.cart_cache_id);
    } catch (err) {
      setError('Error al eliminar producto. Intenta de nuevo.');
      console.error('Failed to remove item:', err);
    }
  };

  /**
   * Abre el modal de confirmación de pedido
   */
  const handleCheckoutClick = () => {
    setShowConfirmModal(true);
  };

  /**
   * Procesa el checkout después de confirmar
   */
  const handleConfirmCheckout = async () => {
    try {
      setError(null);
      setShowConfirmModal(false);
      setProcessingCheckout(true);

      // Convertir selectedAddress a número (address_1 -> 1, address_2 -> 2, etc.)
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

  /**
   * Cierra el modal de confirmación
   */
  const handleCloseModal = () => {
    setShowConfirmModal(false);
  };

  /**
   * Navega a la página de productos
   */
  const handleGoToProducts = () => {
    navigate('/products');
  };

  // ============================================
  // HELPERS
  // ============================================

  /**
   * Verifica si el cliente tiene al menos una dirección registrada
   */
  const hasAnyAddress = () => {
    return customerInfo?.address_1 || customerInfo?.address_2 || customerInfo?.address_3;
  };

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return (
      <>
        <SearchBar />
        <LoadingSpinner message="Cargando carrito..." />
        <Footer />
      </>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <>
      <SearchBar />

      <main className="cart-page">
        <div className="container">
          {/* Mensaje de error si lo hay */}
          {error && (
            <ErrorMessage
              error={error}
              onDismiss={() => setError(null)}
            />
          )}

          {/* Estado: Carrito vacío */}
          {items.length === 0 ? (
            <div className="empty-cart">
              <p>Tu carrito está vacío</p>
              <button
                className="btn-primary"
                onClick={handleGoToProducts}
              >
                Ir a Productos
              </button>
            </div>
          ) : (
            /* Estado: Carrito con items */
            <div className="cart-layout">
              {/* Lista de productos en el carrito */}
              <CartItemList
                items={items}
                onQuantityChange={handleQuantityChange}
                onRemove={handleRemove}
              />

              {/* Resumen y botón de checkout */}
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

      {/* ============================================ */}
      {/* MODAL DE CONFIRMACIÓN DE PEDIDO             */}
      {/* ============================================ */}
      {showConfirmModal && (
        <div className="modal-overlay enable" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            {/* Botón de cerrar */}
            <button
              className="modal-close"
              onClick={handleCloseModal}
              aria-label="Cerrar modal"
            >
              &times;
            </button>

            {/* Header del modal */}
            <div className="modal-header">
              <h2>Confirmar Pedido</h2>
            </div>

            {/* Cuerpo del modal */}
            <div className="modal-body">
              <p className="confirm-message">
                ¿Desea confirmar su pedido?
              </p>

              {/* Selector de dirección de envío */}
              <div className="address-box">
                <p className="address-box__label">
                  Se enviará a:
                </p>

                {/* Dropdown para seleccionar dirección */}
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

                {/* Mostrar dirección seleccionada */}
                <p className="address-box__address" style={{ marginTop: '0.5rem' }}>
                  {customerInfo?.[selectedAddress] || 'Sin dirección registrada'}
                </p>
              </div>

              {/* Advertencia si no hay direcciones */}
              {!hasAnyAddress() && (
                <p className="address-warning">
                  Por favor, actualiza tu dirección en tu perfil antes de continuar
                </p>
              )}
            </div>

            {/* Footer del modal con botones */}
            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={handleCloseModal}
              >
                Cancelar
              </button>
              <button
                className="btn-primary"
                onClick={handleConfirmCheckout}
                disabled={!hasAnyAddress() || processingCheckout}
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