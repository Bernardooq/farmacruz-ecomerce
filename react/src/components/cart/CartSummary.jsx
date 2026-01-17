/**
 * CartSummary.jsx
 * ===============
 * Componente de resumen del carrito de compras
 * 
 * Muestra un resumen del pedido con subtotal, envío y total estimado.
 * Incluye el botón de checkout para proceder con el pedido.
 * 
 * Props:
 * @param {Array} items - Array de items del carrito
 * @param {function} onCheckout - Callback para proceder al checkout
 * @param {boolean} processingCheckout - Estado de procesamiento (default: false)
 * 
 * Cálculo de precios:
 * - Usa final_price del backend (incluye IVA y descuentos)
 * - Fallback a base_price si final_price no está disponible
 * - Envío se calcula después (no incluido en este componente)
 * 
 * Características:
 * - Suma automática de todos los items
 * - Botón deshabilitado cuando está procesando o carrito vacío
 * - Formato de moneda con 2 decimales
 * 
 * Uso:
 * <CartSummary
 *   items={cartItems}
 *   onCheckout={handleCheckout}
 *   processingCheckout={isProcessing}
 * />
 */

export default function CartSummary({
  items,
  onCheckout,
  processingCheckout = false
}) {
  // ============================================
  // CALCULATIONS
  // ============================================

  /**
   * Calcula el subtotal sumando todos los items
   * Usa final_price del backend que ya incluye IVA
   */
  const subtotal = items.reduce((sum, item) => {
    const product = item.product || {};
    // Backend already calculated final_price
    const price = product.final_price || product.base_price || 0;
    return sum + price * item.quantity;
  }, 0).toFixed(2);

  // ============================================
  // RENDER
  // ============================================
  return (
    <aside className="cart-summary">
      <h2 className="cart-summary__title">Resumen del Pedido</h2>

      {/* Subtotal */}
      <div className="summary-row">
        <span>Subtotal:</span>
        <span>${subtotal}</span>
      </div>

      {/* Envío (calculado después) */}
      <div className="summary-row">
        <span>Envío:</span>
        <span>A calcular</span>
      </div>

      <hr />

      {/* Total Estimado */}
      <div className="summary-row total">
        <span>Total Estimado:</span>
        <span>${subtotal}</span>
      </div>

      {/* Botón de Checkout */}
      <button
        className="btn-checkout"
        onClick={onCheckout}
        disabled={processingCheckout || items.length === 0}
      >
        {processingCheckout ? 'Procesando...' : 'Finalizar Pedido'}
      </button>
    </aside>
  );
}