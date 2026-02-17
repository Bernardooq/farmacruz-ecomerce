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
  }, 0).toFixed(2);

  return (
    <aside className="cart-summary-card">
      <h2 className="section-title">Resumen del Pedido</h2>

      {/* Subtotal */}
      <div className="cart-summary-card__row">
        <span>Subtotal:</span>
        <span>${subtotal}</span>
      </div>

      {/* Envío */}
      <div className="cart-summary-card__row">
        <span>Envío:</span>
        <span>A calcular</span>
      </div>

      {/* Total Estimado */}
      <div className="cart-summary-card__row cart-summary-card__row--total">
        <span>Total Estimado:</span>
        <span>${subtotal}</span>
      </div>

      {/* Botón de Checkout */}
      <button
        className="btn btn--primary btn--block"
        onClick={onCheckout}
        disabled={processingCheckout || items.length === 0}
      >
        {processingCheckout ? 'Procesando...' : 'Finalizar Pedido'}
      </button>
    </aside>
  );
}