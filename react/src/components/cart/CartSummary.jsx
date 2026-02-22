export default function CartSummary({
  items,
  onCheckout,
  processingCheckout = false
}) {
  // Calcula el subtotal sumando todos los items
  const subtotal = items.reduce((sum, item) => {
    const product = item.product || {};
    const price = product.final_price || product.base_price || 0;
    return sum + price * item.quantity;
  }, 0);

  // El costo de envío será manejado por el backend
  const total = subtotal;

  const handleCheckout = () => {
    onCheckout(); // Ya no pasamos shipping_cost
  };

  return (
    <aside className="cart-summary-card">
      <h2 className="section-title">Resumen del Pedido</h2>

      {/* Subtotal */}
      <div className="cart-summary-card__row">
        <span>Subtotal:</span>
        <span>${subtotal.toFixed(2)}</span>
      </div>

      <div className="cart-summary-card__row">
        <span>Precios de envío:</span>
        <span>A calcular...</span>
      </div>

      {/* Total (sin costo de envío visible para clientes) */}
      <div className="cart-summary-card__row cart-summary-card__row--total">
        <span>Total:</span>
        <span>${total.toFixed(2)}</span>
      </div>

      {/* Botón de Checkout */}
      <button
        className="btn btn--primary btn--block"
        onClick={handleCheckout}
        disabled={processingCheckout || items.length === 0}
      >
        {processingCheckout ? 'Procesando...' : 'Finalizar Pedido'}
      </button>
    </aside>
  );
}