/**
 * Cart.jsx
 * ========
 * Página del carrito de compras de FarmaCruz
 * 
 * Funcionalidades:
 * - Ver items del carrito
 * - Modificar cantidades (con validación de stock)
 * - Eliminar productos del carrito
 * - Seleccionar dirección de envío
 * - Realizar checkout
 * - Ver resumen de precios y total
 * 
 * Permisos: Solo para clientes autenticados
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { userService } from '../services/userService';
import SearchBar from '../components/layout/SearchBar';
import Footer from '../components/layout/Footer';
import CartItemList from '../components/cart/CartItemList';
import CartSummary from '../components/cart/CartSummary';
import HelpGuide from '../components/common/HelpGuide';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

// ============================================
// CONSTANTES
// ============================================
const DEFAULT_ADDRESS = 'address_1';
const ERROR_DISPLAY_DURATION = 3000;

export default function Cart() {
  // ============================================
  // HOOKS & STATE
  // ============================================
  const { items, loading, updateQuantity, removeItem, checkout, refreshCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [customerInfo, setCustomerInfo] = useState(null);
  const [selectedAddress, setSelectedAddress] = useState(DEFAULT_ADDRESS);
  const [error, setError] = useState(null);
  const [processingCheckout, setProcessingCheckout] = useState(false);
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [orderNotes, setOrderNotes] = useState('');

  // ============================================
  // EFFECTS
  // ============================================
  useEffect(() => {
    const loadCustomerInfo = async () => {
      try {
        const data = await userService.getCurrentUserCustomerInfo();
        setCustomerInfo(data);
      } catch (err) {
        console.error('Error loading customer info:', err);
      }
    };
    if (user) loadCustomerInfo();
  }, [user]);

  // ============================================
  // EVENT HANDLERS
  // ============================================
  const handleQuantityChange = async (item, newQty) => {
    if (newQty < 1) return;
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
      const addressNumber = parseInt(selectedAddress.replace('address_', ''));
      await checkout(addressNumber, orderNotes);
      navigate('/profile');
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message || 'Error al procesar el pedido. Intenta de nuevo.';

      // Si el backend rechaza por problemas de inventario
      if (errorMsg.toLowerCase().includes('stock')) {
        setError(`⚠️ ${errorMsg}. Hemos recargado tu carrito con el inventario actual. Por favor, revisa y ajusta las cantidades rojas antes de reintentar.`);
        refreshCart(); // Forzamos recarga desde el backend para que los items limiten su "maxQty" a la nueva realidad
      } else {
        setError(errorMsg);
      }
      console.error('Checkout failed:', err);
    } finally {
      setProcessingCheckout(false);
    }
  };

  const handleCloseModal = () => setShowConfirmModal(false);
  const handleGoToProducts = () => navigate('/products');

  const hasAnyAddress = () => customerInfo?.address_1 || customerInfo?.address_2 || customerInfo?.address_3;

  // ============================================
  // RENDER - LOADING STATE
  // ============================================
  if (loading) {
    return (
      <div className="page">
        <SearchBar />
        <LoadingSpinner message="Cargando carrito..." />
        <Footer />
      </div>
    );
  }

  // ============================================
  // RENDER - MAIN CONTENT
  // ============================================
  return (
    <div className="page">
      <SearchBar />

      <main className="page__content">
        <div className="page-container">
          <div className="d-flex items-center justify-between mb-6">
            <h1 className="section-title">Mi Carrito</h1>
            <HelpGuide
              title="Guía del Carrito"
              items={[
                "Cantidades: Puedes aumentar o disminuir la cantidad de cada producto. El sistema validará automáticamente si hay stock suficiente.",
                "Eliminar: Haz clic en el icono de bote de basura si ya no deseas un producto.",
                "Dirección: Al finalizar el pedido, podrás elegir entre tus direcciones registradas.",
                "Pagos: Una vez realizado el pago de tu pedido, este será validado y enviado. Puedes contactar a tu agente de marketing asignado para acelerar el proceso o simplemente esperar a que nuestro equipo te contacte.",
                "Finalizar: Haz clic en 'Finalizar Pedido' para enviar tu orden y recibir las instrucciones de pago.",
                "Notas: Puedes agregar comentarios especiales a tu pedido (ej: fechas de caducidad específicas)."
              ]}
            />
          </div>

          {/* Mensaje de error */}
          {error && <ErrorMessage error={error} onDismiss={() => setError(null)} />}

          {/* Estado: Carrito vacío */}
          {items.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state__icon">🛒</div>
              <p className="empty-state__text mb-4">Tu carrito está vacío</p>
              <button className="btn btn--primary" onClick={handleGoToProducts}>
                Ir a Productos
              </button>
            </div>
          ) : (
            /* Estado: Carrito con items */
            <div className="cart">
              <div className="cart__items">
                <CartItemList
                  items={items}
                  onQuantityChange={handleQuantityChange}
                  onRemove={handleRemove}
                />
              </div>
              <div className="cart__summary">
                <CartSummary
                  items={items}
                  onCheckout={handleCheckoutClick}
                  processingCheckout={processingCheckout}
                />
              </div>
            </div>
          )}
        </div>
      </main>

      <Footer />

      {/* ============================================ */}
      {/* MODAL DE CONFIRMACIÓN DE PEDIDO             */}
      {/* ============================================ */}
      {showConfirmModal && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal modal--sm" onClick={(e) => e.stopPropagation()}>
            {/* Header del modal */}
            <div className="modal__header">
              <h2>Confirmar Pedido</h2>
              <button className="modal__close" onClick={handleCloseModal} aria-label="Cerrar modal">
                &times;
              </button>
            </div>

            {/* Cuerpo del modal */}
            <div className="modal__body">
              <p className="text-center mb-4">¿Desea confirmar su pedido?</p>

              {/* Selector de dirección de envío */}
              <div className="form-group">
                <label className="form-group__label">Se enviará a:</label>
                <select
                  value={selectedAddress}
                  onChange={(e) => setSelectedAddress(e.target.value)}
                  className="select"
                >
                  {customerInfo?.address_1 && (
                    <option value="address_1">Dirección 1: {customerInfo.address_1}</option>
                  )}
                  {customerInfo?.address_2 && (
                    <option value="address_2">Dirección 2: {customerInfo.address_2}</option>
                  )}
                  {customerInfo?.address_3 && (
                    <option value="address_3">Dirección 3: {customerInfo.address_3}</option>
                  )}
                </select>

                <p className="form-group__hint mt-2">
                  {customerInfo?.[selectedAddress] || 'Sin dirección registrada'}
                </p>
              </div>

              {/* Campo de notas del pedido (para el cliente) */}
              <div className="form-group mt-4">
                <label className="form-group__label" htmlFor="order-notes">
                  Notas del Pedido <span style={{ fontWeight: 400, opacity: 0.65 }}>(Opcional)</span>
                </label>
                <textarea
                  id="order-notes"
                  className="input"
                  rows={3}
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Ej: Quiero productos de lotes recientes, o favor de revisar fechas de caducidad..."
                  style={{ resize: 'vertical', minHeight: '72px' }}
                />
              </div>

              {/* Advertencia si no hay direcciones */}
              {!hasAnyAddress() && (
                <div className="alert alert--warning mt-4">
                  Por favor, actualiza tu dirección en tu perfil antes de continuar
                </div>
              )}
            </div>

            {/* Footer del modal */}
            <div className="modal__footer">
              <button className="btn btn--secondary" onClick={handleCloseModal}>
                Cancelar
              </button>
              <button
                className="btn btn--primary"
                onClick={handleConfirmCheckout}
                disabled={!hasAnyAddress() || processingCheckout}
              >
                {processingCheckout ? 'Procesando...' : 'Confirmar Pedido'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}